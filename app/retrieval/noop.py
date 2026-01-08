import time
from typing import List

from app.retrieval.base import Retriever, RetrievalResult
from app.logging import log_event


class NoOpRetriever(Retriever):
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        t0 = time.perf_counter()

        results: List[RetrievalResult] = []

        log_event(
            "retrieval_complete",
            top_k=top_k,
            result_count=len(results),
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

        return results
