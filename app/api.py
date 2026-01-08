from fastapi import APIRouter
from pydantic import BaseModel

from app.llm import call_llm
from app.logging import log_event

router = APIRouter()


class PromptRequest(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    response: str


@router.post("/prompt", response_model=PromptResponse)
def prompt_endpoint(req: PromptRequest):
    log_event("api_request", endpoint="/prompt")

    output = call_llm(req.prompt)

    return PromptResponse(response=output)
