from datetime import datetime, timezone
import time
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

from app.llm import call_llm
from app.logging import log_event
from app.retrieval.index import StalenessAwareRetriever, ingest_document
from app.config import settings

router = APIRouter()
retriever = StalenessAwareRetriever()


class PromptRequest(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    response: str
    warning: str | None = None


class IngestRequest(BaseModel):
    doc_id: str
    text: str
    source: str | None = None


class IngestResponse(BaseModel):
    added: int
    updated: int
    deleted: int
    total_chunks: int
    duration_ms: float


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5
    max_age_days: int | None = None


class RetrieveResponse(BaseModel):
    results: list[dict]


@router.post("/prompt", response_model=PromptResponse)
def prompt_endpoint(req: PromptRequest):
    log_event("api_request", endpoint="/prompt")

    fresh_results = retriever.retrieve(
        req.prompt,
        top_k=5,
        max_age_days=settings.staleness_max_age_days,
    )
    results = fresh_results
    warning = None

    if not results:
        fallback_results = retriever.retrieve(req.prompt, top_k=5)
        if fallback_results:
            warning = (
                "No documents found within the allowed age window. "
                "Using older documents that may be stale."
            )
            results = fallback_results

    if results and not warning:
        stale_count = 0
        for item in results:
            updated_at = item.get("last_updated_at")
            if not updated_at:
                continue
            try:
                ts = datetime.fromisoformat(updated_at)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0
            except ValueError:
                continue
            if age_days >= settings.staleness_warning_days:
                stale_count += 1
        if stale_count:
            warning = (
                f"{stale_count} retrieved document chunk(s) are older than "
                f"{settings.staleness_warning_days} days."
            )

    context = ""
    if results:
        lines = []
        for idx, item in enumerate(results, start=1):
            text = item.get("text", "")
            doc_id = item.get("doc_id", "unknown")
            chunk_id = item.get("chunk_id", "unknown")
            updated_at = item.get("last_updated_at", "unknown")
            lines.append(
                f"[{idx}] doc_id={doc_id} chunk_id={chunk_id} updated_at={updated_at}\n{text}"
            )
        context = "\n\n".join(lines)

    output = call_llm(req.prompt, context=context or None)
    return PromptResponse(response=output, warning=warning)


@router.post("/ingest", response_model=IngestResponse)
def ingest_endpoint(req: IngestRequest):
    log_event("api_request", endpoint="/ingest", doc_id=req.doc_id)
    result = ingest_document(req.doc_id, req.text, source=req.source)
    return IngestResponse(**result)


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_endpoint(req: RetrieveRequest):
    log_event("api_request", endpoint="/retrieve")
    results = retriever.retrieve(
        req.query,
        top_k=req.top_k,
        max_age_days=req.max_age_days,
    )
    return RetrieveResponse(results=results)


@router.post("/upload", response_model=IngestResponse)
def upload_endpoint(
    file: UploadFile = File(...),
    doc_id: str | None = Form(default=None),
    source: str | None = Form(default=None),
):
    log_event("api_request", endpoint="/upload", filename=file.filename)
    content = file.file.read()
    text = content.decode("utf-8", errors="replace")
    resolved_doc_id = doc_id or file.filename or f"upload-{int(time.time())}"
    result = ingest_document(resolved_doc_id, text, source=source or file.filename)
    return IngestResponse(**result)
