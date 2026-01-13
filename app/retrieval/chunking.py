from typing import List, Dict
import uuid

def chunk_text(
    text: str,
    doc_id: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[Dict]:
    chunks = []
    start = 0
    idx = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        chunks.append({
            "chunk_id": f"{doc_id}_{idx}",
            "doc_id": doc_id,
            "index": idx,
            "text": chunk_text,
        })

        start = end - overlap
        idx += 1

    return chunks
