import trafilatura


def fetch_url(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    return downloaded or ""


def parse_url(url: str) -> list[tuple[str, dict]]:
    raw_html = fetch_url(url)
    if not raw_html:
        return []
    text = trafilatura.extract(raw_html, include_comments=False, include_tables=False)
    if not text or not text.strip():
        return []
    return [(text.strip(), {"url": url})]
