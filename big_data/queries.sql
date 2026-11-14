-- SQLite gold queries. Databricks: USE CATALOG <catalog>; USE SCHEMA <schema>;
-- 1. Demand by territory
SELECT r.region, SUM(f.count) AS demand FROM fact_indicators f JOIN dim_region r USING(region_id) WHERE source='demand' GROUP BY r.region ORDER BY demand DESC;
-- 2. Services by territory
SELECT r.region, SUM(f.count) AS services FROM fact_indicators f JOIN dim_region r USING(region_id) WHERE source='services' GROUP BY r.region ORDER BY services DESC;
-- 3. Language distribution of demand
SELECT l.language,SUM(f.count) AS demand FROM fact_indicators f JOIN dim_language l USING(language_id) WHERE source='demand' GROUP BY l.language;
-- 4. Demand per service unit (illustrative indicator, not a causal or capacity estimate)
SELECT r.region, SUM(CASE WHEN source='demand' THEN count ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN source='services' THEN count ELSE 0 END),0) AS demand_per_service FROM fact_indicators f JOIN dim_region r USING(region_id) GROUP BY r.region;
-- 5. Provenance and freshness
SELECT source,MIN(snapshot_date) AS oldest_snapshot,MAX(snapshot_date) AS newest_snapshot,SUM(CASE WHEN synthetic THEN 1 ELSE 0 END) AS synthetic_records,COUNT(*) AS records FROM fact_indicators GROUP BY source;
-- Real official sources (requires: python -m big_data.official_integration)
-- 6. Estimated children 0-11 among refugee requests, Brazil 2025 (OBMigra p.16-17)
SELECT t.value AS refugee_requests, c.value AS children_pct, ROUND(t.value*c.value/100.0) AS estimated_children_requests FROM gold_official_context t JOIN gold_official_context c ON c.indicator_id='refugee_requests_children_0_11_pct' WHERE t.indicator_id='refugee_requests_total';
-- 7. Recognition ratio: recognized / requested, Brazil 2025 (different cohorts; indicative only)
SELECT ROUND(r.value*100.0/q.value,1) AS recognized_per_100_requests FROM gold_official_context r JOIN gold_official_context q ON q.indicator_id='refugee_requests_total' WHERE r.indicator_id='refugee_recognized_total';
-- 8. Territorial coverage: IBGE municipalities of SP vs. synthetic regions present in gold
SELECT (SELECT COUNT(*) FROM dim_municipality WHERE state_code='SP') AS ibge_sp_municipalities, (SELECT COUNT(*) FROM dim_region) AS demo_regions;
