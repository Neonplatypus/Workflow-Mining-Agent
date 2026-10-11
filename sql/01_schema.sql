-- =====================================================================
-- BigQuery Data Model Schema for Workflow Mining Agent
-- AI Builder Cup 2026 - Production DDL
-- =====================================================================

-- 1. Raw Ingested Tickets
CREATE TABLE IF NOT EXISTS `workflow_mining.raw_tickets` (
  raw_id STRING,
  ticket_id STRING,
  title STRING,
  description STRING,
  category STRING,
  priority STRING,
  created_at TIMESTAMP,
  resolved_at TIMESTAMP,
  assignee STRING,
  resolution_notes STRING,
  status STRING,
  -- Isolated ground truth fields (for evaluation only)
  workflow_ground_truth STRING,
  handling_minutes_ground_truth FLOAT64,
  ingestion_batch_id STRING,
  ingested_at TIMESTAMP
);

-- 2. Cleaned and Normalized Tickets
CREATE TABLE IF NOT EXISTS `workflow_mining.normalized_tickets` (
  ticket_id STRING,
  normalized_title STRING,
  normalized_description STRING,
  normalized_resolution_notes STRING,
  combined_text STRING,
  category STRING,
  priority STRING,
  created_at TIMESTAMP,
  resolved_at TIMESTAMP,
  assignee STRING,
  elapsed_resolution_minutes FLOAT64,
  estimated_active_handling_minutes FLOAT64,
  status STRING,
  -- Retained purely for Stage F evaluation table join
  eval_ground_truth_workflow STRING,
  eval_ground_truth_minutes FLOAT64,
  normalized_at TIMESTAMP
);

-- 3. Discovered Workflows
CREATE TABLE IF NOT EXISTS `workflow_mining.discovered_workflows` (
  workflow_id STRING,
  run_id STRING,
  workflow_name STRING,
  description STRING,
  category STRING,
  common_trigger STRING,
  typical_resolution_steps ARRAY<STRING>,
  required_inputs_and_systems ARRAY<STRING>,
  common_exceptions ARRAY<STRING>,
  suggested_automation_approach STRING,
  confidence_score FLOAT64,
  confidence_explanation STRING,
  implementation_complexity STRING,
  complexity_score FLOAT64,
  created_at TIMESTAMP
);

-- 4. Ticket to Discovered Workflow Assignments
CREATE TABLE IF NOT EXISTS `workflow_mining.ticket_workflow_assignments` (
  run_id STRING,
  ticket_id STRING,
  workflow_id STRING,
  cluster_distance FLOAT64,
  assignment_confidence FLOAT64,
  is_representative_sample BOOLEAN,
  assigned_at TIMESTAMP
);

-- 5. Deterministic Workflow Metrics (Computed purely via SQL)
CREATE TABLE IF NOT EXISTS `workflow_mining.workflow_metrics` (
  metric_id STRING,
  run_id STRING,
  workflow_id STRING,
  total_matching_tickets INT64,
  tickets_per_month FLOAT64,
  avg_handling_minutes FLOAT64,
  median_handling_minutes FLOAT64,
  total_handling_hours_per_month FLOAT64,
  estimated_annual_handling_hours FLOAT64,
  hourly_labor_rate FLOAT64,
  estimated_annual_labor_cost FLOAT64,
  automatable_percentage FLOAT64,
  potential_hours_saved_per_month FLOAT64,
  potential_annual_hours_saved FLOAT64,
  potential_annual_cost_savings FLOAT64,
  priority_rank INT64,
  priority_score FLOAT64,
  ranking_factors_json STRING,
  calculation_assumptions_json STRING,
  calculated_at TIMESTAMP
);

-- 6. Analysis Runs
CREATE TABLE IF NOT EXISTS `workflow_mining.analysis_runs` (
  run_id STRING,
  dataset_name STRING,
  total_tickets_processed INT64,
  workflows_discovered_count INT64,
  total_potential_annual_savings FLOAT64,
  top_recommended_workflow_id STRING,
  status STRING, -- 'RUNNING', 'COMPLETED', 'FAILED'
  model_name STRING,
  clustering_method STRING,
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- 7. Automation Specifications Drafted by Agent
CREATE TABLE IF NOT EXISTS `workflow_mining.automation_specifications` (
  draft_id STRING,
  run_id STRING,
  workflow_id STRING,
  workflow_name STRING,
  business_objective STRING,
  problem_statement STRING,
  specification_json STRING,
  pseudocode_markdown STRING,
  evidence_ticket_ids ARRAY<STRING>,
  created_at TIMESTAMP
);

-- 8. Human Review & Approval Records
CREATE TABLE IF NOT EXISTS `workflow_mining.human_reviews` (
  review_id STRING,
  draft_id STRING,
  workflow_id STRING,
  approval_status STRING, -- 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'REVISION_REQUESTED'
  reviewer_name STRING,
  reviewer_comments STRING,
  is_demo_user BOOLEAN,
  reviewed_at TIMESTAMP
);

-- 9. Evaluation Results (Stage F Ground Truth Validation)
CREATE TABLE IF NOT EXISTS `workflow_mining.evaluation_results` (
  eval_id STRING,
  run_id STRING,
  planted_workflows_total INT64,
  planted_workflows_detected INT64,
  coverage_percentage FLOAT64,
  precision FLOAT64,
  recall FLOAT64,
  f1_score FLOAT64,
  ground_truth_total_hours FLOAT64,
  predicted_total_hours FLOAT64,
  percentage_error FLOAT64,
  checklist_quality_percentage FLOAT64,
  leakage_detected BOOLEAN,
  evaluated_at TIMESTAMP
);
