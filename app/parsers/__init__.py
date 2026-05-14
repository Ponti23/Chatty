from app.parsers.pdf import parse_pdf
from app.parsers.docx import parse_docx
from app.parsers.text import parse_text
from app.parsers.url import parse_url

PARSERS: dict[str, callable] = {
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


def get_parser(source_type: str):
    return PARSERS[source_type]


def detect_type(filename: str) -> str | None:
    import pathlib
    ext = pathlib.Path(filename).suffix.lower()
    return FILE_EXTENSION_MAP.get(ext)
