from openai import OpenAI
from app.config import settings
from app.logging import log_event

client = OpenAI(api_key=settings.openai_api_key)


def call_llm(prompt: str) -> str:
    log_event(
        "llm_request",
        model=settings.model_name,
        prompt_length=len(prompt),
    )

    response = client.chat.completions.create(
        model=settings.model_name,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    output = response.choices[0].message.content

    log_event(
        "llm_response",
        response_length=len(output),
    )

    return output
