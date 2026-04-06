-- Official public dataset (BigQuery; counts toward monthly free query quota):
--   bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
--
-- Prefer the Python exporter (queries + pivot): scripts/fetch_ga4_bigquery.py

SELECT
  PARSE_DATE('%Y%m%d', event_date) AS date,
  SUM(IFNULL(ecommerce.purchase_revenue_in_usd, 0)) AS revenue,
  COUNTIF(event_name = 'purchase') AS purchases,
  COUNTIF(event_name = 'session_start') AS sessions
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY 1
ORDER BY 1;
