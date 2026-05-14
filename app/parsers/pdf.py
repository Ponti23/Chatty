import pdfplumber
import io


def parse_pdf(content: bytes) -> list[tuple[str, dict]]:
    segments = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                segments.append((text, {"page_number": page_num}))
    return segments
