from typing import List
from openai import OpenAI

from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)


class OpenAIEmbedder:
    def embed(self, texts: List[str]) -> List[List[float]]:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in response.data]
