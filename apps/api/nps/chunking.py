import re
from nps.config import settings
from nps.contracts import SemanticChunk, SlidePlanContract
from nps.errors import DomainError


def token_count(text):
    # Conservative multilingual budget: Korean characters count individually.
    return max(1, len(re.findall(r"[가-힣]|[A-Za-z0-9]+|[^\s]", text)))


def chunk_document(document, document_id, version_id, security_class="synthetic"):
    result = []
    for section in document.sections:
        pending, pending_loc = [], None

        def flush():
            nonlocal pending, pending_loc
            if pending:
                text = "\n".join(pending)
                result.append(
                    SemanticChunk(
                        document_id=document_id,
                        version_id=version_id,
                        section_id=section.section_id,
                        text=text,
                        token_count=token_count(text),
                        source_location=pending_loc,
                        security_class=security_class,
                    )
                )
                pending, pending_loc = [], None

        for node in section.nodes:
            if node.type in {"table", "image"}:
                flush()
                text = node.text or f"원문 이미지 {node.node_id}"
                result.append(
                    SemanticChunk(
                        document_id=document_id,
                        version_id=version_id,
                        section_id=section.section_id,
                        text=text,
                        token_count=token_count(text),
                        source_location=node.source_location,
                        security_class=security_class,
                        table_refs=[node.node_id] if node.type == "table" else [],
                        image_refs=[node.node_id] if node.type == "image" else [],
                    )
                )
                continue
            # Sentence boundaries are preferred; very long sentences split with explicit offsets in location metadata.
            sentences = re.split(r"(?<=[.!?。])\s+|\n+", node.text)
            for sentence in sentences:
                pieces = [
                    sentence[i : i + settings().chunk_tokens]
                    for i in range(0, len(sentence), settings().chunk_tokens)
                ] or [""]
                for piece in pieces:
                    if token_count("\n".join(pending + [piece])) > settings().chunk_tokens:
                        flush()
                    pending_loc = pending_loc or node.source_location
                    pending.append(piece)
        flush()
    for i, chunk in enumerate(result):
        chunk.previous_chunk_id = result[i - 1].chunk_id if i else None
        chunk.next_chunk_id = result[i + 1].chunk_id if i + 1 < len(result) else None
    return result


def validate_evidence(plan: SlidePlanContract, chunks):
    index = {str(c.chunk_id): c for c in chunks}
    for slide in plan.slides:
        refs = list(slide.source_refs) + [ref for block in slide.content_blocks for ref in block.source_refs]
        for ref in refs:
            chunk = index.get(str(ref.chunk_id))
            if not chunk or chunk.version_id != ref.document_version_id or chunk.section_id != ref.section:
                raise DomainError("EVIDENCE_INVALID", 422)
            if (
                ref.document_version_id not in plan.document_versions
                or ref.page != chunk.source_location.page
            ):
                raise DomainError("EVIDENCE_INVALID", 422)
            if any(n not in chunk.table_refs + chunk.image_refs for n in ref.node_ids):
                raise DomainError("EVIDENCE_INVALID", 422)
    return {"status": "PASS", "slides": len(plan.slides)}
