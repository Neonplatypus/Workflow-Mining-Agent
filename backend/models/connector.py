"""
Data models for Enterprise Ingestion Connectors (Jira, ServiceNow, DLP).
AI Builder Cup 2026.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ConnectorType(str, Enum):
    JIRA = "JIRA"
    SERVICENOW = "SERVICENOW"
    GENERIC_REST = "GENERIC_REST"
    CSV = "CSV"


class AuthType(str, Enum):
    API_TOKEN = "API_TOKEN"
    BASIC = "BASIC"
    OAUTH2 = "OAUTH2"


class SyncStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class FieldMappingConfig(BaseModel):
    """
    Dynamic field mapping configuration to adapt any ITSM custom fields
    to the canonical ticket schema.
    """
    title_field: str = Field(default="summary", description="Source field for ticket title")
    description_field: str = Field(default="description", description="Source field for ticket description")
    resolution_notes_field: str = Field(default="resolution_notes", description="Source field for engineer resolution notes or close notes")
    category_field: str = Field(default="category", description="Source field for ticket category")
    priority_field: str = Field(default="priority", description="Source field for ticket priority")
    assignee_field: str = Field(default="assignee", description="Source field for assignee")
    created_at_field: str = Field(default="created", description="Source field for created timestamp")
    resolved_at_field: str = Field(default="resolutiondate", description="Source field for resolution timestamp")
    handling_time_field: Optional[str] = Field(default=None, description="Field for spent minutes/seconds (e.g. timespent, time_worked)")
    status_field: str = Field(default="status", description="Source field for ticket status")
    custom_field_rules: Dict[str, str] = Field(default_factory=dict, description="Arbitrary custom field lookups (e.g. {'customfield_10024': 'resolution_notes'})")


class DLPConfig(BaseModel):
    """
    Google Cloud DLP & Privacy Sanitization rules.
    Applied before raw ticket text touches embeddings or LLMs.
    """
    enabled: bool = Field(default=True, description="Enable automatic DLP sanitization")
    mask_pii: bool = Field(default=True, description="Mask employee names, emails, phone numbers")
    mask_secrets: bool = Field(default=True, description="Mask passwords, API keys, bearer tokens")
    mask_network: bool = Field(default=True, description="Mask internal IP addresses, private hostnames, subnets")
    mask_financial: bool = Field(default=True, description="Mask credit card numbers, account identifiers")
    redaction_placeholder: str = Field(default="[REDACTED_{TYPE}]", description="Placeholder template for masked items")


class ConnectorConfig(BaseModel):
    """
    Configuration for an enterprise ITSM source connector.
    """
    connector_id: str = Field(..., description="Unique connector identifier (e.g. jira-prod-01)")
    name: str = Field(..., description="Human readable name (e.g. Production Jira Cloud)")
    connector_type: ConnectorType = Field(..., description="ITSM Platform type")
    base_url: str = Field(..., description="Instance URL (e.g. https://company.atlassian.net or https://company.service-now.com)")
    auth_type: AuthType = Field(default=AuthType.API_TOKEN)
    username_or_email: Optional[str] = Field(None, description="Service account or admin email")
    api_token_or_secret: Optional[str] = Field(None, description="API token, PAT, or OAuth secret (masked in API responses)")
    query_filter: Optional[str] = Field(None, description="JQL query for Jira or sysparm_query for ServiceNow")
    field_mapping: FieldMappingConfig = Field(default_factory=FieldMappingConfig)
    dlp_config: DLPConfig = Field(default_factory=DLPConfig)
    auto_sync_interval_hours: int = Field(default=24, description="Periodic synchronization interval")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = None
    last_sync_status: SyncStatus = Field(default=SyncStatus.IDLE)
    last_sync_message: Optional[str] = None
    total_tickets_synced: int = Field(default=0)


class SyncSummary(BaseModel):
    connector_id: str
    connector_type: ConnectorType
    status: SyncStatus
    tickets_fetched: int
    tickets_sanitized: int
    tickets_ingested: int
    errors: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
