# Workflow Mining Agent — AI Builder Cup 2026

> **Track:** Future of Work & Enterprise Productivity  
> **Team:** Workflow Mining Agent Team  
> **Core Principle:** *AI identifies and explains patterns; deterministic SQL calculates the numbers; a human approves any proposed automation. The system never executes generated automations automatically.*

---

## 🚀 Executive Summary

Organizations lose hundreds of engineering hours every month to repetitive manual IT tasks buried in messy service ticket history. Teams often automate the wrong things because they lack empirical data on which workflows waste the most time.

**Workflow Mining Agent** solves this:
1. **Ingests** unstructured IT service tickets (titles, descriptions, timestamps, resolution notes).
2. **Discovers** recurring procedural workflows using semantic embeddings and clustering.
3. **Interprets** workflows, extracts common resolution steps, and identifies decision rules using Gemini 1.5 Flash.
4. **Quantifies** monthly hours wasted and potential labor savings using deterministic SQL (BigQuery / analytical SQL engine) — **Gemini never invents numbers**.
5. **Drafts** a complete, evidence-grounded automation specification using **Google ADK** for the highest-ROI opportunity.
6. **Enforces Human-in-the-Loop Governance** through an approval gate with a mandatory safety boundary.
7. **Evaluates** discovery accuracy against hidden ground truth (coverage, precision, recall, F1, and handling-time error).

---

## 🏆 Three-Minute Live Demo Walkthrough

Optimized for the AI Builder Cup presentation:

| Time | Screen | Demo Storyline & Key Talking Points |
|------|--------|-------------------------------------|
| **0:00 - 0:30** | **Overview** | **The Problem:** Introduce that organizations waste thousands of engineering hours on repetitive tasks without knowing which ones to automate. Show the top-level KPIs: **3,000 tickets analyzed**, **6 distinct workflows discovered**, **857 monthly handling hours**, and **$668,000+ potential annual savings**. Point out the distribution chart showing where engineer hours leak. |
| **0:30 - 1:00** | **Ticket Explorer** | **Unstructured Reality:** Show messy tickets with typos ("pawword", "acces"), inconsistent terminology, and varying priorities. Click any ticket to open the **Semantic Assignment Inspector** demonstrating how the agent grouped the ticket based on resolution notes with an explainable similarity score. |
| **1:00 - 1:45** | **Workflow Opportunities** | **Deterministic Ranking & Runbooks:** Open the top-ranked workflow (*Access Provisioning* or *Test Environment Resets*). Show the extracted **Step-by-Step Resolution Runbook** synthesized from real engineer notes. Show the **Transparent Prioritization Formula** breakdown: Savings (40%), Recurrence (25%), Confidence (20%), Simplicity (15%). Show explicit calculation assumptions. |
| **1:45 - 2:20** | **Automation Studio** | **Google ADK Agent & Human Governance:** Open the generated Automation Specification. Highlight the prominent **Mandatory Safety Boundary** (*approval records a review decision, never executes*). Show ordered steps with evidence grounding badges (✅ Grounded in Evidence vs 💡 Architecture Recommendation). Demonstrate recording an **Approve Proposal** decision. |
| **2:20 - 2:45** | **Evaluation Center** | **Scientific Proof:** Show live measured results against the 6 planted ground-truth workflows: **100% Coverage (6/6 discovered)**, **~92% Precision**, **~90% Recall**, and low time-estimation percentage error. Highlight the **Zero Ground-Truth Leakage** verification badge. |
| **2:45 - 3:00** | **Architecture & Close** | **Enterprise Value:** Summarize the Google Cloud architecture (Cloud Run, BigQuery, Gemini on Vertex AI, Google ADK). Emphasize how this agent empowers IT leaders to make data-backed automation decisions *before* writing code. |

---

## 🛠️ Technology Stack

- **AI & LLM:** Gemini 1.5 Flash on Vertex AI (`gemini-1.5-flash`).
- **Semantic Representation:** Vertex AI `text-embedding-004` (with TF-IDF/SVD local fallback).
- **Analytical Database:** Google BigQuery (`workflow_mining` dataset) + SQL analytics.
- **Agent Orchestrator:** Google Agent Development Kit (ADK) multi-step orchestration.
- **Backend API:** FastAPI (Python 3.11), Uvicorn, Scikit-Learn, Pydantic.
- **Frontend Dashboard:** React 18, Vite, Lucide Icons, Enterprise SaaS Design System.
- **Cloud Deployment:** Google Cloud Run (single-container multi-stage build).

---

## ⚡ Quickstart (Local Demo Mode)

The application works completely out of the box in **Local Demo Mode** without requiring Google Cloud credentials or API keys.

### 1. Clone & Setup Python Environment

```bash
git clone <repository_url>
cd workflow-mining-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Synthetic Dataset (3,000 Tickets)

```bash
python scripts/generate_data.py --count 3000 --seed 42
```
*Creates `data/synthetic_tickets_3000.csv` with 6 planted workflows and isolated ground truth.*

### 3. Run the Automated Test Suite

```bash
python -m pytest tests -v
```
*Executes all 12 unit, integration, calculation, and safety boundary tests.*

### 4. Build Frontend & Launch Application

```bash
# Build React frontend
cd frontend
npm install
npm run build
cd ..

# Launch FastAPI web application
python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8000
```

Open your browser to:
- **Interactive Dashboard:** `http://localhost:8000/`
- **Swagger API Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

---

## ☁️ Google Cloud & Cloud Run Deployment

To deploy the application to Google Cloud Run with Vertex AI and BigQuery enabled:

1. Configure Google Cloud credentials and project:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. Follow the detailed steps in [docs/cloud_run_deployment.md](docs/cloud_run_deployment.md).
3. Deploy directly using Cloud Build:
   ```bash
   gcloud run deploy workflow-mining-agent \
       --source . \
       --region us-central1 \
       --platform managed \
       --allow-unauthenticated \
       --set-env-vars APP_MODE=CLOUD,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,BIGQUERY_DATASET=workflow_mining
   ```

---

## 🔬 Evaluation & Reliability Proof

The evaluation harness in `backend/evaluation/evaluator.py` benchmarks discovery results against hidden ground truth:

1. **Workflow Detection:** Unsupervised semantic clustering groups tickets and maps clusters to planted workflows, computing macro precision, recall, and F1 score.
2. **Coverage:** Measures how many of the 6 planted workflows are identified.
3. **Time Estimation Error:** Compares predicted monthly handling hours against ground-truth handling totals, calculating Mean Absolute Error (MAE) and percentage error.
4. **Specification Quality Checklist:** Verifies the presence of triggers, ordered steps, system targets, decision rules, approval gates, rollback strategies, logging, and acceptance criteria (7-point checklist).
5. **Robustness:** Tests resilience against misspelled terms (`pawword`, `acces`, `clenup`) and technical abbreviations (`k8s`, `SA`, `prod`).
6. **Ground-Truth Leakage Check:** Verifies that no ground-truth column was ever ingested or passed into discovery prompts.

---

## 🛡️ Mandatory Safety Boundary

Generated automation specifications are blueprints designed for engineering review. **Approval in the dashboard is a recorded review decision, not permission to execute.** The Workflow Mining Agent does not connect to mutating production APIs and will never execute generated scripts automatically.

---

## 📄 License

Developed for the **Google AI Builder Cup 2026**.
