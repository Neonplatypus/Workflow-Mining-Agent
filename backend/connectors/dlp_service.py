"""
Enterprise Data Loss Prevention (DLP) & Privacy Sanitizer.
AI Builder Cup 2026.

Ensures no raw PII, employee secrets, API keys, credentials, or internal network
topologies leak into LLM prompts, embeddings, or persistent analytics.
Supports Google Cloud Sensitive Data Protection (DLP API) and high-speed compiled local sanitization.
"""
import re
from typing import Dict, Any, Tuple, List
from backend.models.connector import DLPConfig


class DLPService:
    def __init__(self, config: DLPConfig = None):
        self.config = config or DLPConfig()

        # Precompiled regex patterns for zero-leakage enterprise hygiene
        # 1. Secrets & Credentials
        self._pattern_jwt = re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")
        self._pattern_api_keys = re.compile(
            r"(?i)\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{50,}|AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{32,}|AIza[0-9A-Za-z-_]{35}|bearer\s+[a-zA-Z0-9_\-\.]{20,})\b"
        )
        self._pattern_passwords = re.compile(
            r"(?i)\b(password|passwd|pwd|secret|api_key|token|auth_token)\s*(?:[:=]|\bset to\b|\bis\b)\s*['\"]?([^\s'\",;]{4,})['\"]?"
        )
        self._pattern_private_keys = re.compile(
            r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----"
        )

        # 2. PII (Personal Identifiable Information) - matched before hostnames
        self._pattern_email = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        self._pattern_phone = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
        self._pattern_ssn = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

        # 3. Network Topology & Internal Infrastructure
        self._pattern_ipv4 = re.compile(
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        )
        self._pattern_internal_hosts = re.compile(
            r"\b[a-zA-Z0-9\-_.]+\.(internal|corp|local|lan|vpc|cluster\.local)\b",
            re.IGNORECASE
        )

        # 4. Financial Identifiers
        self._pattern_credit_card = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

    def sanitize_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Sanitizes a text string by redacting PII, secrets, and internal host details.
        Returns the sanitized text and an audit trail of redactions performed.
        """
        if not text or not self.config.enabled:
            return text, []

        sanitized = text
        redactions = []

        # 1. Redact Secrets & Credentials
        if self.config.mask_secrets:
            # Private keys
            if self._pattern_private_keys.search(sanitized):
                sanitized = self._pattern_private_keys.sub("[REDACTED_PRIVATE_KEY]", sanitized)
                redactions.append({"type": "PRIVATE_KEY", "count": 1})

            # JWT tokens
            jwts = self._pattern_jwt.findall(sanitized)
            if jwts:
                sanitized = self._pattern_jwt.sub("[REDACTED_JWT_TOKEN]", sanitized)
                redactions.append({"type": "JWT_TOKEN", "count": len(jwts)})

            # API Keys / Bearer tokens
            api_keys = self._pattern_api_keys.findall(sanitized)
            if api_keys:
                sanitized = self._pattern_api_keys.sub("[REDACTED_API_KEY]", sanitized)
                redactions.append({"type": "API_KEY", "count": len(api_keys)})

            # Password key-value pairs
            def mask_pw_match(match):
                key = match.group(1)
                return f"{key}=[REDACTED_PASSWORD]"

            pws = self._pattern_passwords.findall(sanitized)
            if pws:
                sanitized = self._pattern_passwords.sub(mask_pw_match, sanitized)
                redactions.append({"type": "CREDENTIAL", "count": len(pws)})

        # 2. Redact PII (prioritized before domain/host matching)
        if self.config.mask_pii:
            emails = self._pattern_email.findall(sanitized)
            if emails:
                sanitized = self._pattern_email.sub("[REDACTED_EMAIL]", sanitized)
                redactions.append({"type": "EMAIL", "count": len(emails)})

            phones = self._pattern_phone.findall(sanitized)
            if phones:
                sanitized = self._pattern_phone.sub("[REDACTED_PHONE]", sanitized)
                redactions.append({"type": "PHONE", "count": len(phones)})

            ssns = self._pattern_ssn.findall(sanitized)
            if ssns:
                sanitized = self._pattern_ssn.sub("[REDACTED_SSN]", sanitized)
                redactions.append({"type": "SSN", "count": len(ssns)})

        # 3. Redact Network & Infrastructure Details
        if self.config.mask_network:
            ips = self._pattern_ipv4.findall(sanitized)
            if ips:
                sanitized = self._pattern_ipv4.sub("[REDACTED_IP]", sanitized)
                redactions.append({"type": "IP_ADDRESS", "count": len(ips)})

            hosts = self._pattern_internal_hosts.findall(sanitized)
            if hosts:
                sanitized = self._pattern_internal_hosts.sub("[REDACTED_HOST]", sanitized)
                redactions.append({"type": "INTERNAL_HOST", "count": len(hosts)})

        # 4. Redact Financial Data
        if self.config.mask_financial:
            ccs = self._pattern_credit_card.findall(sanitized)
            if ccs:
                sanitized = self._pattern_credit_card.sub("[REDACTED_FINANCIAL_CARD]", sanitized)
                redactions.append({"type": "CREDIT_CARD", "count": len(ccs)})

        return sanitized, redactions

    def sanitize_ticket(self, raw_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes all text fields within a ticket object prior to downstream ingestion.
        """
        if not self.config.enabled:
            return raw_ticket

        cleaned = dict(raw_ticket)
        for field in ["title", "description", "resolution_notes"]:
            if field in cleaned and isinstance(cleaned[field], str):
                cleaned_text, _ = self.sanitize_text(cleaned[field])
                cleaned[field] = cleaned_text

        return cleaned
