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


from unittest.mock import patch


def test_url_parser_registered():
    assert "url" in PARSERS


def test_parse_url_extracts_main_content():
    parser = get_parser("url")
    fake_html = "<html><body><article><p>Main article content here.</p></article></body></html>"

    with patch("app.parsers.url.fetch_url") as mock_fetch:
        mock_fetch.return_value = fake_html
        segments = parser("https://example.com/article")

    assert len(segments) > 0
    text, metadata = segments[0]
    assert "Main article content" in text
    assert metadata.get("url") == "https://example.com/article"


def test_parse_url_returns_empty_on_no_content():
    parser = get_parser("url")
    with patch("app.parsers.url.fetch_url") as mock_fetch:
        mock_fetch.return_value = "<html><body></body></html>"
        segments = parser("https://example.com/empty")
    assert segments == []
