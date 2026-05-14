from docx import Document
import io


def parse_docx(content: bytes) -> list[tuple[str, dict]]:
    doc = Document(io.BytesIO(content))
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if not full_text:
        return []
    return [(full_text, {})]
