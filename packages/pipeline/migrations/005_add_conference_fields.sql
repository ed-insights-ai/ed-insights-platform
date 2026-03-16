BEGIN;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS is_conference_game BOOLEAN DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS home_conference     VARCHAR(100) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS away_conference     VARCHAR(100) DEFAULT NULL;

COMMENT ON COLUMN games.is_conference_game IS
    'True if game counts toward conference standings. From SideArm is_conference flag.';
COMMENT ON COLUMN games.home_conference IS
    'Conference of the scraping school (always known from schools.conference).';
COMMENT ON COLUMN games.away_conference IS
    'Conference of opponent. NULL = unknown. Filled as opponent registry grows.';

COMMIT;
