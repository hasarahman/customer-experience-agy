# Cloud Run Deployment & Operational Patterns

This reference documents container packaging, Artifact Registry deployment, and authenticated proxying for Google ADK agents running on Google Cloud Run.

---

## 1. Container Packaging with Multi-Stage `uv`

Modern ADK agents leverage Astral `uv` for sub-second dependency resolution:

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.11-slim-bookworm
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
EXPOSE 8080
CMD ["uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 2. Deploying via Google Artifact Registry

> [!WARNING]
> Modern GCP projects disable legacy Container Registry (`gcr.io`). Attempting to push to `gcr.io/PROJECT_ID` triggers `denied: gcr.io repo does not exist`.

Always use Google Artifact Registry or Cloud Run source builds:

```bash
# Direct Source Deploy (Cloud Build automatically packages and pushes to Artifact Registry)
gcloud run deploy <service-name> \
  --source <source-directory> \
  --project <project-id> \
  --region us-central1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=<project-id>,GOOGLE_CLOUD_LOCATION=us-central1,MODEL=gemini-2.5-flash \
  --min-instances 0 \
  --max-instances 5 \
  --memory 1Gi \
  --cpu 1 \
  --allow-unauthenticated
```

---

## 3. Secure Authenticated Local Development

If the Cloud Run service is private (no `--allow-unauthenticated`), or for seamless testing:

```bash
# 1. Establish an authenticated local proxy
gcloud run services proxy <service-name> \
  --project <project-id> \
  --region us-central1 \
  --port 8080

# 2. Query the local proxy
curl -X POST http://127.0.0.1:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "app",
    "userId": "test-user",
    "sessionId": "session_001",
    "newMessage": {"role": "user", "parts": [{"text": "Hello!"}]}
  }'
```

---

## 4. ADK API Endpoints

ADK FastAPI services expose standard HTTP endpoints:

1. **`POST /apps/{appName}/users/{userId}/sessions`**:
   Creates a new session context. Returns `{"id": "<session-id>"}`.
2. **`POST /run`**:
   Executes an agent turn. Body schema:
   ```json
   {
     "appName": "app",
     "userId": "string",
     "sessionId": "string",
     "newMessage": {
       "role": "user",
       "parts": [{"text": "string"}]
     }
   }
   ```
3. **`GET /health`** or **`GET /`**:
   Health probe for Cloud Run container lifecycle.
