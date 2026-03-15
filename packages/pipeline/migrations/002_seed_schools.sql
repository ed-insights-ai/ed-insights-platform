-- Ed Insights Platform — Seed Data
-- Migration 002: Seed Harding University and Henderson State (HUW) schools

BEGIN;

INSERT INTO schools (name, abbreviation, conference, mascot)
VALUES
    ('Harding University', 'HU', 'GAC', 'Bisons'),
    ('Henderson State University', 'HUW', 'GAC', 'Reddies')
ON CONFLICT (abbreviation) DO NOTHING;

COMMIT;
