from openai import OpenAI
from app.config import settings
from app.logging import log_event

client = OpenAI(api_key=settings.openai_api_key)


def call_llm(prompt: str, context: str | None = None) -> str:
    log_event(
        "llm_request",
        model=settings.model_name,
        prompt_length=len(prompt),
    )

    messages = []
    if context:
        messages.append(
            {
                "role": "system",
                "content": (
                    "You are a factual assistant. Use only the provided context. If there is no context, say so."
                ),
            }
        )
        messages.append(
            {
                "role": "system",
                "content": f"Context:\n{context}",
            }
        )
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=settings.model_name,
        messages=messages,
    )

    output = response.choices[0].message.content

    log_event(
        "llm_response",
        response_length=len(output),
    )

    return output
