# Chronicle (Staleness-Aware RAG)

Chronicle is an MVP staleness-aware retrieval-augmented generation (RAG) service. It ingests documents, chunks and embeds them, stores everything in SQLite, and retrieves the most relevant (and freshest) chunks for answering prompts. Retrieval scoring decays with document age, and the API can warn if the retrieved context is stale.

## Features
- Document ingest with change detection and re-embedding only changed chunks.
- Staleness-aware retrieval with optional max age filtering.
- Prompt endpoint that injects retrieved context and reports staleness warnings.
- Simple dev UI for prompt testing.
- File-based JSON logging with Loki/Grafana support via Alloy.

## Architecture (High Level)
- API: FastAPI app in `app/main.py` and `app/api.py`.
- Storage: SQLite database at `data/chronicle.db`.
- Embeddings: OpenAI `text-embedding-3-small`.
- LLM: OpenAI chat completions (`gpt-4.1-mini` by default).
- Observability: File logs in `logs/chronicle.log` scraped by Alloy, sent to Loki, viewed in Grafana.

## Setup
Create a `.env` file in the repo root with at least:
```
OPENAI_API_KEY=your_key_here
```
Optional settings (defaults shown):
```
APP_NAME=staleness-rag
LOG_LEVEL=INFO
LOG_FILE=logs/chronicle.log
DB_PATH=data/chronicle.db
STALENESS_HALF_LIFE_DAYS=30.0
STALENESS_WARNING_DAYS=30
STALENESS_MAX_AGE_DAYS=180
MODEL_NAME=gpt-4.1-mini
```

Install dependencies for local dev:
```
pip install -r requirements.txt
```

## Running Locally
Start the API:
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the dev UI at `http://localhost:8000/`.

## Docker Compose (API + UI + Observability)
```
docker compose up --build
```

Services:
- API: `http://localhost:8000`
- Dev UI (nginx): `http://localhost:3000`
- Grafana: `http://localhost:3001` (admin/admin)

## API Endpoints
- `POST /ingest` `{ "doc_id": "...", "text": "...", "source": "..." }`
- `POST /upload` multipart file upload with `file`, optional `doc_id`, `source`
- `POST /retrieve` `{ "query": "...", "top_k": 5, "max_age_days": 180 }`
- `POST /prompt` `{ "prompt": "..." }` -> `{ response, warning }`

## Observability
Logs are written to `logs/chronicle.log` in JSON lines. In Docker Compose, this file is shared via the `logs` volume and tailed by Alloy (`observability/config.alloy`), which pushes to Loki. Grafana is pre-provisioned with a Loki datasource.

If you do not see logs:
- Verify the log file exists inside the app container at `/app/logs/chronicle.log`.
- Confirm the Alloy container can see the same file at `/app/logs/chronicle.log`.

## Smoke Test
Run the MVP smoke test (expects the API to be running):
```
python scripts/test_mvp.py
```

## Notes
- This is an MVP and not hardened for production. There is no authentication, rate limiting, or input-size enforcement.
- Retrieval currently scans all chunks in SQLite; large corpora will need a vector index.
