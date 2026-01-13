from typing import List, Dict
from app.logging import log_event


class InMemoryIndex:
    def __init__(self):
        self.vectors: List[List[float]] = []
        self.metadata: List[Dict] = []

    def add(self, embeddings: List[List[float]], metadatas: List[Dict]):
        self.vectors.extend(embeddings)
        self.metadata.extend(metadatas)

        log_event(
            "index_add",
            added=len(embeddings),
            total=len(self.vectors),
        )
