-- tl-fwn audit: attribution of the two-perspective home-contradiction delta.
--
-- Run read-only:
--   psql -X -v ON_ERROR_STOP=1 -U lume -d ed_insights -f docs/tl-fwn-home-contradiction-attribution.sql
--
-- The 111 IDs below are the rows whose date changed from "Unknown" to an ISO
-- date in commit 860b3cd (PR #42). They are derived from that commit's HU/HUW
-- per-season games.parquet files, not inferred from the live database.
--
-- Measured 2026-08-08:
--   * 523 contradiction groups across all 2,140 dated games.
--   * 471 contradiction groups across the 2,029 games dated before PR #42.
--   * 52 added groups, each with one restored row and one pre-existing row.
--   * 0 removed groups; 471 groups are retained.
--   * 59 of the 111 restored rows are outside the contradiction metric.
-- PR #48 did not modify games artifacts: its data changes are player_stats only.

WITH restored(game_id) AS (
  VALUES
  (1201601),
  (1201602),
  (1201603),
  (1201604),
  (1201605),
  (1201606),
  (1201607),
  (1201608),
  (1201609),
  (1201610),
  (1201611),
  (1201612),
  (1201613),
  (1201614),
  (1201615),
  (1201616),
  (1201617),
  (1201618),
  (1201619),
  (1201620),
  (1201701),
  (1201702),
  (1201703),
  (1201704),
  (1201705),
  (1201706),
  (1201707),
  (1201708),
  (1201709),
  (1201710),
  (1201711),
  (1201712),
  (1201713),
  (1201714),
  (1201715),
  (1201716),
  (1201801),
  (1201802),
  (1201803),
  (1201804),
  (1201805),
  (1201806),
  (1201807),
  (1201808),
  (1201809),
  (1201810),
  (1201811),
  (1201812),
  (1201813),
  (1201814),
  (1201815),
  (1201816),
  (1201817),
  (8201601),
  (8201602),
  (8201603),
  (8201604),
  (8201605),
  (8201606),
  (8201607),
  (8201608),
  (8201609),
  (8201610),
  (8201611),
  (8201612),
  (8201613),
  (8201614),
  (8201615),
  (8201616),
  (8201617),
  (8201618),
  (8201619),
  (8201620),
  (8201701),
  (8201702),
  (8201703),
  (8201704),
  (8201705),
  (8201706),
  (8201707),
  (8201708),
  (8201709),
  (8201710),
  (8201711),
  (8201712),
  (8201713),
  (8201714),
  (8201715),
  (8201716),
  (8201717),
  (8201718),
  (8201719),
  (8201801),
  (8201802),
  (8201803),
  (8201804),
  (8201805),
  (8201806),
  (8201807),
  (8201808),
  (8201809),
  (8201810),
  (8201811),
  (8201812),
  (8201813),
  (8201814),
  (8201815),
  (8201816),
  (8201817),
  (8201915),
  (8201918)
),
base AS (
  SELECT
    g.game_id,
    s.abbreviation,
    s.gender,
    g.date,
    g.home_team,
    g.away_team,
    r.game_id IS NOT NULL AS restored_by_pr42,
    least(g.home_team, g.away_team) AS team_a,
    greatest(g.home_team, g.away_team) AS team_b
  FROM games g
  JOIN schools s ON s.id = g.school_id
  LEFT JOIN restored r ON r.game_id = g.game_id
  WHERE g.date IS NOT NULL
),
current_groups AS (
  SELECT gender, date, team_a, team_b
  FROM base
  GROUP BY 1, 2, 3, 4
  HAVING count(*) > 1 AND count(DISTINCT home_team) > 1
),
pre42_groups AS (
  SELECT gender, date, team_a, team_b
  FROM base
  WHERE NOT restored_by_pr42
  GROUP BY 1, 2, 3, 4
  HAVING count(*) > 1 AND count(DISTINCT home_team) > 1
),
comparison AS (
  SELECT
    coalesce(current_groups.gender, pre42_groups.gender) AS gender,
    coalesce(current_groups.date, pre42_groups.date) AS date,
    coalesce(current_groups.team_a, pre42_groups.team_a) AS team_a,
    coalesce(current_groups.team_b, pre42_groups.team_b) AS team_b,
    CASE
      WHEN current_groups.gender IS NULL THEN 'removed'
      WHEN pre42_groups.gender IS NULL THEN 'added'
      ELSE 'retained'
    END AS status
  FROM current_groups
  FULL OUTER JOIN pre42_groups USING (gender, date, team_a, team_b)
)
SELECT
  status,
  count(*) AS contradiction_groups,
  count(*) FILTER (WHERE status = 'added') AS newly_countable_groups
FROM comparison
GROUP BY status
ORDER BY status;

-- Lists every added or removed group and every perspective in it. An added
-- group must contain a restored Harding row and its already-dated counterpart.
WITH restored(game_id) AS (
  SELECT game_id
  FROM (
    VALUES
      (1201601),(1201602),(1201603),(1201604),(1201605),(1201606),(1201607),
      (1201608),(1201609),(1201610),(1201611),(1201612),(1201613),(1201614),
      (1201615),(1201616),(1201617),(1201618),(1201619),(1201620),(1201701),
      (1201702),(1201703),(1201704),(1201705),(1201706),(1201707),(1201708),
      (1201709),(1201710),(1201711),(1201712),(1201713),(1201714),(1201715),
      (1201716),(1201801),(1201802),(1201803),(1201804),(1201805),(1201806),
      (1201807),(1201808),(1201809),(1201810),(1201811),(1201812),(1201813),
      (1201814),(1201815),(1201816),(1201817),(8201601),(8201602),(8201603),
      (8201604),(8201605),(8201606),(8201607),(8201608),(8201609),(8201610),
      (8201611),(8201612),(8201613),(8201614),(8201615),(8201616),(8201617),
      (8201618),(8201619),(8201620),(8201701),(8201702),(8201703),(8201704),
      (8201705),(8201706),(8201707),(8201708),(8201709),(8201710),(8201711),
      (8201712),(8201713),(8201714),(8201715),(8201716),(8201717),(8201718),
      (8201719),(8201801),(8201802),(8201803),(8201804),(8201805),(8201806),
      (8201807),(8201808),(8201809),(8201810),(8201811),(8201812),(8201813),
      (8201814),(8201815),(8201816),(8201817),(8201915),(8201918)
  ) AS ids(game_id)
),
base AS (
  SELECT
    g.game_id,
    s.abbreviation,
    s.gender,
    g.date,
    g.home_team,
    g.away_team,
    r.game_id IS NOT NULL AS restored_by_pr42,
    least(g.home_team, g.away_team) AS team_a,
    greatest(g.home_team, g.away_team) AS team_b
  FROM games g
  JOIN schools s ON s.id = g.school_id
  LEFT JOIN restored r ON r.game_id = g.game_id
  WHERE g.date IS NOT NULL
),
current_groups AS (
  SELECT gender, date, team_a, team_b
  FROM base
  GROUP BY 1, 2, 3, 4
  HAVING count(*) > 1 AND count(DISTINCT home_team) > 1
),
pre42_groups AS (
  SELECT gender, date, team_a, team_b
  FROM base
  WHERE NOT restored_by_pr42
  GROUP BY 1, 2, 3, 4
  HAVING count(*) > 1 AND count(DISTINCT home_team) > 1
),
changed_groups AS (
  SELECT
    coalesce(current_groups.gender, pre42_groups.gender) AS gender,
    coalesce(current_groups.date, pre42_groups.date) AS date,
    coalesce(current_groups.team_a, pre42_groups.team_a) AS team_a,
    coalesce(current_groups.team_b, pre42_groups.team_b) AS team_b,
    CASE
      WHEN current_groups.gender IS NULL THEN 'removed'
      WHEN pre42_groups.gender IS NULL THEN 'added'
    END AS status
  FROM current_groups
  FULL OUTER JOIN pre42_groups USING (gender, date, team_a, team_b)
  WHERE current_groups.gender IS NULL OR pre42_groups.gender IS NULL
)
SELECT
  changed_groups.status,
  changed_groups.gender,
  changed_groups.date,
  changed_groups.team_a,
  changed_groups.team_b,
  string_agg(
    format(
      '%s:%s:%s/%s:%s',
      base.game_id,
      base.abbreviation,
      base.home_team,
      base.away_team,
      CASE WHEN base.restored_by_pr42 THEN 'restored' ELSE 'preexisting' END
    ),
    '; ' ORDER BY base.restored_by_pr42 DESC, base.game_id
  ) AS perspectives
FROM changed_groups
JOIN base USING (gender, date, team_a, team_b)
GROUP BY 1, 2, 3, 4, 5
ORDER BY 1, 2, 3, 4, 5;
