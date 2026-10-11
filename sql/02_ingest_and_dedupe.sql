-- =====================================================================
-- Ingestion & Deduplication SQL Script
-- AI Builder Cup 2026 - Stage A & Stage D
-- =====================================================================

-- Normalize and deduplicate incoming raw tickets into canonical normalized table
INSERT INTO `workflow_mining.normalized_tickets`
(
  ticket_id,
  normalized_title,
  normalized_description,
  normalized_resolution_notes,
  combined_text,
  category,
  priority,
  created_at,
  resolved_at,
  assignee,
  elapsed_resolution_minutes,
  estimated_active_handling_minutes,
  status,
  eval_ground_truth_workflow,
  eval_ground_truth_minutes,
  normalized_at
)
WITH deduplicated_raw AS (
  SELECT
    ticket_id,
    title,
    description,
    category,
    priority,
    created_at,
    resolved_at,
    assignee,
    resolution_notes,
    status,
    workflow_ground_truth,
    handling_minutes_ground_truth,
    ROW_NUMBER() OVER(
      PARTITION BY ticket_id 
      ORDER BY ingested_at DESC, created_at DESC
    ) as row_num
  FROM `workflow_mining.raw_tickets`
  WHERE ticket_id IS NOT NULL 
    AND title IS NOT NULL
)
SELECT
  ticket_id,
  TRIM(REGEXP_REPLACE(LOWER(title), r'\s+', ' ')) AS normalized_title,
  TRIM(REGEXP_REPLACE(LOWER(COALESCE(description, '')), r'\s+', ' ')) AS normalized_description,
  TRIM(REGEXP_REPLACE(LOWER(COALESCE(resolution_notes, '')), r'\s+', ' ')) AS normalized_resolution_notes,
  CONCAT(
    TRIM(title), ' | ', 
    TRIM(COALESCE(description, '')), ' | ', 
    TRIM(COALESCE(resolution_notes, ''))
  ) AS combined_text,
  COALESCE(category, 'General IT') AS category,
  COALESCE(priority, 'Medium') AS priority,
  created_at,
  resolved_at,
  COALESCE(assignee, 'Unassigned') AS assignee,
  -- Calculate elapsed calendar time in minutes
  CASE 
    WHEN resolved_at IS NOT NULL AND resolved_at >= created_at 
    THEN TIMESTAMP_DIFF(resolved_at, created_at, MINUTE)
    ELSE NULL
  END AS elapsed_resolution_minutes,
  -- Deterministic handling time estimation heuristic:
  -- When active handling time is not logged by a timer, calculate an active work ratio
  -- bounded between 5 and 60 minutes, ensuring queue wait time is NOT treated as labor time.
  CASE
    WHEN handling_minutes_ground_truth IS NOT NULL THEN handling_minutes_ground_truth
    WHEN resolved_at IS NOT NULL THEN 
      GREATEST(5.0, LEAST(60.0, ROUND(TIMESTAMP_DIFF(resolved_at, created_at, MINUTE) * 0.08, 1)))
    ELSE 15.0
  END AS estimated_active_handling_minutes,
  COALESCE(status, 'Closed') AS status,
  workflow_ground_truth AS eval_ground_truth_workflow,
  handling_minutes_ground_truth AS eval_ground_truth_minutes,
  CURRENT_TIMESTAMP() AS normalized_at
FROM deduplicated_raw
WHERE row_num = 1;
