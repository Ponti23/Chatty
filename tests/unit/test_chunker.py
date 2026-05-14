from app.chunking import Chunker, Chunk


SOURCE_ID = "source-test-001"


def test_chunk_short_text_produces_one_chunk():
    chunker = Chunker(source_id=SOURCE_ID)
    segments = [("Short text that fits in one chunk.", {})]
    chunks = chunker.chunk(segments)
    assert len(chunks) == 1
    assert chunks[0].text == "Short text that fits in one chunk."
    assert chunks[0].source_id == SOURCE_ID
    assert chunks[0].chunk_index == 0


def test_chunk_long_text_produces_multiple_chunks():
    chunker = Chunker(source_id=SOURCE_ID, chunk_size=50, chunk_overlap=10)
    long_text = "word " * 100  # 500 characters
    segments = [(long_text, {})]
    chunks = chunker.chunk(segments)
    assert len(chunks) > 1


def test_chunk_indices_are_sequential():
    chunker = Chunker(source_id=SOURCE_ID, chunk_size=50, chunk_overlap=10)
    long_text = "word " * 100
    segments = [(long_text, {})]
    chunks = chunker.chunk(segments)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_metadata_is_preserved():
    chunker = Chunker(source_id=SOURCE_ID)
    segments = [("Some text.", {"page_number": 3})]
    chunks = chunker.chunk(segments)
    assert chunks[0].metadata["page_number"] == 3


def test_chunk_source_id_on_all_chunks():
    chunker = Chunker(source_id=SOURCE_ID, chunk_size=50, chunk_overlap=10)
    segments = [("word " * 100, {})]
    chunks = chunker.chunk(segments)
    assert all(c.source_id == SOURCE_ID for c in chunks)


def test_chunk_returns_chunk_dataclass():
    chunker = Chunker(source_id=SOURCE_ID)
    chunks = chunker.chunk([("Hello world.", {})])
    assert isinstance(chunks[0], Chunk)
    assert hasattr(chunks[0], "text")
    assert hasattr(chunks[0], "source_id")
    assert hasattr(chunks[0], "chunk_index")
    assert hasattr(chunks[0], "metadata")
