"""
Connector Manager & Ingestion Orchestrator for Enterprise ITSM Connectors.
AI Builder Cup 2026.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from backend.models.connector import (
    ConnectorConfig,
    ConnectorType,
    AuthType,
    SyncStatus,
    SyncSummary,
    FieldMappingConfig,
    DLPConfig
)
from backend.connectors.base import BaseConnector
from backend.connectors.jira_connector import JiraConnector
from backend.connectors.servicenow_connector import ServiceNowConnector
from backend.repositories.ticket_repository import TicketRepository


class ConnectorManager:
    def __init__(self, repo: Optional[TicketRepository] = None):
        self.repo = repo or TicketRepository()
        self._connectors: Dict[str, ConnectorConfig] = {}
        self._sync_history: List[SyncSummary] = []
        self._init_default_presets()

    def _init_default_presets(self):
        """Initializes default enterprise sandbox connector configurations."""
        # 1. Jira Enterprise Sandbox Preset
        jira_cfg = ConnectorConfig(
            connector_id="jira-enterprise-01",
            name="Atlassian Jira Cloud (IT Service Desk)",
            connector_type=ConnectorType.JIRA,
            base_url="https://demo-corp.atlassian.net",
            auth_type=AuthType.API_TOKEN,
            username_or_email="cloud-admin@enterprise.demo",
            api_token_or_secret="demo-token-masked-xxxx",
            query_filter="project = 'IT' AND status IN ('Closed', 'Resolved') ORDER BY updated DESC",
            field_mapping=FieldMappingConfig(
                title_field="fields.summary",
                description_field="fields.description",
                resolution_notes_field="fields.resolution.description",
                category_field="fields.issuetype.name",
                priority_field="fields.priority.name",
                assignee_field="fields.assignee.displayName"
            ),
            dlp_config=DLPConfig(
                enabled=True,
                mask_pii=True,
                mask_secrets=True,
                mask_network=True
            ),
            total_tickets_synced=0,
            last_sync_status=SyncStatus.IDLE
        )
        self._connectors[jira_cfg.connector_id] = jira_cfg

        # 2. ServiceNow Enterprise Preset
        snow_cfg = ConnectorConfig(
            connector_id="servicenow-enterprise-01",
            name="ServiceNow Washington DC (Global Incident Management)",
            connector_type=ConnectorType.SERVICENOW,
            base_url="https://demo-corp.service-now.com",
            auth_type=AuthType.BASIC,
            username_or_email="admin.service_desk",
            api_token_or_secret="demo-pwd-masked-xxxx",
            query_filter="stateIN6,7^ORDERBYDESCsys_updated_on",
            field_mapping=FieldMappingConfig(
                title_field="short_description",
                description_field="description",
                resolution_notes_field="close_notes",
                category_field="category",
                priority_field="priority",
                assignee_field="assigned_to.display_value"
            ),
            dlp_config=DLPConfig(
                enabled=True,
                mask_pii=True,
                mask_secrets=True,
                mask_network=True
            ),
            total_tickets_synced=0,
            last_sync_status=SyncStatus.IDLE
        )
        self._connectors[snow_cfg.connector_id] = snow_cfg

    def get_connector(self, connector_id: str) -> Optional[ConnectorConfig]:
        return self._connectors.get(connector_id)

    def list_connectors(self) -> List[Dict[str, Any]]:
        result = []
        for c in self._connectors.values():
            d = c.model_dump()
            # Mask sensitive secret
            if d.get("api_token_or_secret"):
                d["api_token_or_secret"] = "••••••••••••••••"
            result.append(d)
        return result

    def upsert_connector(self, config: ConnectorConfig) -> ConnectorConfig:
        self._connectors[config.connector_id] = config
        return config

    def _create_instance(self, config: ConnectorConfig) -> BaseConnector:
        if config.connector_type == ConnectorType.JIRA:
            return JiraConnector(config)
        elif config.connector_type == ConnectorType.SERVICENOW:
            return ServiceNowConnector(config)
        else:
            raise ValueError(f"Unsupported connector type: {config.connector_type}")

    def test_connection(self, connector_id: str) -> Dict[str, Any]:
        cfg = self.get_connector(connector_id)
        if not cfg:
            raise KeyError(f"Connector '{connector_id}' not found.")
        instance = self._create_instance(cfg)
        return instance.test_connection()

    def sync_connector(self, connector_id: str, max_records: int = 100) -> SyncSummary:
        """
        Executes a live synchronization job for a configured connector:
        1. Queries provider API for raw tickets
        2. Applies dynamic field mapping
        3. Sanitizes PII/Secrets/IPs via Cloud DLP
        4. Ingests normalized tickets into repository
        """
        cfg = self.get_connector(connector_id)
        if not cfg:
            raise KeyError(f"Connector '{connector_id}' not found.")

        started_at = datetime.utcnow()
        t0 = time.time()
        cfg.last_sync_status = SyncStatus.RUNNING

        try:
            instance = self._create_instance(cfg)
            # Pull, map, and sanitize tickets
            normalized_tickets = instance.pull_and_normalize_tickets(max_records=max_records)
            
            # Ingest directly into database
            dataset_label = f"{cfg.name} ({cfg.connector_type})"
            ingest_res = self.repo.ingest_ticket_records(normalized_tickets, dataset_name=dataset_label)

            dur = round(time.time() - t0, 2)
            cfg.last_synced_at = datetime.utcnow()
            cfg.last_sync_status = SyncStatus.SUCCESS
            cfg.last_sync_message = f"Synchronized {ingest_res.valid_records} tickets in {dur}s."
            cfg.total_tickets_synced += ingest_res.valid_records

            summary = SyncSummary(
                connector_id=connector_id,
                connector_type=cfg.connector_type,
                status=SyncStatus.SUCCESS,
                tickets_fetched=len(normalized_tickets),
                tickets_sanitized=len(normalized_tickets),
                tickets_ingested=ingest_res.valid_records,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=dur
            )
            self._sync_history.append(summary)
            return summary

        except Exception as e:
            dur = round(time.time() - t0, 2)
            cfg.last_synced_at = datetime.utcnow()
            cfg.last_sync_status = SyncStatus.FAILED
            cfg.last_sync_message = str(e)

            summary = SyncSummary(
                connector_id=connector_id,
                connector_type=cfg.connector_type,
                status=SyncStatus.FAILED,
                tickets_fetched=0,
                tickets_sanitized=0,
                tickets_ingested=0,
                errors=[str(e)],
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=dur
            )
            self._sync_history.append(summary)
            return summary
