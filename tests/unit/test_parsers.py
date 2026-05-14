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


def test_docx_parser_registered():
    assert "docx" in PARSERS


def test_parse_docx_returns_text_segments():
    import pathlib
    parser = get_parser("docx")
    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "sample.docx"
    with open(fixture, "rb") as f:
        content = f.read()
    segments = parser(content)
    assert len(segments) > 0
    text, metadata = segments[0]
    assert "Hello from test DOCX" in text
    assert metadata == {}


def test_txt_parser_registered():
    assert "txt" in PARSERS


def test_parse_txt_returns_text_segments():
    parser = get_parser("txt")
    content = b"Hello from test text file.\nSecond line here."
    segments = parser(content)
    assert len(segments) == 1
    text, metadata = segments[0]
    assert "Hello from test text file" in text
    assert metadata == {}
