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
