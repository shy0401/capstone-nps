from uuid import uuid4
import importlib.util
import pytest
from nps.parsers import ParserRegistry, safe_parse
from nps.chunking import chunk_document
from nps.errors import DomainError


@pytest.fixture(scope="module")
def fixtures(tmp_path_factory):
    path = tmp_path_factory.mktemp("golden")
    spec = importlib.util.spec_from_file_location("fixtures", "infra/scripts/generate_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.generate(path)
    return path


@pytest.mark.parametrize("ext", [".pdf", ".docx", ".xlsx", ".hwpx", ".hwp"])
def test_parse_unicode_and_chunk(fixtures, ext):
    result = ParserRegistry().parse(fixtures / ("synthetic" + ext), ext)
    chunks = chunk_document(result, uuid4(), uuid4())
    assert chunks and "합성" in " ".join(c.text for c in chunks)
    assert all(c.source_location.section == c.section_id for c in chunks)
    if ext not in {".pdf", ".hwp"}:
        tables = [c for c in chunks if c.table_refs]
        assert len(tables) == 1 and "18" in tables[0].text
    assert chunks[0].previous_chunk_id is None and chunks[-1].next_chunk_id is None


def test_hwp_explicit_failure(tmp_path, monkeypatch):
    from nps.config import settings

    monkeypatch.setattr(settings(), "hwp_enabled", False)
    with pytest.raises(DomainError, match="HWP_ADAPTER_DISABLED"):
        ParserRegistry().parse(tmp_path / "x.hwp", ".hwp")


def test_safe_subprocess(fixtures):
    result = safe_parse(fixtures / "synthetic.docx", ".docx")
    assert result.parser_version == "docx-1.0"
