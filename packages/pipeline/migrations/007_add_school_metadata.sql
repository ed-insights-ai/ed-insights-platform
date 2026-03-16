-- Migration 007: Add enabled and gender columns to schools
-- Required for completeness audit queries

BEGIN;

ALTER TABLE schools
    ADD COLUMN IF NOT EXISTS gender  VARCHAR(10) DEFAULT 'men',
    ADD COLUMN IF NOT EXISTS enabled BOOLEAN     DEFAULT true;

COMMENT ON COLUMN schools.gender IS 'men or women — matches schools.toml gender field.';
COMMENT ON COLUMN schools.enabled IS 'Whether this program is actively scraped.';

COMMIT;
