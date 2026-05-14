import pathlib
from collections.abc import Callable

from app.parsers.pdf import parse_pdf
from app.parsers.docx import parse_docx
from app.parsers.text import parse_text
from app.parsers.url import parse_url

PARSERS: dict[str, Callable] = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "txt": parse_text,
    "md": parse_text,
    "url": parse_url,
}

FILE_EXTENSION_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "md",
}


def get_parser(source_type: str) -> Callable:
    if source_type not in PARSERS:
        raise ValueError(f"Unknown source type '{source_type}'. Valid types: {list(PARSERS)}")
    return PARSERS[source_type]


def detect_type(filename: str) -> str | None:
    ext = pathlib.Path(filename).suffix.lower()
    return FILE_EXTENSION_MAP.get(ext)
