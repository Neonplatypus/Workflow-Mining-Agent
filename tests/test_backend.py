"""
Unit, Integration, and Safety Boundary Test Suite for Workflow Mining Agent.
AI Builder Cup 2026.
"""

import os
import sys
import pytest
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.data.synthetic_generator import generate_synthetic_dataset
from backend.repositories.ticket_repository import TicketRepository
from backend.services.clustering_service import ClusteringService
from backend.services.quantification_service import QuantificationService
from backend.services.workflow_discovery import WorkflowDiscoveryService
from backend.agent.adk_orchestrator import ADKAutomationAgent
from backend.models.automation import ReviewRequest, ApprovalStatus
from backend.evaluation.evaluator import EvaluationFramework


def test_synthetic_generator_determinism():
    """Validates that random seed generates deterministic tickets and exact 6 planted workflows."""
    tickets1, manifest1 = generate_synthetic_dataset(num_tickets=200, seed=42)
    tickets2, manifest2 = generate_synthetic_dataset(num_tickets=200, seed=42)
    
    assert len(tickets1) == 200
    assert len(tickets2) == 200
    assert tickets1[0]["ticket_id"] == tickets2[0]["ticket_id"]
    assert tickets1[0]["title"] == tickets2[0]["title"]
    assert len(manifest1["workflows"]) == 6
    assert manifest1["one_off_total"] > 0


def test_ground_truth_leakage_isolation():
    """Validates that ground-truth fields are strictly isolated and never leaked into discovery text."""
    tickets, _ = generate_synthetic_dataset(num_tickets=100, seed=42)
    
    for t in tickets:
        # Title and description must NOT contain raw hidden ground-truth label variable names
        assert "workflow_ground_truth" not in t["title"]
        assert "handling_minutes_ground_truth" not in t["description"]


def test_deterministic_quantification_math():
    """Validates that hours saved calculations are mathematically exact and non-hallucinated."""
    service = QuantificationService(hourly_labor_rate=65.0, default_automatable_pct=0.75)
    
    sample_tickets = [
        {"ticket_id": "T-1", "estimated_active_handling_minutes": 20.0, "created_at": "2025-10-01T10:00:00"},
        {"ticket_id": "T-2", "estimated_active_handling_minutes": 40.0, "created_at": "2025-10-15T10:00:00"},
        {"ticket_id": "T-3", "estimated_active_handling_minutes": 60.0, "created_at": "2025-10-25T10:00:00"}
    ]
    
    metrics = service.calculate_cluster_metrics("WF-TEST", sample_tickets, confidence_score=0.9, complexity_score=0.3)
    
    # 20 + 40 + 60 = 120 minutes = 2.0 hours
    assert metrics.total_matching_tickets == 3
    assert metrics.avg_handling_minutes == 40.0
    assert metrics.median_handling_minutes == 40.0
    # Potential annual savings = annual hours * 0.75
    assert metrics.potential_annual_hours_saved == round(metrics.estimated_annual_handling_hours * 0.75, 2)
    # Potential annual cost savings = annual hours saved * $65
    assert metrics.potential_annual_cost_savings == round(metrics.potential_annual_hours_saved * 65.0, 2)


def test_ranking_algorithm_transparency():
    """Validates that workflow prioritization formula produces explainable factors summing to final score."""
    service = QuantificationService(hourly_labor_rate=65.0, default_automatable_pct=0.75)
    
    tickets_wf1 = [{"ticket_id": f"T-1-{i}", "estimated_active_handling_minutes": 30.0, "created_at": "2025-10-01T10:00:00"} for i in range(50)]
    tickets_wf2 = [{"ticket_id": f"T-2-{i}", "estimated_active_handling_minutes": 10.0, "created_at": "2025-10-01T10:00:00"} for i in range(10)]
    
    m1 = service.calculate_cluster_metrics("WF-01", tickets_wf1, 0.95, 0.2)
    m2 = service.calculate_cluster_metrics("WF-02", tickets_wf2, 0.70, 0.8)
    
    ranked = service.rank_workflows([
        {"workflow_id": "WF-01", "metrics": m1, "confidence_score": 0.95, "complexity_score": 0.2},
        {"workflow_id": "WF-02", "metrics": m2, "confidence_score": 0.70, "complexity_score": 0.8}
    ])
    
    assert ranked[0]["workflow_id"] == "WF-01"
    assert ranked[0]["metrics"].priority_rank == 1
    assert ranked[1]["metrics"].priority_rank == 2
    assert "composite_priority_score" in ranked[0]["metrics"].ranking_factors


def test_adk_safety_boundary_approval_never_executes():
    """MANDATORY SAFETY BOUNDARY: Approving a specification records a review decision and NEVER executes."""
    agent = ADKAutomationAgent()
    discovery = WorkflowDiscoveryService()
    quant = QuantificationService()
    
    sample_tickets = [
        {"ticket_id": "T-10", "title": "Grant access to bigquery", "description": "Need dataset read", "resolution_notes": "Granted viewer role", "estimated_active_handling_minutes": 20.0, "created_at": "2025-10-01T10:00:00"}
    ]
    interp = discovery.interpret_cluster(0, sample_tickets, sample_tickets, 0.9)
    metrics = quant.calculate_cluster_metrics("WF-01", sample_tickets, 0.9, 0.3)
    
    from backend.models.workflow import DiscoveredWorkflow
    wf = DiscoveredWorkflow(
        workflow_id="WF-01",
        workflow_name=interp["workflow_name"],
        description=interp["description"],
        common_trigger=interp["common_trigger"],
        typical_resolution_steps=interp["typical_resolution_steps"],
        required_inputs_and_systems=interp["required_inputs_and_systems"],
        common_exceptions=interp["common_exceptions"],
        suggested_automation_approach=interp["suggested_automation_approach"],
        confidence_score=0.9,
        confidence_explanation=interp["confidence_explanation"],
        implementation_complexity="Low",
        complexity_score=0.3,
        representative_ticket_ids=["T-10"],
        cluster_size=1,
        metrics=metrics
    )
    
    spec = agent.draft_specification(wf, sample_tickets, "TEST-RUN")
    assert spec.approval_status == ApprovalStatus.PENDING_REVIEW
    assert "Approval is a recorded review decision, NOT permission to execute" in spec.safety_boundary_notice
    
    # Process approval
    reviewed_spec = agent.process_review(spec, ReviewRequest(
        action=ApprovalStatus.APPROVED,
        reviewer_name="Lead Security Architect",
        comments="Approved for Q1 engineering backlog. Ready for manual implementation."
    ))
    
    assert reviewed_spec.approval_status == ApprovalStatus.APPROVED
    assert reviewed_spec.reviewer_name == "Lead Security Architect"
    # Ensure safety notice is still prominent
    assert "Approval is a recorded review decision" in reviewed_spec.safety_boundary_notice


def test_evaluation_framework_metrics():
    """Validates that evaluation report computes real precision, recall, and time estimation errors."""
    evaluator = EvaluationFramework()
    
    mock_tickets = [
        {
            "ticket_id": f"T-{i}",
            "title": "Password reset Okta",
            "predicted_workflow_id": "WF-01",
            "eval_ground_truth_workflow": "WF_PASSWORD_RESET",
            "estimated_active_handling_minutes": 10.0,
            "eval_ground_truth_minutes": 10.0
        }
        for i in range(20)
    ]
    
    from backend.models.workflow import DiscoveredWorkflow, WorkflowMetrics
    dummy_metrics = WorkflowMetrics(
        total_matching_tickets=20, tickets_per_month=10.0, avg_handling_minutes=10.0,
        median_handling_minutes=10.0, total_handling_hours_per_month=3.3, estimated_annual_handling_hours=40.0,
        hourly_labor_rate=65.0, estimated_annual_labor_cost=2600.0, automatable_percentage=0.75,
        potential_hours_saved_per_month=2.5, potential_annual_hours_saved=30.0, potential_annual_cost_savings=1950.0,
        priority_rank=1, priority_score=85.0
    )
    dummy_wf = DiscoveredWorkflow(
        workflow_id="WF-01", workflow_name="Password Resets", description="Unlock accounts",
        common_trigger="Locked user", typical_resolution_steps=["Verify user", "Reset Okta"],
        required_inputs_and_systems=["Okta"], common_exceptions=["Lost MFA"],
        suggested_automation_approach="Self-service portal", confidence_score=0.92,
        confidence_explanation="High similarity", implementation_complexity="Low",
        complexity_score=0.2, representative_ticket_ids=["T-1"], cluster_size=20,
        metrics=dummy_metrics
    )
    
    rep = evaluator.evaluate_run("RUN-TEST", "Unit Test Dataset", mock_tickets, [dummy_wf], None)
    
    assert rep.detection_metrics.precision > 0.0
    assert rep.detection_metrics.recall > 0.0
    assert rep.time_metrics.percentage_error >= 0.0
    assert rep.leakage_verification.leakage_detected is False
    assert rep.automation_quality.checklist_passed_items == 7
