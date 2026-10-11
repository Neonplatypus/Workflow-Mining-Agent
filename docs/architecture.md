# Workflow Mining Agent — System Architecture
**AI Builder Cup 2026 | Future of Work & Enterprise Productivity**

## 1. System Overview

The **Workflow Mining Agent** discovers repetitive manual IT service tasks hidden in unstructured ticket history, measures the employee hours wasted, ranks automation candidates by return on investment (ROI), and uses Google ADK and Gemini to draft structured, evidence-backed automation specifications.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TICKET INGESTION PIPELINE                       │
│  - CSV Upload / Built-in Synthetic Tickets (3,000 tickets default)      │
│  - Column Mapping & Schema Validation                                   │
│  - Quarantine Ground-Truth (Isolated for Stage F Evaluation Only)      │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     STAGE C: SEMANTIC DISCOVERY                        │
│  - Vertex AI Embeddings (text-embedding-004) / Semantic Vectorizer     │
│  - Unsupervised MiniBatchKMeans / Cosine Similarity Clustering          │
│  - Gemini on Vertex AI: Workflow Naming, Step Extraction, Exceptions    │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   STAGE D: DETERMINISTIC QUANTIFICATION                │
│  - Deterministic Analytical Engine / BigQuery SQL Analytics            │
│  - Monthly Hours Wasted = SUM(Active Handling Minutes) / 60 / Months    │
│  - Potential Annual Labor Savings = Hours × Automatable % × Labor Rate │
│  - Explainable Multi-Factor Prioritization Formula (0-100 Score)       │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                STAGE E: GOOGLE ADK SPECIFICATION AGENT                 │
│  - Synthesizes Step-by-Step Runbook from Extracted Resolution Notes    │
│  - Flags Evidence Grounding vs Architecture Recommendations            │
│  - Generates Idempotency, Preconditions, Retries, Rollback Strategy    │
│  - MANDATORY HUMAN APPROVAL GATE: Review / Approve / Reject            │
│  - STRICT BOUNDARY: Never executes automations automatically           │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   STAGE F & G: EVALUATION & DASHBOARD                  │
│  - Stage F: Precision, Recall, F1, Coverage (6/6), Time MAE, Leakage   │
│  - Stage G: React SaaS Dashboard (Overview, Tickets, Workflows, Studio)│
│  - Cloud Run Single-Container Deployment (FastAPI + React SPA)         │
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Core Architectural Principles

1. **AI Identifies Patterns, Deterministic SQL Calculates Numbers:**
   Gemini semantic models interpret unstructured language, summarize procedural patterns, and name workflows. Deterministic SQL in BigQuery calculates ticket counts, monthly hours, annual labor costs, and prioritization scores. Gemini never invents numbers.

2. **Strict Ground-Truth Isolation:**
   Evaluation labels (`workflow_ground_truth` and `handling_minutes_ground_truth`) are quarantined at ingestion. Neither clustering features nor Gemini prompts have access to ground-truth fields.

3. **Mandatory Safety Boundary:**
   Approval of an automation specification is a recorded human review decision, not permission to execute. The system contains no execution engines or production mutating connections.

## 3. Technology Stack

- **Large Language Models:** Gemini 1.5 Flash on Vertex AI (`gemini-1.5-flash`).
- **Semantic Embeddings:** Vertex AI `text-embedding-004`.
- **Analytical Storage:** Google BigQuery (`workflow_mining` dataset).
- **Agent Orchestrator:** Google Agent Development Kit (ADK) multi-step orchestration.
- **Backend API:** Python 3.11, FastAPI, Uvicorn, Pydantic, Scikit-Learn.
- **Frontend Dashboard:** React 18, Vite, Lucide Icons, Enterprise SaaS Design System.
- **Hosting:** Cloud Run container with public HTTPS endpoint.
