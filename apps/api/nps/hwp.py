"""Bounded HWP 5.x body reader, run only in the safe parser subprocess.

Format reference: Hancom HWP 5.0 revision 1.3, sections 3.2 and 4.1/4.3.
Reads BodyText rather than the incomplete first-page preview. Never executes
Scripts, embedded OLE objects, fields or external links. Layout is not rendered.
"""

import re
import struct
import zlib

import olefile

from nps.config import settings
from nps.contracts import Node, NormalizedDocument, Section, SourceLocation
from nps.errors import DomainError

PARA_TEXT = 67
EXTENDED_CONTROLS = set(range(1, 10)) | set(range(11, 13)) | set(range(14, 24))


def paragraph_text(payload):
    if len(payload) % 2:
        raise DomainError("DOC_MALFORMED", 422)
    output = bytearray()
    offset = 0
    while offset < len(payload):
        char = struct.unpack_from("<H", payload, offset)[0]
        width = 16 if char in EXTENDED_CONTROLS else 2
        if offset + width > len(payload):
            raise DomainError("DOC_MALFORMED", 422)
        if char >= 32:
            output.extend(payload[offset:offset + 2])
        elif char in {9, 10, 13, 24, 30, 31}:
            output.extend({9: "\t", 10: "\n", 13: "\n", 24: "-", 30: " ", 31: " "}[char].encode("utf-16le"))
        offset += width
    try:
        return output.decode("utf-16le", errors="strict").strip()
    except UnicodeDecodeError:
        raise DomainError("HWP_ENCODING_UNSUPPORTED", 422) from None


def decompress_section(data, limit):
    if limit <= 0:
        raise DomainError("DOC_RESOURCE_LIMIT", 422)
    try:
        decoder = zlib.decompressobj(-15)
        body = decoder.decompress(data, limit + 1)
        if len(body) > limit or decoder.unconsumed_tail:
            raise DomainError("DOC_RESOURCE_LIMIT", 422)
        if not decoder.eof:
            raise DomainError("DOC_MALFORMED", 422)
        return body
    except zlib.error:
        raise DomainError("DOC_MALFORMED", 422) from None


def records(data):
    offset = count = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise DomainError("DOC_MALFORMED", 422)
        header = struct.unpack_from("<I", data, offset)[0]
        tag, level, length = header & 1023, (header >> 10) & 1023, header >> 20
        offset += 4
        if length == 4095:
            if len(data) - offset < 4:
                raise DomainError("DOC_MALFORMED", 422)
            length = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        if length > len(data) - offset or tag < 16:
            raise DomainError("DOC_MALFORMED", 422)
        count += 1
        if count > settings().max_cells * 20 or level > 128:
            raise DomainError("DOC_RESOURCE_LIMIT", 422)
        yield tag, level, data[offset:offset + length]
        offset += length


class HWPParser:
    version = "hwp5-native-1.0"

    def parse(self, path):
        if not settings().hwp_enabled:
            raise DomainError("HWP_ADAPTER_DISABLED", 422)
        if not olefile.isOleFile(path):
            raise DomainError("HWP_FORMAT_UNSUPPORTED", 422)
        with olefile.OleFileIO(path, raise_defects=olefile.DEFECT_INCORRECT) as ole:
            if not ole.exists("FileHeader"):
                raise DomainError("DOC_MALFORMED", 422)
            header = ole.openstream("FileHeader").read(256)
            if len(header) < 256 or not header.startswith(b"HWP Document File\x00"):
                raise DomainError("DOC_MALFORMED", 422)
            if header[35] != 5:
                raise DomainError("HWP_VERSION_UNSUPPORTED", 422)
            flags = struct.unpack_from("<I", header, 36)[0]
            if flags & 2:
                raise DomainError("DOC_ENCRYPTED", 422)
            if flags & 4:
                raise DomainError("HWP_DISTRIBUTION_UNSUPPORTED", 422)
            if flags & ((1 << 4) | (1 << 8) | (1 << 10)):
                raise DomainError("HWP_DRM_UNSUPPORTED", 422)
            names = ole.listdir()
            if len(names) > settings().archive_max_entries:
                raise DomainError("DOC_RESOURCE_LIMIT", 422)
            names = sorted(
                (n for n in names if len(n) == 2 and n[0] == "BodyText" and re.fullmatch(r"Section\d+", n[1])),
                key=lambda n: int(n[1][7:]),
            )
            if not names:
                raise DomainError("DOC_EMPTY", 422)
            if len(names) > settings().max_pages:
                raise DomainError("DOC_RESOURCE_LIMIT", 422)
            sections, total_bytes, node_count = [], 0, 0
            for name in names:
                remaining = settings().archive_max_bytes - total_bytes
                if ole.get_size(name) > remaining:
                    raise DomainError("DOC_RESOURCE_LIMIT", 422)
                data = ole.openstream(name).read(remaining + 1)
                body = decompress_section(data, remaining) if flags & 1 else data
                total_bytes += len(body)
                if total_bytes > settings().archive_max_bytes:
                    raise DomainError("DOC_RESOURCE_LIMIT", 422)
                sid = "hwp-" + name[1].lower()
                nodes = []
                for index, (tag, level, payload) in enumerate(records(body)):
                    if tag != PARA_TEXT:
                        continue
                    text = paragraph_text(payload)
                    if text:
                        node_count += 1
                        if node_count > settings().max_cells:
                            raise DomainError("DOC_RESOURCE_LIMIT", 422)
                        nodes.append(Node(
                            type="paragraph", text=text,
                            source_location=SourceLocation(section=sid, paragraph=index),
                        ))
                if nodes:
                    sections.append(Section(section_id=sid, heading=nodes[0].text[:80], nodes=nodes))
            if not sections:
                raise DomainError("DOC_EMPTY", 422)
            return NormalizedDocument(
                metadata={"format": "hwp", "fidelity": "body-text-including-cell-paragraphs",
                          "sections": len(names), "page_mapping": "unavailable"},
                sections=sections, parser_version=self.version,
                warnings=["HWP_TABLE_IMAGE_STRUCTURE_NOT_AVAILABLE_REVIEW_REQUIRED"],
            )
