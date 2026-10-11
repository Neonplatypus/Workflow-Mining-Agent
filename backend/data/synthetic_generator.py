"""
Synthetic IT Service Ticket Generator for Workflow Mining Agent.
AI Builder Cup 2026 - Stage B.

Generates realistic IT service tickets with 6 planted repetitive workflows and noisy one-offs.
Deterministic via random seed.
Ground-truth fields are strictly marked and isolated for Stage F evaluation only.
"""

import random
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple


PLANTED_WORKFLOWS = {
    "WF_ACCESS_PROVISIONING": {
        "name": "Access Provisioning and Permission Requests",
        "description": "Granting IAM roles, folder permissions, repository access, or database credentials upon request.",
        "category": "Identity & Access",
        "typical_handling_range": (15, 30),  # minutes
        "templates": [
            ("Grant {role} access to {resource} for {user}",
             "User {user} requires {role} permissions on {resource} for upcoming project sprint. Manager approval attached.",
             "Verified manager sign-off via ticketing system. Added {user} to group {group} and bound {role} to {resource}. Verified permissions using policy analyzer. Notified user."),
            ("Permission escalation request: {resource}",
             "I cannot access {resource} with error HTTP 403 Forbidden. Need read/write access to deploy configs.",
             "Checked current IAM bindings. Found missing role {role}. Added binding in Cloud Console. User confirmed access restored."),
            ("Add {user} to GitHub repo {repo_name} team",
             "Please add contractor {user} to team {group} with write access to {repo_name}.",
             "Validated contractor security vetting status. Invited {user} to org team with {role} permissions. Sent onboarding guidelines."),
            ("Database read replica access for {user}",
             "Data analyst {user} requests read-only access to BigQuery analytical dataset {resource}.",
             "Generated least-privilege service credential / IAM dataViewer binding. Verified dataset expiration policy. Sent connection string and tested query."),
            ("Access request - {resource} - urgent",
             "Urgent: {user} blocked on client deliverable. Needs temporary elevation to {role} on {resource}.",
             "Obtained emergency change authorization. Granted temporary IAM binding with 24-hour TTL. Logged security audit ticket.")
        ],
        "roles": ["roles/bigquery.dataViewer", "roles/storage.objectAdmin", "roles/container.developer", "DevOps-Contributor", "Data-Analyst-L2"],
        "resources": ["project-analytics-prod", "gs://finance-raw-reports", "k8s-cluster-staging", "bi-reporting-bq", "repo/payment-service"],
        "groups": ["sec-cloud-devs", "fin-analytics-read", "devops-core", "app-engineers"],
        "repos": ["checkout-service", "data-pipeline-v2", "auth-gateway", "frontend-portal"]
    },
    "WF_ENV_RESET": {
        "name": "Development or Test Environment Resets",
        "description": "Restoring staging/test databases from sanitized snapshots, restarting services, and flushing caches.",
        "category": "Infrastructure",
        "typical_handling_range": (25, 45),  # minutes
        "templates": [
            ("Reset staging environment {env_id} for QA cycle",
             "Staging env {env_id} has corrupted test data from automated integration test run. Please restore to baseline clean snapshot.",
             "Drained ingress traffic on {env_id}. Executed backup restore script from master clean snapshot. Flushed Redis cache. Executed seed data migration. Ran smoke test suite: all 18 endpoints passed. Reopened to QA."),
            ("Staging test DB desync in {env_id} - restore requested",
             "Database state in {env_id} is inconsistent. FK constraints failing during checkout test. Need reset.",
             "Terminated active connections to Postgres DB. Restored anonymized schema snapshot v4.2. Restarted backend pods. Verified health check /healthz returned 200 OK."),
            ("Sandbox environment {env_id} cleanup and rebuild",
             "Sprint finished. Please teardown ephemeral resources in {env_id} and redeploy latest master branch.",
             "Triggered Cloud Build pipeline reset-sandbox. Shrunk StatefulSet to 0, purged PVCs, applied Terraform baseline. Deployed commit sha. Validated microservice mesh."),
            ("Flush cache and reseed mock data on {env_id}",
             "Automated tests running out of test customer accounts. Please flush Redis cluster and rerun seeder script.",
             "Connected to bastion host. Ran FLUSHDB on Redis cluster. Executed python seed_accounts.py --count 500. Verified mock data present.")
        ],
        "envs": ["staging-us-central1", "qa-regression-02", "dev-sandbox-blue", "perf-test-cluster", "uat-staging-01"]
    },
    "WF_LOG_DISK_CLEANUP": {
        "name": "Log Cleanup and Disk Space Remediation",
        "description": "Purging uncompressed log files, clearing /tmp directories, and rotating logs when disk alarms trigger.",
        "category": "Operations",
        "typical_handling_range": (15, 25),  # minutes
        "templates": [
            ("High Disk Space Alert: {host} filesystem at {pct}%",
             "Monitoring alert P2: Partition /var/log on VM {host} has reached {pct}% capacity. Immediate remediation required.",
             "SSHed into {host}. Identified unrotated debug logs in /var/log/app/ exceeding 45GB. Compressed historical logs >7 days into gzip. Purged old stdout.log files. Updated logrotate configuration. Disk usage dropped to 42%."),
            ("Disk full alert: {host} /tmp partition warning",
             "Host {host} reporting 94% inode and disk utilization on /tmp.",
             "Inspected /tmp on {host}. Found leftover docker build caches and orphan core dumps. Removed files older than 3 days. Cleaned systemd journal logs via journalctl --vacuum-time=3d. Usage normalized to 35%."),
            ("Remediate log buildup on worker node {host}",
             "Kubernetes node {host} reporting ephemeral-storage pressure. Pod eviction risk.",
             "Ran crictl rmi --prune to eliminate dangling container images. Cleaned /var/log/pods logs. Node status transitioned back to Ready with 68% free storage."),
            ("Routine storage remediation on {host}",
             "Automated metric alert: /data volume on {host} surpassed 88% watermark.",
             "Analyzed storage breakdown via ncdu. Archived completed batch output files to Cloud Storage bucket gs://coldline-archives/. Freed 120GB.")
        ],
        "hosts": ["gce-prod-api-01", "worker-batch-node-04", "k8s-node-pool-prod-7", "log-aggregator-vm-02", "bastion-relay-01"],
        "percentages": [91, 94, 96, 98, 92]
    },
    "WF_PASSWORD_RESET": {
        "name": "Password Resets and Account Unlocks",
        "description": "Verifying employee identity and resetting locked directory credentials or multi-factor tokens.",
        "category": "Helpdesk",
        "typical_handling_range": (8, 15),  # minutes
        "templates": [
            ("User account locked out after multiple failed attempts: {user}",
             "Employee {user} locked out of corporate Okta/Google Workspace. Self-service reset failed due to expired SMS MFA token.",
             "Verified employee identity via video call and Slack manager verification. Cleared account lockout in Okta Admin console. Generated one-time temporary access token valid 1 hour. Instructed user to register new WebAuthn FIDO key. Confirmed successful login."),
            ("Password expired and cannot login: {user}",
             "My domain password expired over the weekend and I cannot connect to VPN or corporate portal.",
             "Verified identity with badge ID lookup against HR database. Initiated self-service password reset workflow. Reset Active Directory password with 'Must change at next login' flag. Assisted user with Cisco AnyConnect VPN reconnection."),
            ("MFA token desync / new device setup for {user}",
             "Got a replacement company laptop/phone and lost Google Authenticator OTP token for {user}.",
             "Followed out-of-band identity verification protocol. Sent verification code to registered recovery email. Revoked old MFA tokens and enrolled new hardware token. Tested portal sign-in."),
            ("Account unlock request: {user}",
             "Help, typed wrong password 5 times on SSO page. Please unblock account.",
             "Looked up user {user} in directory. Account was in soft-lock state. Manually unlocked account and sent password reset link to verified phone number. Verified incident closed.")
        ]
    },
    "WF_DEPLOY_VALIDATION": {
        "name": "Routine Deployment and Configuration Validation",
        "description": "Post-deployment smoke testing, configuration validation, canary monitoring, and release sign-off.",
        "category": "DevOps",
        "typical_handling_range": (20, 35),  # minutes
        "templates": [
            ("Post-deployment verification for release {version} on {service}",
             "Scheduled release {version} deployed to production. Require manual smoke test, metric verification, and rollback readiness check.",
             "Executed automated post-deploy smoke tests against /healthz and /api/v1/ping. Checked Cloud Monitoring metrics for error rate spikes (5xx rate < 0.01%). Verified ConfigMap and Secret versions match release manifest. Confirmed release {version} stable and notified on-call lead."),
            ("Verify canary rollout of {service} {version}",
             "Traffic routing 10% canary for {service} release {version}. Monitor latency and error budget.",
             "Monitored Prometheus p95 latency and HTTP 500 error counts for 15 minutes. Latency stayed within SLA (<120ms). Compared logs with baseline. Promoted canary to 100% traffic. Sign-off recorded."),
            ("Config drift check and environment validation for {service}",
             "Please verify production configuration parameters for {service} align with staging release {version}.",
             "Extracted Kubernetes deployment yaml and compared with Helm values-prod.yaml. Found no drift. Ran integration health check. Appended validation log to release ticket.")
        ],
        "services": ["payment-gateway", "auth-service", "order-processing-api", "inventory-service", "search-indexer"],
        "versions": ["v2.14.0", "v3.1.2", "v2.15.1", "v4.0.0-rc3", "v1.9.8"]
    },
    "WF_CERT_SERVICE_ACCOUNT": {
        "name": "Service Account and Certificate Renewal Requests",
        "description": "Rotating expiring SSL/TLS certificates and service account keys across clusters and secrets managers.",
        "category": "Security",
        "typical_handling_range": (30, 50),  # minutes
        "templates": [
            ("SSL Certificate expiration warning: {domain} expiring in 14 days",
             "Certificate alert: TLS certificate for {domain} expires on next renewal window. Needs renewal and ingress reload.",
             "Generated new CSR using company CA / Google Certificate Manager. Issued renewed TLS cert with 365-day validity. Updated Secret 'tls-{domain}' in Kubernetes production namespace. Reloaded ingress controller without downtime. Verified handshake using openssl s_client -connect {domain}:443."),
            ("Rotate service account key for {service_account}",
             "Security compliance requirement: Service account key for {service_account} is 90 days old. Rotation required.",
             "Created new key pair for {service_account} via gcloud iam service-accounts keys create. Updated Google Secret Manager secret 'sa-key-{service_account}'. Performed rolling restart of dependent worker pods. Verified worker operational. Deleted deprecated old key from IAM."),
            ("mTLS internal certificate renewal for {domain}",
             "Service mesh mutual TLS certificate expiring for internal endpoint {domain}.",
             "Renewed root-signed client certificate. Distributed cert to Vault storage. Restarted Envoy sidecars. Confirmed mTLS connection status healthy.")
        ],
        "domains": ["api.corp.internal", "portal.payments.net", "staging-gateway.cloud", "auth.sso.internal"],
        "service_accounts": ["sa-bigquery-loader@prod.iam.gserviceaccount.com", "sa-pubsub-subscriber@prod.iam.gserviceaccount.com", "sa-cloudbuild-deployer@prod.iam.gserviceaccount.com"]
    }
}

ONE_OFF_TEMPLATES = [
    ("Broken laptop monitor / HDMI port flickering", "Laptop HDMI display flickers when connecting to external monitor at desk 4B.", "Hardware Support", 35, "Replaced faulty USB-C dongle and verified display output."),
    ("Conference room C Zoom room audio echo", "During all-hands meeting, microphones in Conf Room C cause severe echo.", "Facilities IT", 45, "Recalibrated ceiling microphone array and updated Zoom Rooms controller firmware."),
    ("Coffee machine smart display network offline", "Breakroom IoT touch panel not connecting to guest WiFi.", "Facilities IT", 20, "Rebooted local AP and rejoined IoT MAC address to isolated VLAN."),
    ("Keyboard sticky keys after coffee spill", "Spilled coffee on mechanical keyboard. Spacebar and enter keys sticking.", "Hardware Support", 15, "Swapped damaged keyboard with new standard-issue peripheral from IT depot."),
    ("Custom SQL query syntax error in reporting dashboard", "Getting syntax error 1064 in custom SQL query in Looker Studio report.", "Data Support", 55, "Assisted user with dialect syntax. Fixed unescaped reserved word in GROUP BY clause."),
    ("Third-party vendor API unexpected 502 Bad Gateway", "Stripe webhook integration returning intermittent 502 gateway errors.", "Third-Party Incidents", 60, "Checked Stripe status page; identified vendor incident. Subscribed to status updates and monitored resolution."),
    ("Slow WiFi in engineering annex 3rd floor", "Multiple users reporting packet loss and high latency on corporate-secure SSID.", "Network IT", 50, "Investigated Meraki dashboard. Found radio interference on channel 6. Switched AP to DFS channel; SNR normalized."),
    ("Need ergonomic mouse recommendation", "Ergonomic assessment suggested vertical mouse for wrist strain.", "IT Procurement", 10, "Approved standard Logitech MX Vertical requisition from IT equipment catalog."),
    ("Excel crashing when opening 500MB CSV file", "Finance analyst reporting Excel memory limit exceeded when opening client transaction dump.", "Desktop Support", 25, "Guided user to open dataset in BigQuery / Python Pandas instead of 32-bit Excel."),
    ("Printer paper jam on 2nd floor copier", "Copier Tray 2 jammed during print run of quarterly slides.", "Facilities IT", 15, "Cleared paper path obstruction in duplexing unit. Tested test print sheet successfully.")
]

ENGINEERS = [
    "Alex Chen (SRE)", "Priya Sharma (Cloud Ops)", "Marcus Vance (DevOps)", 
    "Jordan Taylor (IT Support)", "Elena Rostova (SecOps)", "David Kim (Platform Eng)",
    "Samira Khan (Cloud Identity)", "Carlos Mendez (Systems Eng)"
]

USER_NAMES = [
    "r.patel", "m.smith", "j.kowalski", "s.garcia", "t.nakamura", 
    "l.dupont", "a.fischer", "k.johansson", "v.singh", "b.williams"
]


def _introduce_noise(text: str, noise_type: str) -> str:
    """Adds realistic noise: typos, abbreviations, casing inconsistency."""
    if noise_type == "typo":
        replacements = [
            ("password", "pawword"), ("access", "acces"), ("environment", "enviornment"),
            ("staging", "stagging"), ("cleanup", "clenup"), ("storage", "stroage"),
            ("permission", "permision"), ("certificate", "certifcate"), ("account", "acct"),
            ("urgent", "urgnt"), ("database", "db"), ("restart", "restrt")
        ]
        for src, dst in replacements:
            if src in text.lower() and random.random() < 0.3:
                return text.replace(src, dst)
    elif noise_type == "abbrev":
        replacements = [
            ("production", "prod"), ("development", "dev"), ("administrator", "admin"),
            ("configuration", "config"), ("repository", "repo"), ("application", "app"),
            ("service account", "SA"), ("kubernetes", "k8s")
        ]
        for src, dst in replacements:
            if src in text.lower():
                return text.replace(src, dst)
    return text


def generate_synthetic_dataset(
    num_tickets: int = 3000,
    seed: int = 42,
    start_date: datetime = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generates a deterministic synthetic IT ticket dataset.
    
    Returns:
        (tickets_list, ground_truth_manifest)
    """
    random.seed(seed)
    if start_date is None:
        start_date = datetime(2025, 10, 1, 8, 0, 0)
    
    # Target distribution of tickets:
    # 75% planted repetitive workflows (distributed across 6 categories)
    # 25% one-off noise tickets
    num_planted = int(num_tickets * 0.75)
    num_one_offs = num_tickets - num_planted
    
    # Workflow distribution weights
    wf_keys = list(PLANTED_WORKFLOWS.keys())
    # WF1: Access (20%), WF2: Env (14%), WF3: Log (17%), WF4: Pwd (24%), WF5: Deploy (13%), WF6: Cert (12%)
    wf_weights = [0.20, 0.14, 0.17, 0.24, 0.13, 0.12]
    
    planted_counts = {wf: 0 for wf in wf_keys}
    tickets = []
    
    # Ground truth summary for evaluation comparison
    ground_truth_stats = {
        "seed": seed,
        "total_tickets": num_tickets,
        "planted_total": num_planted,
        "one_off_total": num_one_offs,
        "workflows": {
            wf: {
                "name": PLANTED_WORKFLOWS[wf]["name"],
                "count": 0,
                "total_handling_minutes": 0.0,
                "expected_hours_total": 0.0
            } for wf in wf_keys
        }
    }
    
    ticket_counter = 1
    
    # 1. Generate planted repetitive tickets
    for _ in range(num_planted):
        wf_key = random.choices(wf_keys, weights=wf_weights, k=1)[0]
        wf_meta = PLANTED_WORKFLOWS[wf_key]
        planted_counts[wf_key] += 1
        
        tmpl = random.choice(wf_meta["templates"])
        title_fmt, desc_fmt, res_fmt = tmpl
        
        # Format variables
        ctx = {
            "user": random.choice(USER_NAMES),
            "role": random.choice(wf_meta.get("roles", ["Viewer"])),
            "resource": random.choice(wf_meta.get("resources", ["cloud-prod"])),
            "group": random.choice(wf_meta.get("groups", ["all-engineers"])),
            "repo_name": random.choice(wf_meta.get("repos", ["main-app"])),
            "env_id": random.choice(wf_meta.get("envs", ["staging-01"])),
            "host": random.choice(wf_meta.get("hosts", ["srv-01"])),
            "pct": random.choice(wf_meta.get("percentages", [95])),
            "service": random.choice(wf_meta.get("services", ["core-api"])),
            "version": random.choice(wf_meta.get("versions", ["v1.0.0"])),
            "domain": random.choice(wf_meta.get("domains", ["app.internal"])),
            "service_account": random.choice(wf_meta.get("service_accounts", ["sa@proj.iam.gserviceaccount.com"]))
        }
        
        title = title_fmt.format(**ctx)
        desc = desc_fmt.format(**ctx)
        res_notes = res_fmt.format(**ctx)
        
        # Inject realistic noise: 20% typos, 25% abbreviations
        if random.random() < 0.20:
            title = _introduce_noise(title, "typo")
            desc = _introduce_noise(desc, "typo")
        elif random.random() < 0.25:
            title = _introduce_noise(title, "abbrev")
        
        # Handling time (ground truth)
        min_h, max_h = wf_meta["typical_handling_range"]
        # Add normal jitter
        handling_mins = round(max(3.0, random.gauss((min_h + max_h) / 2.0, (max_h - min_h) / 4.0)), 1)
        
        # Realistic timestamp over 90 days
        day_offset = random.randint(0, 90)
        hour_offset = random.randint(7, 19)
        minute_offset = random.randint(0, 59)
        created_dt = start_date + timedelta(days=day_offset, hours=hour_offset, minutes=minute_offset)
        
        # Resolution elapsed time (includes queue wait + active handling)
        # Note: Active handling time != elapsed calendar time!
        queue_wait_minutes = random.randint(10, 480)
        elapsed_minutes = queue_wait_minutes + int(handling_mins)
        resolved_dt = created_dt + timedelta(minutes=elapsed_minutes)
        
        # Priority distribution: mostly Medium/High
        priority = random.choices(["Low", "Medium", "High", "Critical"], weights=[0.15, 0.50, 0.25, 0.10], k=1)[0]
        
        ticket_id = f"TICK-{ticket_counter:05d}"
        ticket_counter += 1
        
        ticket_record = {
            "ticket_id": ticket_id,
            "title": title,
            "description": desc,
            "category": wf_meta["category"],
            "priority": priority,
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat(),
            "assignee": random.choice(ENGINEERS),
            "resolution_notes": res_notes,
            "status": "Closed",
            # Hidden evaluation fields ONLY
            "workflow_ground_truth": wf_key,
            "handling_minutes_ground_truth": handling_mins
        }
        tickets.append(ticket_record)
        
        # Accumulate ground truth stats
        ground_truth_stats["workflows"][wf_key]["count"] += 1
        ground_truth_stats["workflows"][wf_key]["total_handling_minutes"] += handling_mins

    # 2. Generate one-off noise tickets
    for _ in range(num_one_offs):
        one_off = random.choice(ONE_OFF_TEMPLATES)
        title, desc, cat, base_mins, res_note = one_off
        
        handling_mins = round(max(5.0, random.gauss(base_mins, 8.0)), 1)
        day_offset = random.randint(0, 90)
        created_dt = start_date + timedelta(days=day_offset, hours=random.randint(8, 18), minutes=random.randint(0, 59))
        resolved_dt = created_dt + timedelta(minutes=random.randint(30, 600) + int(handling_mins))
        
        ticket_id = f"TICK-{ticket_counter:05d}"
        ticket_counter += 1
        
        ticket_record = {
            "ticket_id": ticket_id,
            "title": title,
            "description": desc,
            "category": cat,
            "priority": random.choice(["Low", "Medium", "High"]),
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat(),
            "assignee": random.choice(ENGINEERS),
            "resolution_notes": res_note,
            "status": "Closed",
            # Ground truth: None / ONE_OFF
            "workflow_ground_truth": "ONE_OFF",
            "handling_minutes_ground_truth": handling_mins
        }
        tickets.append(ticket_record)

    # Shuffle dataset to mix planted and one-off tickets thoroughly
    random.shuffle(tickets)
    
    # Calculate final ground truth hours
    for wf in wf_keys:
        mins = ground_truth_stats["workflows"][wf]["total_handling_minutes"]
        ground_truth_stats["workflows"][wf]["expected_hours_total"] = round(mins / 60.0, 2)
        
    return tickets, ground_truth_stats


def save_dataset_to_csv(tickets: List[Dict[str, Any]], filepath: str, include_ground_truth: bool = True) -> None:
    """Saves tickets to CSV format."""
    if not tickets:
        return
    
    fieldnames = list(tickets[0].keys())
    if not include_ground_truth:
        fieldnames = [f for f in fieldnames if not f.endswith("_ground_truth")]
        
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in tickets:
            row = {k: t[k] for k in fieldnames}
            writer.writerow(row)
