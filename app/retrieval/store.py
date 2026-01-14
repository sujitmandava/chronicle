import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Iterable


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                source TEXT,
                content_hash TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT,
                chunk_index INTEGER,
                chunk_hash TEXT,
                text TEXT,
                embedding TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
            CREATE INDEX IF NOT EXISTS idx_chunks_updated_at ON chunks(updated_at);
            """
        )


def get_document(db_path: str, doc_id: str) -> Optional[Dict]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE doc_id = ?",
            (doc_id,),
        ).fetchone()
        return dict(row) if row else None


def upsert_document(db_path: str, doc: Dict) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO documents (doc_id, source, content_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                source = excluded.source,
                content_hash = excluded.content_hash,
                updated_at = excluded.updated_at
            """,
            (
                doc["doc_id"],
                doc.get("source"),
                doc.get("content_hash"),
                doc.get("created_at"),
                doc.get("updated_at"),
            ),
        )


def get_chunks_by_doc(db_path: str, doc_id: str) -> List[Dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM chunks WHERE doc_id = ?",
            (doc_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_chunks(db_path: str, chunks: Iterable[Dict]) -> None:
    with _connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO chunks (
                chunk_id, doc_id, chunk_index, chunk_hash,
                text, embedding, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                chunk_hash = excluded.chunk_hash,
                text = excluded.text,
                embedding = excluded.embedding,
                updated_at = excluded.updated_at
            """,
            [
                (
                    c["chunk_id"],
                    c["doc_id"],
                    c["index"],
                    c.get("chunk_hash"),
                    c["text"],
                    c.get("embedding"),
                    c.get("created_at"),
                    c.get("updated_at"),
                )
                for c in chunks
            ],
        )


def delete_chunks(db_path: str, doc_id: str, chunk_ids: List[str]) -> None:
    if not chunk_ids:
        return
    with _connect(db_path) as conn:
        conn.executemany(
            "DELETE FROM chunks WHERE doc_id = ? AND chunk_id = ?",
            [(doc_id, cid) for cid in chunk_ids],
        )


def list_chunks(db_path: str) -> List[Dict]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM chunks").fetchall()
        return [dict(r) for r in rows]


def parse_embedding(raw: Optional[str]) -> Optional[List[float]]:
    if raw is None:
        return None
    return json.loads(raw)


def serialize_embedding(embedding: List[float]) -> str:
    return json.dumps(embedding)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_stale(updated_at: Optional[str], max_age_days: Optional[int]) -> bool:
    if not updated_at or max_age_days is None:
        return False
    try:
        ts = datetime.fromisoformat(updated_at)
    except ValueError:
        return False
    return datetime.now(timezone.utc) - ts > timedelta(days=max_age_days)
