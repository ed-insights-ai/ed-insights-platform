-- Migration 008: Preserve evidence-backed neutral-site classification

BEGIN;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS neutral_site BOOLEAN DEFAULT false;

COMMENT ON COLUMN games.neutral_site IS
    'True only when source venue evidence identifies a neutral site.';

COMMIT;
