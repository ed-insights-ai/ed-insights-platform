-- Ed Insights Platform — Seed Data
-- Migration 002: Seed Harding University schools

BEGIN;

INSERT INTO schools (name, abbreviation, conference, mascot)
VALUES
    ('Harding University', 'HU', 'GAC', 'Bisons'),
    ('Harding University (Women)', 'HUW', 'GAC', 'Lady Bisons')
ON CONFLICT (abbreviation) DO NOTHING;

COMMIT;
