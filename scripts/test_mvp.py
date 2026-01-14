import json
import os
import sys
import time
from urllib import request
import uuid


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_multipart(path: str, fields: dict, file_field: str, filename: str, data: bytes) -> dict:
    boundary = f"----chronicle-{uuid.uuid4().hex}"
    body = bytearray()
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8")
    )
    body.extend(b"Content-Type: text/plain\r\n\r\n")
    body.extend(data)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = request.Request(
        f"{BASE_URL}{path}",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    doc_id = f"doc-{int(time.time())}"
    text_v1 = "Chronicle is a staleness-aware RAG system. It keeps documents fresh."
    text_v2 = text_v1 + " Updates only re-embed changed chunks."

    ingest1 = _post("/ingest", {"doc_id": doc_id, "text": text_v1, "source": "test"})
    if ingest1.get("total_chunks", 0) <= 0:
        print("Ingest failed: no chunks created")
        return 1

    results1 = _post("/retrieve", {"query": "staleness-aware", "top_k": 3})
    if not results1.get("results"):
        print("Retrieve failed: no results")
        return 1

    ingest2 = _post("/ingest", {"doc_id": doc_id, "text": text_v2, "source": "test"})
    if ingest2.get("added", 0) + ingest2.get("updated", 0) <= 0:
        print("Update failed: no chunks updated")
        return 1

    upload_text = "Upload test document for Chronicle RAG."
    upload = _post_multipart(
        "/upload",
        {"doc_id": f"{doc_id}-upload", "source": "upload-test"},
        "file",
        "upload.txt",
        upload_text.encode("utf-8"),
    )
    if upload.get("total_chunks", 0) <= 0:
        print("Upload ingest failed: no chunks created")
        return 1

    results2 = _post("/retrieve", {"query": "re-embed", "top_k": 3})
    if not results2.get("results"):
        print("Retrieve failed after update: no results")
        return 1

    print("OK", {"ingest1": ingest1, "ingest2": ingest2, "upload": upload})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
