-- Ed Insights Platform — Fix Seeds and Indexes
-- Migration 003: Fix HUW seed data, rename misleading indexes, add game_id indexes
--
-- Fixes:
--   (1) HUW abbreviation was 'Henderson State University / Reddies' —
--       correct is 'Harding University (Women) / Lady Bisons'
--   (2) idx_*_school_season indexes only had school_id — rename to match
--   (3) Add missing game_id indexes on FK child tables

BEGIN;

-- (1) Fix HUW seed data: should be Harding Women, not Henderson State
UPDATE schools
   SET name    = 'Harding University (Women)',
       mascot  = 'Lady Bisons'
 WHERE abbreviation = 'HUW';

-- If HUW row doesn't exist yet, insert the correct one
INSERT INTO schools (name, abbreviation, conference, mascot)
VALUES ('Harding University (Women)', 'HUW', 'GAC', 'Lady Bisons')
ON CONFLICT (abbreviation) DO NOTHING;

-- (2) Rename misleading indexes: they only index school_id, not season
--     Drop the old names and recreate with accurate names
DROP INDEX IF EXISTS idx_team_game_stats_school_season;
CREATE INDEX IF NOT EXISTS idx_team_game_stats_school
    ON team_game_stats (school_id);

DROP INDEX IF EXISTS idx_player_game_stats_school_season;
CREATE INDEX IF NOT EXISTS idx_player_game_stats_school
    ON player_game_stats (school_id);

DROP INDEX IF EXISTS idx_game_events_school_season;
CREATE INDEX IF NOT EXISTS idx_game_events_school
    ON game_events (school_id);

-- (3) Add game_id indexes for FK lookups on child tables
CREATE INDEX IF NOT EXISTS idx_team_game_stats_game
    ON team_game_stats (game_id);

CREATE INDEX IF NOT EXISTS idx_player_game_stats_game
    ON player_game_stats (game_id);

CREATE INDEX IF NOT EXISTS idx_game_events_game
    ON game_events (game_id);

COMMIT;
