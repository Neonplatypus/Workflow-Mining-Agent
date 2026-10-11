"""
FastAPI Backend Application for Workflow Mining Agent.
AI Builder Cup 2026.
"""

import os
import uuid
import json
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import settings, is_cloud_mode_ready
from backend.models.ticket import Ticket, TicketIngestionResult, TicketSummary
from backend.models.workflow import DiscoveredWorkflow, WorkflowMetrics
from backend.models.automation import (
    AutomationSpecification,
    ApprovalStatus,
    ReviewRequest
)
from backend.models.evaluation import EvaluationReport
from backend.repositories.ticket_repository import TicketRepository
from backend.services.clustering_service import ClusteringService
from backend.services.workflow_discovery import WorkflowDiscoveryService
from backend.services.quantification_service import QuantificationService
from backend.agent.adk_orchestrator import ADKAutomationAgent
from backend.evaluation.evaluator import EvaluationFramework
from backend.data.synthetic_generator import generate_synthetic_dataset, save_dataset_to_csv


app = FastAPI(
    title="Workflow Mining Agent API",
    description="Discovers repetitive manual workflows in IT service tickets, quantifies wasted hours via deterministic SQL, and drafts evidence-grounded automation specifications.",
    version="1.0.0"
)

# Enable CORS for local dev and Cloud Run
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory application state and job cache
repo = TicketRepository()
clustering_service = ClusteringService()
discovery_service = WorkflowDiscoveryService()
quant_service = QuantificationService()
agent = ADKAutomationAgent()
evaluator = EvaluationFramework()

# Global run state
analysis_jobs: Dict[str, Dict[str, Any]] = {}
discovered_workflows_cache: Dict[str, List[DiscoveredWorkflow]] = {}
automation_specs_cache: Dict[str, AutomationSpecification] = {}
evaluation_reports_cache: Dict[str, EvaluationReport] = {}
active_run_id: Optional[str] = None


class SyntheticGenerateRequest(BaseModel):
    count: int = Field(default=3000, ge=100, le=10000)
    seed: int = Field(default=42)


class AnalysisRunRequest(BaseModel):
    dataset_name: Optional[str] = "Default IT Tickets"
    hourly_labor_rate: Optional[float] = 65.0
    automatable_percentage: Optional[float] = 0.75
    n_clusters: Optional[int] = 6


def _execute_analysis_pipeline(run_id: str, hourly_rate: float, automatable_pct: float, n_clusters: int):
    """
    Background worker that runs the full end-to-end pipeline:
    1. Ingestion / normalized tickets fetch
    2. Semantic Embeddings & Clustering (Stage C)
    3. Gemini / Semantic interpretation (Stage C)
    4. Deterministic SQL Quantification & Ranking (Stage D)
    5. Google ADK Automation Specification drafting for top workflow (Stage E)
    6. Ground truth evaluation (Stage F)
    """
    try:
        analysis_jobs[run_id]["status"] = "RUNNING"
        analysis_jobs[run_id]["progress"] = 10
        analysis_jobs[run_id]["message"] = "Fetching tickets for semantic embedding..."

        tickets = repo.get_all_normalized_tickets_for_clustering()
        if not tickets:
            # If database is empty, automatically load synthetic tickets
            csv_path = os.path.join(settings.DATA_DIR, "synthetic_tickets_3000.csv")
            if not os.path.exists(csv_path):
                synth_tickets, _ = generate_synthetic_dataset(num_tickets=3000, seed=42)
                save_dataset_to_csv(synth_tickets, csv_path, include_ground_truth=True)
            repo.ingest_csv(csv_path, dataset_name="Synthetic IT Service Tickets")
            tickets = repo.get_all_normalized_tickets_for_clustering()

        analysis_jobs[run_id]["progress"] = 30
        analysis_jobs[run_id]["message"] = "Clustering semantically similar tickets..."

        # Stage C: Clustering
        cluster_runner = ClusteringService(n_clusters=n_clusters)
        cluster_res = cluster_runner.discover_clusters(tickets)
        clusters = cluster_res["clusters"]
        assignments = cluster_res["ticket_assignments"]
        
        # Update tickets with workflow assignments
        ticket_map = {t["ticket_id"]: t for t in tickets}
        db_assignments = []
        for t_id, (c_idx, sim) in assignments.items():
            wf_id = f"WF-{c_idx + 1:02d}"
            db_assignments.append((t_id, wf_id, sim))
            if t_id in ticket_map:
                ticket_map[t_id]["predicted_workflow_id"] = wf_id
                
        repo.update_ticket_workflow_assignments(db_assignments)

        analysis_jobs[run_id]["progress"] = 55
        analysis_jobs[run_id]["message"] = "Interpreting workflows and extracting resolution steps..."

        # Stage C & D: Interpretation and Deterministic Quantification
        custom_quant = QuantificationService(hourly_labor_rate=hourly_rate, default_automatable_pct=automatable_pct)
        raw_workflows = []

        for c in clusters:
            c_idx = c["cluster_idx"]
            wf_id = f"WF-{c_idx + 1:02d}"
            c_tickets = [ticket_map[t_id] for t_id in c["ticket_ids"] if t_id in ticket_map]
            rep_tickets = [ticket_map[t_id] for t_id in c["representative_ticket_ids"] if t_id in ticket_map]

            interpretation = discovery_service.interpret_cluster(
                cluster_idx=c_idx,
                cluster_tickets=c_tickets,
                representative_tickets=rep_tickets,
                coherence_score=c["coherence_score"]
            )

            metrics = custom_quant.calculate_cluster_metrics(
                workflow_id=wf_id,
                cluster_tickets=c_tickets,
                confidence_score=interpretation["confidence_score"],
                complexity_score=interpretation.get("complexity_score", 0.4)
            )

            raw_workflows.append({
                "workflow_id": wf_id,
                "workflow_name": interpretation["workflow_name"],
                "description": interpretation["description"],
                "category": c_tickets[0].get("category", "IT Support") if c_tickets else "IT Support",
                "common_trigger": interpretation["common_trigger"],
                "typical_resolution_steps": interpretation["typical_resolution_steps"],
                "required_inputs_and_systems": interpretation["required_inputs_and_systems"],
                "common_exceptions": interpretation["common_exceptions"],
                "suggested_automation_approach": interpretation["suggested_automation_approach"],
                "confidence_score": interpretation["confidence_score"],
                "confidence_explanation": interpretation["confidence_explanation"],
                "implementation_complexity": interpretation["implementation_complexity"],
                "complexity_score": interpretation.get("complexity_score", 0.4),
                "representative_ticket_ids": c["representative_ticket_ids"],
                "cluster_size": len(c_tickets),
                "metrics": metrics
            })

        # Rank workflows deterministically
        ranked = custom_quant.rank_workflows(raw_workflows)
        discovered_wfs = [DiscoveredWorkflow(**w) for w in ranked]
        discovered_workflows_cache[run_id] = discovered_wfs

        analysis_jobs[run_id]["progress"] = 80
        analysis_jobs[run_id]["message"] = "ADK Agent drafting automation specification for top workflow..."

        # Stage E: Draft specification for top ranked workflow
        top_wf = discovered_wfs[0]
        top_rep_tickets = [ticket_map[t_id] for t_id in top_wf.representative_ticket_ids if t_id in ticket_map]
        automation_spec = agent.draft_specification(top_wf, top_rep_tickets, run_id)
        automation_specs_cache[automation_spec.draft_id] = automation_spec

        analysis_jobs[run_id]["progress"] = 92
        analysis_jobs[run_id]["message"] = "Evaluating performance against ground truth..."

        # Stage F: Evaluation against ground truth
        full_tickets, _ = repo.get_tickets(limit=10000)
        report = evaluator.evaluate_run(
            run_id=run_id,
            dataset_name=analysis_jobs[run_id]["dataset_name"],
            tickets_with_ground_truth=full_tickets,
            discovered_workflows=discovered_wfs,
            automation_spec=automation_spec
        )
        evaluation_reports_cache[run_id] = report

        analysis_jobs[run_id]["status"] = "COMPLETED"
        analysis_jobs[run_id]["progress"] = 100
        analysis_jobs[run_id]["message"] = "Analysis completed successfully."
        analysis_jobs[run_id]["completed_at"] = datetime.utcnow().isoformat()
        analysis_jobs[run_id]["top_workflow_id"] = top_wf.workflow_id
        analysis_jobs[run_id]["draft_id"] = automation_spec.draft_id

    except Exception as e:
        import traceback
        traceback.print_exc()
        analysis_jobs[run_id]["status"] = "FAILED"
        analysis_jobs[run_id]["error"] = str(e)
        analysis_jobs[run_id]["message"] = f"Analysis failed: {str(e)}"


@app.get("/health")
def health_check():
    """Health check endpoint for Cloud Run and monitoring."""
    return {
        "status": "healthy",
        "app_mode": settings.APP_MODE,
        "is_cloud_mode_ready": is_cloud_mode_ready(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    """Returns top-level dashboard metrics for the Overview screen."""
    global active_run_id
    
    # If no analysis run has occurred yet, auto-trigger baseline demo run
    if not active_run_id or active_run_id not in discovered_workflows_cache:
        demo_run_id = "RUN-DEMO-001"
        active_run_id = demo_run_id
        analysis_jobs[demo_run_id] = {
            "run_id": demo_run_id,
            "dataset_name": "Synthetic IT Tickets (3,000)",
            "status": "COMPLETED",
            "progress": 100,
            "created_at": datetime.utcnow().isoformat()
        }
        _execute_analysis_pipeline(demo_run_id, 65.0, 0.75, 6)

    workflows = discovered_workflows_cache.get(active_run_id, [])
    full_tickets, total_tickets = repo.get_tickets(limit=1)

    total_monthly_hours = round(sum(w.metrics.total_handling_hours_per_month for w in workflows), 1)
    total_potential_monthly_savings_hours = round(sum(w.metrics.potential_hours_saved_per_month for w in workflows), 1)
    total_potential_annual_savings_cost = round(sum(w.metrics.potential_annual_cost_savings for w in workflows), 2)

    top_opportunities = [
        {
            "workflow_id": w.workflow_id,
            "workflow_name": w.workflow_name,
            "tickets_per_month": w.metrics.tickets_per_month,
            "total_handling_hours_per_month": w.metrics.total_handling_hours_per_month,
            "potential_annual_cost_savings": w.metrics.potential_annual_cost_savings,
            "priority_score": w.metrics.priority_score,
            "priority_rank": w.metrics.priority_rank,
            "implementation_complexity": w.implementation_complexity
        }
        for w in workflows[:5]
    ]

    distribution = [
        {
            "workflow_id": w.workflow_id,
            "name": w.workflow_name,
            "ticket_count": w.cluster_size,
            "monthly_hours": w.metrics.total_handling_hours_per_month
        }
        for w in workflows
    ]

    return {
        "active_run_id": active_run_id,
        "total_tickets_analyzed": total_tickets,
        "workflows_discovered_count": len(workflows),
        "total_monthly_handling_hours": total_monthly_hours,
        "potential_monthly_savings_hours": total_potential_monthly_savings_hours,
        "potential_annual_cost_savings_usd": total_potential_annual_savings_cost,
        "top_opportunities": top_opportunities,
        "workflow_distribution": distribution,
        "cloud_mode_enabled": is_cloud_mode_ready(),
        "app_mode": settings.APP_MODE
    }


@app.post("/api/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads and ingests a custom CSV ticket dataset."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    save_path = os.path.join(settings.DATA_DIR, f"upload_{uuid.uuid4().hex[:8]}_{file.filename}")
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    res = repo.ingest_csv(save_path, dataset_name=file.filename)
    return res


@app.post("/api/datasets/generate-synthetic")
def generate_synthetic(req: SyntheticGenerateRequest):
    """Generates synthetic dataset deterministically."""
    csv_path = os.path.join(settings.DATA_DIR, f"synthetic_tickets_{req.count}.csv")
    tickets, manifest = generate_synthetic_dataset(num_tickets=req.count, seed=req.seed)
    save_dataset_to_csv(tickets, csv_path, include_ground_truth=True)
    
    with open("data/ground_truth_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    res = repo.ingest_csv(csv_path, dataset_name=f"Generated Synthetic ({req.count} tickets)")
    return {
        "message": f"Successfully generated and ingested {req.count} tickets.",
        "ingestion_result": res,
        "planted_workflows": manifest["workflows"]
    }


@app.get("/api/tickets")
def get_tickets(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    workflow_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Queries tickets with pagination and filters."""
    tickets, total = repo.get_tickets(limit=limit, offset=offset, category=category, workflow_id=workflow_id, search=search)
    return {
        "items": tickets,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """Retrieves single ticket with workflow explanation."""
    t = repo.get_ticket_by_id(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t


@app.post("/api/analysis/run")
def start_analysis_run(req: AnalysisRunRequest, background_tasks: BackgroundTasks):
    """Starts asynchronous workflow mining run."""
    global active_run_id
    run_id = f"RUN-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    active_run_id = run_id
    
    analysis_jobs[run_id] = {
        "run_id": run_id,
        "dataset_name": req.dataset_name,
        "status": "QUEUED",
        "progress": 0,
        "message": "Analysis queued for background processing...",
        "created_at": datetime.utcnow().isoformat()
    }
    
    background_tasks.add_task(
        _execute_analysis_pipeline,
        run_id,
        req.hourly_labor_rate or 65.0,
        req.automatable_percentage or 0.75,
        req.n_clusters or 6
    )
    
    return {"run_id": run_id, "status": "QUEUED"}


@app.get("/api/analysis/{run_id}")
def get_analysis_status(run_id: str):
    """Polls analysis status."""
    if run_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Analysis run ID not found")
    return analysis_jobs[run_id]


@app.get("/api/workflows")
def get_workflows(run_id: Optional[str] = None):
    """Returns ranked list of discovered workflows."""
    target_run = run_id or active_run_id
    if not target_run or target_run not in discovered_workflows_cache:
        # Return fallback or empty
        return []
    return discovered_workflows_cache[target_run]


@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: str, run_id: Optional[str] = None):
    """Returns details for a specific workflow."""
    target_run = run_id or active_run_id
    workflows = discovered_workflows_cache.get(target_run, [])
    for w in workflows:
        if w.workflow_id == workflow_id:
            return w
    raise HTTPException(status_code=404, detail="Workflow not found")


@app.get("/api/workflows/{workflow_id}/tickets")
def get_workflow_tickets(workflow_id: str):
    """Returns tickets assigned to a workflow cluster."""
    tickets, total = repo.get_tickets(limit=100, workflow_id=workflow_id)
    return {"tickets": tickets, "total": total}


@app.post("/api/automations/draft")
def draft_automation_spec(workflow_id: str, run_id: Optional[str] = None):
    """Drafts automation specification for selected workflow."""
    target_run = run_id or active_run_id
    workflows = discovered_workflows_cache.get(target_run, [])
    target_wf = next((w for w in workflows if w.workflow_id == workflow_id), None)
    if not target_wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    rep_tickets, _ = repo.get_tickets(limit=5, workflow_id=workflow_id)
    spec = agent.draft_specification(target_wf, rep_tickets, target_run or "MANUAL-RUN")
    automation_specs_cache[spec.draft_id] = spec
    return spec


@app.get("/api/automations/{draft_id}")
def get_automation_spec(draft_id: str):
    """Retrieves drafted specification."""
    if draft_id not in automation_specs_cache:
        # If looking for first available draft
        if automation_specs_cache:
            return list(automation_specs_cache.values())[0]
        raise HTTPException(status_code=404, detail="Automation draft not found")
    return automation_specs_cache[draft_id]


@app.post("/api/automations/{draft_id}/review")
def review_automation_spec(draft_id: str, review: ReviewRequest):
    """
    Submits human review decision.
    MANDATORY SAFETY BOUNDARY: Approval records a review decision, never executes the automation.
    """
    if draft_id not in automation_specs_cache:
        raise HTTPException(status_code=404, detail="Automation draft not found")
        
    spec = automation_specs_cache[draft_id]
    updated_spec = agent.process_review(spec, review)
    automation_specs_cache[draft_id] = updated_spec
    return updated_spec


@app.get("/api/evaluation/{run_id}")
def get_evaluation_report(run_id: str):
    """Retrieves Stage F evaluation report comparing predictions to ground truth."""
    if run_id not in evaluation_reports_cache:
        # If run exists, compute report on the fly
        target_run = run_id or active_run_id
        workflows = discovered_workflows_cache.get(target_run, [])
        if workflows:
            tickets, _ = repo.get_tickets(limit=10000)
            spec = list(automation_specs_cache.values())[0] if automation_specs_cache else None
            rep = evaluator.evaluate_run(run_id, "Synthetic Dataset", tickets, workflows, spec)
            evaluation_reports_cache[run_id] = rep
            return rep
        raise HTTPException(status_code=404, detail="Evaluation report not found")
    return evaluation_reports_cache[run_id]


@app.get("/api/exports/automation/{draft_id}")
def export_automation_spec(draft_id: str, format: str = Query("markdown", pattern="^(markdown|json)$")):
    """Exports automation specification as clean Markdown or JSON."""
    if draft_id not in automation_specs_cache:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    spec = automation_specs_cache[draft_id]
    if format == "markdown":
        md = agent.export_specification_markdown(spec)
        return PlainTextResponse(content=md, media_type="text/markdown")
    else:
        return JSONResponse(content=spec.dict())


# Serve frontend static assets if built
frontend_dist_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
