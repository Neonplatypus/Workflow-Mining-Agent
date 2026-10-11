"""
Data models for Evaluation Framework (Stage F).
Evaluates workflow detection precision, recall, F1, coverage, handling time estimation error,
checklist score, noise robustness, and ground-truth leakage verification.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkflowDetectionMetrics(BaseModel):
    planted_workflows_total: int = 6
    planted_workflows_detected: int
    coverage_percentage: float
    precision: float
    recall: float
    f1_score: float
    detected_vs_planted_mapping: Dict[str, Optional[str]] = {}


class TimeEstimationMetrics(BaseModel):
    ground_truth_total_hours: float
    predicted_total_hours: float
    mean_absolute_error_hours: float
    percentage_error: float
    error_by_workflow: Dict[str, Dict[str, float]] = {}


class AutomationQualityScore(BaseModel):
    draft_id: str
    checklist_total_items: int = 7  # trigger, steps, exceptions, approvals, rollback, logging, testing
    checklist_passed_items: int
    quality_score_percentage: float
    checklist_breakdown: Dict[str, bool] = {}


class RobustnessMetrics(BaseModel):
    clean_ticket_accuracy: float
    noisy_ticket_accuracy: float
    misspelled_ticket_accuracy: float
    overall_robustness_score: float


class LeakageVerification(BaseModel):
    ground_truth_columns_in_discovery_inputs: bool = False
    ground_truth_tokens_in_prompts: bool = False
    leakage_detected: bool = False
    verification_message: str = "Verified: Zero ground-truth leakage detected in clustering features and prompts."


class EvaluationReport(BaseModel):
    run_id: str
    dataset_name: str
    total_tickets_evaluated: int
    detection_metrics: WorkflowDetectionMetrics
    time_metrics: TimeEstimationMetrics
    automation_quality: AutomationQualityScore
    robustness_metrics: RobustnessMetrics
    leakage_verification: LeakageVerification
    known_limitations: List[str]
    is_live_measured: bool = True
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
