"""
Base Connector Interface for Enterprise ITSM Systems.
AI Builder Cup 2026.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.models.connector import ConnectorConfig, SyncSummary, SyncStatus
from backend.connectors.field_mapper import FieldMapper
from backend.connectors.dlp_service import DLPService


class ConnectorError(Exception):
    pass


class ConnectorAuthError(ConnectorError):
    pass


class ConnectorConnectionError(ConnectorError):
    pass


class BaseConnector(ABC):
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.mapper = FieldMapper(config.field_mapping)
        self.dlp = DLPService(config.dlp_config)

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Validates network connectivity and credentials with the upstream ITSM provider."""
        pass

    @abstractmethod
    def fetch_raw_tickets(self, max_records: int = 100, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Pulls raw ticket records from the provider API with pagination."""
        pass

    def pull_and_normalize_tickets(self, max_records: int = 100, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Pulls raw tickets, normalizes them through the FieldMapper,
        and sanitizes them via the DLPService before returning.
        """
        raw_tickets = self.fetch_raw_tickets(max_records=max_records, since=since)
        normalized_list = []

        for raw in raw_tickets:
            # 1. Map to canonical schema
            canonical = self.normalize_raw_ticket(raw)
            # 2. Apply DLP sanitization to redact PII, tokens, IPs
            sanitized = self.dlp.sanitize_ticket(canonical)
            normalized_list.append(sanitized)

        return normalized_list

    @abstractmethod
    def normalize_raw_ticket(self, raw_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Translates a single raw payload dictionary to the canonical format."""
        pass
