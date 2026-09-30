# Production Deployment Guide: Cloud Run & GCP Firestore

This guide documents how to deploy the modernized **Customer Experience Agent (`Rainbow`)** to **Google Cloud Run** in project **`has-demo-50091`** (region `us-central1`).

---

## 1. Prerequisites & IAM Permissions

Ensure the following Google Cloud APIs are enabled in project `has-demo-50091`:
```bash
gcloud services enable \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    logging.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    --project=has-demo-50091
```

### Dedicated Service Account
Create a service account for Rainbow with least-privilege roles:
```bash
gcloud iam service-accounts create rainbow-agent-sa \
    --description="Service account for Rainbow Customer Experience Agent" \
    --display-name="rainbow-agent-sa" \
    --project=has-demo-50091

# Grant Firestore User (read/write data & vector search)
gcloud projects add-iam-policy-binding has-demo-50091 \
    --member="serviceAccount:rainbow-agent-sa@has-demo-50091.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# Grant Agent Platform User (Gemini models & text-embedding-004)
gcloud projects add-iam-policy-binding has-demo-50091 \
    --member="serviceAccount:rainbow-agent-sa@has-demo-50091.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Grant Logging Writer
gcloud projects add-iam-policy-binding has-demo-50091 \
    --member="serviceAccount:rainbow-agent-sa@has-demo-50091.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"
```

---

## 2. Seed Initial Cloud Firestore Data

Before deploying the runtime, seed sample customers and orders and index the policy knowledge base:
```bash
cd rainbow
export GOOGLE_CLOUD_PROJECT=has-demo-50091
export GOOGLE_CLOUD_LOCATION=us-central1

# Seed sample customers and orders
python3 scripts/seed_firestore.py

# Generate vector embeddings and index policies
python3 scripts/index_knowledge_base.py
```

---

## 3. Container Build & Cloud Run Deployment

Build the container image using Cloud Build:
```bash
gcloud builds submit --tag gcr.io/has-demo-50091/rainbow-agent:latest rainbow/
```

Deploy to Cloud Run:
```bash
gcloud run deploy rainbow-agent \
    --image gcr.io/has-demo-50091/rainbow-agent:latest \
    --platform managed \
    --region us-central1 \
    --service-account rainbow-agent-sa@has-demo-50091.iam.gserviceaccount.com \
    --set-env-vars GOOGLE_CLOUD_PROJECT=has-demo-50091,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=true \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --project has-demo-50091
```

Once deployed, Cloud Run will provide an HTTPS endpoint (e.g. `https://rainbow-agent-xyz-uc.a.run.app`) hosting both the FastAPI web UI and the Agent-to-Agent (A2A) protocol endpoints.
