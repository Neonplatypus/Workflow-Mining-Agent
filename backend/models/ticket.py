"""
Data models for tickets, schemas, and ingestion validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TicketBase(BaseModel):
    ticket_id: str = Field(..., description="Unique ticket identifier")
    title: str = Field(..., description="Ticket summary title")
    description: str = Field(..., description="Detailed description of the issue or request")
    category: str = Field(default="IT Support", description="Ticket category")
    priority: str = Field(default="Medium", description="Low, Medium, High, Critical")
    created_at: datetime = Field(..., description="Ticket creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Ticket resolution timestamp")
    assignee: str = Field(default="Unassigned", description="Engineer or team assigned")
    resolution_notes: str = Field(default="", description="Engineer resolution notes")
    status: str = Field(default="Closed", description="Closed, Resolved, Open, In Progress")


class Ticket(TicketBase):
    """
    Standard Ticket model used by the application and API.
    Ground-truth fields are strictly isolated and marked Optional.
    The discovery agent and clustering pipeline MUST NOT access ground truth fields.
    """
    workflow_ground_truth: Optional[str] = Field(
        None,
        description="Hidden ground truth label for Stage F evaluation ONLY. Must never be used by discovery!"
    )
    handling_minutes_ground_truth: Optional[float] = Field(
        None,
        description="Hidden ground truth handling minutes for evaluation ONLY."
    )
    predicted_workflow_id: Optional[str] = Field(None, description="Discovered workflow cluster ID")
    similarity_score: Optional[float] = Field(None, description="Confidence/similarity score to cluster centroid")


class TicketSummary(BaseModel):
    ticket_id: str
    title: str
    category: str
    priority: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    assignee: str
    status: str
    predicted_workflow_id: Optional[str] = None


class TicketIngestionResult(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int
    errors: List[Dict[str, Any]] = []
    preview: List[Dict[str, Any]] = []
    dataset_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
