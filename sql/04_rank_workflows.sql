-- =====================================================================
-- Deterministic Workflow Prioritization Ranking
-- AI Builder Cup 2026 - Stage D
--
-- Explainable Prioritization Formula:
-- Score (0-100) =
--   (Normalized Potential Annual Savings * 40%) +
--   (Normalized Frequency / Recurrence   * 25%) +
--   (Confidence Score                    * 20%) +
--   ((1.0 - Complexity Score)            * 15%)
-- =====================================================================

WITH raw_metrics AS (
  SELECT
    m.*,
    w.workflow_name,
    w.confidence_score,
    w.complexity_score,
    w.implementation_complexity
  FROM `workflow_mining.workflow_metrics` m
  JOIN `workflow_mining.discovered_workflows` w
    ON m.workflow_id = w.workflow_id
  WHERE m.run_id = @run_id
),

bounds AS (
  SELECT
    MAX(potential_annual_hours_saved) AS max_savings,
    MIN(potential_annual_hours_saved) AS min_savings,
    MAX(tickets_per_month) AS max_freq,
    MIN(tickets_per_month) AS min_freq
  FROM raw_metrics
),

scored_workflows AS (
  SELECT
    r.*,
    -- 1. Savings Factor (0 to 1)
    CASE 
      WHEN b.max_savings > b.min_savings 
      THEN (r.potential_annual_hours_saved - b.min_savings) / (b.max_savings - b.min_savings)
      ELSE 1.0 
    END AS factor_savings,
    -- 2. Recurrence Factor (0 to 1)
    CASE 
      WHEN b.max_freq > b.min_freq 
      THEN (r.tickets_per_month - b.min_freq) / (b.max_freq - b.min_freq)
      ELSE 1.0 
    END AS factor_recurrence,
    -- 3. Confidence Factor (0 to 1)
    COALESCE(r.confidence_score, 0.8) AS factor_confidence,
    -- 4. Ease of Automation Factor (1 - complexity score)
    (1.0 - COALESCE(r.complexity_score, 0.5)) AS factor_simplicity
  FROM raw_metrics r
  CROSS JOIN bounds b
),

calculated_ranks AS (
  SELECT
    s.*,
    ROUND(
      (
        (s.factor_savings * 40.0) +
        (s.factor_recurrence * 25.0) +
        (s.factor_confidence * 20.0) +
        (s.factor_simplicity * 15.0)
      ), 
      2
    ) AS calculated_priority_score,
    ROW_NUMBER() OVER(
      ORDER BY 
        (
          (s.factor_savings * 40.0) +
          (s.factor_recurrence * 25.0) +
          (s.factor_confidence * 20.0) +
          (s.factor_simplicity * 15.0)
        ) DESC
    ) AS calculated_rank
  FROM scored_workflows s
)

UPDATE `workflow_mining.workflow_metrics` target
SET
  priority_rank = cr.calculated_rank,
  priority_score = cr.calculated_priority_score,
  ranking_factors_json = TO_JSON_STRING(STRUCT(
    cr.factor_savings AS savings_factor_weight_40pct,
    cr.factor_recurrence AS recurrence_factor_weight_25pct,
    cr.factor_confidence AS confidence_factor_weight_20pct,
    cr.factor_simplicity AS simplicity_factor_weight_15pct,
    cr.calculated_priority_score AS composite_priority_score
  )),
  calculation_assumptions_json = TO_JSON_STRING(STRUCT(
    CONCAT('Hourly rate: $', CAST(cr.hourly_labor_rate AS STRING), '/hr') AS labor_rate_assumption,
    CONCAT('Automatable ratio: ', CAST(ROUND(cr.automatable_percentage * 100, 0) AS STRING), '%') AS automatable_ratio,
    'Active labor estimation: bounded work ratio excluding calendar queue idle time' AS labor_time_basis,
    'Weighted multi-criteria ranking model prioritizing ROI and implementation feasibility' AS ranking_basis
  ))
FROM calculated_ranks cr
WHERE target.metric_id = cr.metric_id;
