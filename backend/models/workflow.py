"""
Data models for discovered workflows, deterministic metrics, and prioritization rankings.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkflowMetrics(BaseModel):
    """
    Deterministic quantitative metrics calculated via SQL (BigQuery / analytical SQL engine).
    Never invented by LLM!
    """
    total_matching_tickets: int = Field(..., description="Count of tickets mapped to this workflow")
    tickets_per_month: float = Field(..., description="Average monthly frequency")
    avg_handling_minutes: float = Field(..., description="Average active handling minutes per ticket")
    median_handling_minutes: float = Field(..., description="Median active handling minutes per ticket")
    total_handling_hours_per_month: float = Field(..., description="Sum of handling minutes per month / 60")
    estimated_annual_handling_hours: float = Field(..., description="Monthly handling hours * 12")
    hourly_labor_rate: float = Field(default=65.0, description="Configured labor rate in USD/hour")
    estimated_annual_labor_cost: float = Field(..., description="Annual hours * hourly rate")
    automatable_percentage: float = Field(default=0.75, description="Estimated automatable portion (e.g. 0.75)")
    potential_hours_saved_per_month: float = Field(..., description="Monthly hours * automatable percentage")
    potential_annual_hours_saved: float = Field(..., description="Annual hours * automatable percentage")
    potential_annual_cost_savings: float = Field(..., description="Annual hours saved * labor rate")
    
    # Priority score breakdown
    priority_rank: int = Field(default=1, description="Ranking among discovered workflows")
    priority_score: float = Field(..., description="Calculated prioritization score (0 to 100)")
    ranking_factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Transparent breakdown: savings weight, recurrence weight, confidence, complexity"
    )
    calculation_assumptions: List[str] = Field(
        default_factory=list,
        description="Explicit assumptions used for this estimate"
    )


class DiscoveredWorkflow(BaseModel):
    """
    Semantic pattern discovered across tickets, interpreted by Gemini and quantified by SQL.
    """
    workflow_id: str = Field(..., description="e.g. WF-ACCESS-01")
    workflow_name: str = Field(..., description="Clear human-readable name")
    description: str = Field(..., description="Plain-language business description")
    common_trigger: str = Field(..., description="What initiates this workflow")
    typical_resolution_steps: List[str] = Field(default_factory=list, description="Extracted resolution steps")
    required_inputs_and_systems: List[str] = Field(default_factory=list, description="Systems, APIs, inputs")
    common_exceptions: List[str] = Field(default_factory=list, description="Identified exceptions or variations")
    suggested_automation_approach: str = Field(..., description="API-based, webhook, runbook bot, etc.")
    confidence_score: float = Field(..., description="Cluster semantic coherence score 0.0 - 1.0")
    confidence_explanation: str = Field(..., description="Why the agent scored this confidence")
    implementation_complexity: str = Field(default="Medium", description="Low, Medium, High")
    complexity_score: float = Field(default=0.4, description="0.0 to 1.0 (lower is easier to automate)")
    representative_ticket_ids: List[str] = Field(default_factory=list, description="IDs of representative tickets")
    metrics: WorkflowMetrics
    cluster_size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
