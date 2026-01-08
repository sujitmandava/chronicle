from fastapi import APIRouter
from pydantic import BaseModel

from app.llm import call_llm
from app.logging import log_event
from app.retrieval.noop import NoOpRetriever

router = APIRouter()
retriever = NoOpRetriever()


class PromptRequest(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    response: str


@router.post("/prompt", response_model=PromptResponse)
def prompt_endpoint(req: PromptRequest):
    log_event("api_request", endpoint="/prompt")

    _ = retriever.retrieve(req.prompt, top_k=5)

    output = call_llm(req.prompt)
    return PromptResponse(response=output)
