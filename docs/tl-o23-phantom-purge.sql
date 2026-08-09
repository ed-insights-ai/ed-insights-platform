-- tl-o23 — delete the 42 phantom games and their children.
--
-- The 42 are FHSU 2020 (24) and OBU 2020 (18): rows scraped from /stats/2025/ pages that a
-- preseason URL redirect filed under season_year=2020. Each is an exact duplicate of a real
-- 2025 row (same source_url, date, both team names, both scores) and each carries 0 unique
-- information: the cached HTML is byte-identical to its 2025 twin for FHSU, and identical
-- after stripping one Incapsula cache-buster <script> for OBU.
--
-- WHY THIS IS NEEDED AT ALL, given the parquets were regenerated without them:
-- load_db never deletes. _load_games upserts (ON CONFLICT DO UPDATE) and _load_child_table
-- deletes only rows whose game_id appears in the incoming frame. A row that vanishes from
-- the parquets is simply never touched again, so the purge must be explicit.
--
-- THE ROW SET IS PINNED, NOT DETECTED. The id list below was derived twice, independently
-- (Postgres twin-verification, and the game_id column of the deleted 2020 parquets) and the
-- two agree exactly. The season-year detector is used only as a guard, never as the source
-- of the delete set: `extract(year from date) != season_year` condemns 79 legitimate games,
-- because nine programmes played their COVID season in spring 2021 under season_year=2020.
--
-- Run: psql -U lume -d ed_insights -f docs/tl-o23-phantom-purge.sql

BEGIN;

CREATE TEMP TABLE doomed(game_id int PRIMARY KEY);
INSERT INTO doomed VALUES
  (2202001),
  (2202002),
  (2202003),
  (2202004),
  (2202005),
  (2202006),
  (2202007),
  (2202008),
  (2202009),
  (2202010),
  (2202011),
  (2202012),
  (2202013),
  (2202014),
  (2202015),
  (2202016),
  (2202017),
  (2202018),
  (2202019),
  (2202020),
  (2202021),
  (2202022),
  (2202023),
  (2202024),
  (5202001),
  (5202002),
  (5202003),
  (5202004),
  (5202005),
  (5202006),
  (5202007),
  (5202008),
  (5202009),
  (5202010),
  (5202011),
  (5202012),
  (5202013),
  (5202014),
  (5202015),
  (5202016),
  (5202017),
  (5202018);

-- Guard 1 — the list is exactly the 42 rows it claims to be.
DO $$ DECLARE n int; BEGIN
  SELECT count(*) INTO n FROM doomed;
  IF n <> 42 THEN RAISE EXCEPTION 'expected 42 doomed ids, got %', n; END IF;
END $$;

-- Guard 2 — every doomed row really is a phantom AND really has a verified 2025 twin.
DO $$ DECLARE n int; BEGIN
  SELECT count(*) INTO n
    FROM games ph JOIN doomed d ON d.game_id = ph.game_id
   WHERE ph.date IS NOT NULL
     AND extract(year from ph.date) NOT IN (ph.season_year, ph.season_year + 1)
     AND EXISTS (SELECT 1 FROM games t
                  WHERE t.season_year = 2025
                    AND t.source_url  = ph.source_url
                    AND t.date        = ph.date
                    AND t.home_team   = ph.home_team
                    AND t.away_team   = ph.away_team
                    AND t.home_score IS NOT DISTINCT FROM ph.home_score
                    AND t.away_score IS NOT DISTINCT FROM ph.away_score
                    AND t.game_id <> ph.game_id);
  IF n <> 42 THEN RAISE EXCEPTION 'only % of 42 doomed rows are twin-verified phantoms', n; END IF;
END $$;

-- Guard 3 — the 79 legitimate spring-2021 COVID games are not in the list.
DO $$ DECLARE n int; BEGIN
  SELECT count(*) INTO n
    FROM games g JOIN doomed d ON d.game_id = g.game_id
   WHERE g.season_year = 2020 AND extract(year from g.date) = 2021;
  IF n <> 0 THEN RAISE EXCEPTION '% doomed rows are legitimate spring-2021 COVID games', n; END IF;
END $$;

DELETE FROM game_events       WHERE game_id IN (SELECT game_id FROM doomed);
DELETE FROM player_game_stats WHERE game_id IN (SELECT game_id FROM doomed);
DELETE FROM team_game_stats   WHERE game_id IN (SELECT game_id FROM doomed);
DELETE FROM games             WHERE game_id IN (SELECT game_id FROM doomed);

COMMIT;
