from dataclasses import dataclass, field
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    text: str
    source_id: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


class Chunker:
    def __init__(self, source_id: str, chunk_size: int = 512, chunk_overlap: int = 64):
        self.source_id = source_id
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def chunk(self, segments: list[tuple[str, dict]]) -> list[Chunk]:
        chunks = []
        index = 0
        for text, metadata in segments:
            split_texts = self._splitter.split_text(text)
            for split in split_texts:
                chunks.append(Chunk(
                    text=split,
                    source_id=self.source_id,
                    chunk_index=index,
                    metadata=dict(metadata),
                ))
                index += 1
        return chunks
