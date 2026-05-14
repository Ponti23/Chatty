def parse_text(content: bytes) -> list[tuple[str, dict]]:
    text = content.decode("utf-8", errors="replace").strip()
    if not text:
        return []
    return [(text, {})]
