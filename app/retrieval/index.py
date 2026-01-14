import math
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

from app.logging import log_event
from app.config import settings
from app.retrieval.chunking import chunk_text, add_chunk_hashes, hash_text
from app.retrieval.openai_embedder import OpenAIEmbedder
from app.retrieval.base import Retriever, RetrievalResult
from app.retrieval import store


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


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _staleness_weight(updated_at: Optional[str]) -> float:
    if not updated_at:
        return 1.0
    try:
        ts = datetime.fromisoformat(updated_at)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except ValueError:
        return 1.0
    age_days = max((datetime.now(timezone.utc) - ts).total_seconds() / 86400.0, 0.0)
    half_life = max(settings.staleness_half_life_days, 0.1)
    return math.exp(-age_days / half_life)


def ingest_document(doc_id: str, text: str, source: Optional[str] = None) -> Dict:
    t0 = time.perf_counter()
    existing_doc = store.get_document(settings.db_path, doc_id)
    existing_chunks = store.get_chunks_by_doc(settings.db_path, doc_id)
    existing_by_id = {c["chunk_id"]: c for c in existing_chunks}

    chunks = add_chunk_hashes(chunk_text(text, doc_id))
    new_chunk_ids = {c["chunk_id"] for c in chunks}

    to_embed = []
    to_upsert = []

    for chunk in chunks:
        prev_row = existing_by_id.get(chunk["chunk_id"])
        if prev_row and prev_row.get("chunk_hash") == chunk["chunk_hash"]:
            continue
        to_embed.append(chunk)

    embedder = OpenAIEmbedder()
    if to_embed:
        embeddings = embedder.embed([c["text"] for c in to_embed])
        for chunk, embedding in zip(to_embed, embeddings):
            chunk["embedding"] = store.serialize_embedding(embedding)
            prev_time = existing_by_id.get(chunk["chunk_id"], {}).get("created_at")
            chunk["created_at"] = prev_time or store.now_iso()
            chunk["updated_at"] = store.now_iso()
            to_upsert.append(chunk)

    deleted = [cid for cid in existing_by_id.keys() if cid not in new_chunk_ids]
    store.delete_chunks(settings.db_path, doc_id, deleted)

    now = store.now_iso()
    doc_payload = {
        "doc_id": doc_id,
        "source": source,
        "content_hash": hash_text(text),
        "created_at": existing_doc["created_at"] if existing_doc else now,
        "updated_at": now,
    }
    store.upsert_document(settings.db_path, doc_payload)
    if to_upsert:
        store.upsert_chunks(settings.db_path, to_upsert)

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    log_event(
        "ingest_complete",
        doc_id=doc_id,
        added=len(to_upsert),
        deleted=len(deleted),
        duration_ms=duration_ms,
    )
    return {
        "added": len([c for c in to_upsert if c["chunk_id"] not in existing_by_id]),
        "updated": len([c for c in to_upsert if c["chunk_id"] in existing_by_id]),
        "deleted": len(deleted),
        "total_chunks": len(chunks),
        "duration_ms": duration_ms,
    }


class StalenessAwareRetriever(Retriever):
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_age_days: Optional[int] = None,
    ) -> List[RetrievalResult]:
        t0 = time.perf_counter()
        embedder = OpenAIEmbedder()
        query_embedding = embedder.embed([query])[0]

        rows = store.list_chunks(settings.db_path)
        results: List[RetrievalResult] = []

        for row in rows:
            if store.is_stale(row.get("updated_at"), max_age_days):
                continue
            embedding = store.parse_embedding(row.get("embedding"))
            if not embedding:
                continue
            similarity = _cosine_similarity(query_embedding, embedding)
            weight = _staleness_weight(row.get("updated_at"))
            score = similarity * weight
            results.append(
                {
                    "chunk_id": row.get("chunk_id"),
                    "doc_id": row.get("doc_id"),
                    "text": row.get("text"),
                    "similarity": similarity,
                    "created_at": row.get("created_at"),
                    "last_updated_at": row.get("updated_at"),
                    "score": score,
                }
            )

        results.sort(key=lambda r: r.get("score", 0.0), reverse=True)
        results = results[:top_k]

        log_event(
            "retrieval_complete",
            top_k=top_k,
            result_count=len(results),
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
        )
        return results
