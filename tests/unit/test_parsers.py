import pytest
from app.parsers import get_parser, PARSERS


def test_pdf_parser_registered():
    assert "pdf" in PARSERS


def test_parse_pdf_returns_text_segments():
    import pathlib
    parser = get_parser("pdf")
    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "sample.pdf"
    with open(fixture, "rb") as f:
        content = f.read()
    segments = parser(content)
    assert isinstance(segments, list)
    assert len(segments) > 0
    text, metadata = segments[0]
    assert isinstance(text, str)
    assert len(text) > 0
    assert "page_number" in metadata
