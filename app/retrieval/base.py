from abc import ABC, abstractmethod
from typing import List, Dict, Any


class RetrievalResult(Dict[str, Any]):
    """
    Expected keys (future):
      - chunk_id
      - doc_id
      - text
      - similarity
      - created_at
      - last_updated_at
    """
    pass


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        raise NotImplementedError
