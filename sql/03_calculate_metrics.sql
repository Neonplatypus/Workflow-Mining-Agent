-- =====================================================================
-- Deterministic Workflow Metrics Calculation in SQL
-- AI Builder Cup 2026 - Stage D
--
-- CORE PRINCIPLE:
-- AI identifies and explains patterns; deterministic SQL calculates the numbers.
-- No metric or dollar amount is ever invented by Gemini.
-- =====================================================================

-- Parameters provided by API/User:
-- @run_id: STRING
-- @hourly_labor_rate: FLOAT64 (default: 65.00)
-- @default_automatable_pct: FLOAT64 (default: 0.75)

WITH workflow_tickets AS (
  SELECT
    a.run_id,
    a.workflow_id,
    t.ticket_id,
    t.created_at,
    t.estimated_active_handling_minutes,
    EXTRACT(YEAR FROM t.created_at) as t_year,
    EXTRACT(MONTH FROM t.created_at) as t_month
  FROM `workflow_mining.ticket_workflow_assignments` a
  JOIN `workflow_mining.normalized_tickets` t
    ON a.ticket_id = t.ticket_id
  WHERE a.run_id = @run_id
),

-- 1. Date Span & Monthly Frequency
workflow_date_span AS (
  SELECT
    workflow_id,
    COUNT(DISTINCT CONCAT(CAST(t_year AS STRING), '-', CAST(t_month AS STRING))) AS active_months_count,
    GREATEST(
      1.0, 
      DATE_DIFF(MAX(DATE(created_at)), MIN(DATE(created_at)), MONTH) + 1.0
    ) AS span_months
  FROM workflow_tickets
  GROUP BY workflow_id
),

-- 2. Aggregations & Handling Statistics
workflow_stats AS (
  SELECT
    wt.workflow_id,
    COUNT(wt.ticket_id) AS total_matching_tickets,
    ROUND(AVG(wt.estimated_active_handling_minutes), 1) AS avg_handling_minutes,
    -- Median calculation via percentile_cont
    PERCENTILE_CONT(wt.estimated_active_handling_minutes, 0.5) OVER(PARTITION BY wt.workflow_id) AS median_handling_minutes,
    SUM(wt.estimated_active_handling_minutes) AS total_handling_minutes_sum,
    ROW_NUMBER() OVER(PARTITION BY wt.workflow_id ORDER BY wt.ticket_id) as row_id
  FROM workflow_tickets wt
  GROUP BY wt.workflow_id, wt.estimated_active_handling_minutes, wt.ticket_id
),

workflow_summary AS (
  SELECT
    s.workflow_id,
    MAX(s.total_matching_tickets) AS total_matching_tickets,
    MAX(s.avg_handling_minutes) AS avg_handling_minutes,
    MAX(s.median_handling_minutes) AS median_handling_minutes,
    MAX(s.total_handling_minutes_sum) AS total_handling_minutes_sum,
    d.span_months
  FROM workflow_stats s
  JOIN workflow_date_span d ON s.workflow_id = d.workflow_id
  GROUP BY s.workflow_id, d.span_months
)

SELECT
  GENERATE_UUID() AS metric_id,
  @run_id AS run_id,
  ws.workflow_id,
  ws.total_matching_tickets,
  ROUND(ws.total_matching_tickets / ws.span_months, 1) AS tickets_per_month,
  ws.avg_handling_minutes,
  ws.median_handling_minutes,
  -- Handling hours per month = SUM(handling minutes in span) / 60 / span_months
  ROUND((ws.total_handling_minutes_sum / 60.0) / ws.span_months, 2) AS total_handling_hours_per_month,
  -- Annual hours = monthly hours * 12
  ROUND(((ws.total_handling_minutes_sum / 60.0) / ws.span_months) * 12.0, 2) AS estimated_annual_handling_hours,
  @hourly_labor_rate AS hourly_labor_rate,
  -- Annual labor cost = annual hours * labor rate
  ROUND((((ws.total_handling_minutes_sum / 60.0) / ws.span_months) * 12.0) * @hourly_labor_rate, 2) AS estimated_annual_labor_cost,
  @default_automatable_pct AS automatable_percentage,
  -- Potential monthly hours saved
  ROUND(((ws.total_handling_minutes_sum / 60.0) / ws.span_months) * @default_automatable_pct, 2) AS potential_hours_saved_per_month,
  -- Potential annual hours saved
  ROUND((((ws.total_handling_minutes_sum / 60.0) / ws.span_months) * 12.0) * @default_automatable_pct, 2) AS potential_annual_hours_saved,
  -- Potential annual cost savings
  ROUND(((((ws.total_handling_minutes_sum / 60.0) / ws.span_months) * 12.0) * @default_automatable_pct) * @hourly_labor_rate, 2) AS potential_annual_cost_savings,
  CURRENT_TIMESTAMP() AS calculated_at
FROM workflow_summary ws;
