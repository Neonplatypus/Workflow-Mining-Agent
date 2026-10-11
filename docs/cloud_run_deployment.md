# Google Cloud Platform Deployment Guide
**Workflow Mining Agent — AI Builder Cup 2026**

This document provides step-by-step deployment instructions for Google Cloud Run and BigQuery.

---

## 1. Prerequisites

- A Google Cloud Platform (GCP) project with billing enabled.
- Google Cloud SDK (`gcloud`) installed and configured:
  ```bash
  gcloud auth login
  gcloud config set project YOUR_PROJECT_ID
  ```
- Appropriate IAM permissions (Project Owner or Editor).

---

## 2. Enable Required Google Cloud APIs

```bash
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    aiplatform.googleapis.com \
    bigquery.googleapis.com
```

---

## 3. Configure Service Account & Least-Privilege IAM Roles

Create a dedicated runtime service account for Cloud Run:

```bash
# 1. Create service account
gcloud iam service-accounts create workflow-mining-sa \
    --description="Runtime identity for Workflow Mining Agent on Cloud Run" \
    --display-name="Workflow Mining Service Account"

# 2. Grant Vertex AI User (for Gemini models and embeddings)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:workflow-mining-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# 3. Grant BigQuery Data Editor and Job User
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:workflow-mining-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:workflow-mining-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
```

---

## 4. Initialize BigQuery Dataset and Tables

Create the dataset in your target region (e.g. `us-central1`):

```bash
# Create dataset
bq --location=us-central1 mk -d YOUR_PROJECT_ID:workflow_mining

# Initialize schema tables
bq query --use_legacy_sql=false < sql/01_schema.sql
```

---

## 5. Build and Deploy to Cloud Run

### Option A: Direct Source Deploy via Cloud Build (Recommended)

```bash
gcloud run deploy workflow-mining-agent \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account workflow-mining-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars "\
APP_MODE=CLOUD,\
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,\
GOOGLE_CLOUD_LOCATION=us-central1,\
BIGQUERY_DATASET=workflow_mining,\
GOOGLE_GENAI_USE_VERTEXAI=true,\
GEMINI_MODEL=gemini-1.5-flash,\
EMBEDDING_MODEL=text-embedding-004,\
DEFAULT_HOURLY_LABOR_RATE=65.00,\
DEFAULT_AUTOMATABLE_PERCENTAGE=0.75"
```

### Option B: Build Docker Image Locally and Push to Artifact Registry

```bash
# 1. Create Artifact Registry repository
gcloud artifacts repositories create workflow-mining-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Workflow Mining Agent"

# 2. Authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# 3. Build and tag
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/workflow-mining-repo/app:latest .

# 4. Push image
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/workflow-mining-repo/app:latest

# 5. Deploy image to Cloud Run
gcloud run deploy workflow-mining-agent \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/workflow-mining-repo/app:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account workflow-mining-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## 6. Verify Deployment

Once deployed, Cloud Run will print the service URL (e.g., `https://workflow-mining-agent-xyz-uc.a.run.app`).

1. Open `https://YOUR_SERVICE_URL/health` in your browser. Expect:
   ```json
   {
     "status": "healthy",
     "app_mode": "CLOUD",
     "is_cloud_mode_ready": true,
     "timestamp": "..."
   }
   ```
2. Open `https://YOUR_SERVICE_URL/` to view the interactive React dashboard.
