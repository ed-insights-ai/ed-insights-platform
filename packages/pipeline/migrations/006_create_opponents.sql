BEGIN;

CREATE TABLE IF NOT EXISTS opponents (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL UNIQUE,
    abbreviation VARCHAR(20),
    conference   VARCHAR(100),
    division     VARCHAR(10),
    verified_at  TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE opponents IS
    'Reference table of opponent teams. Populated on scrape; conference/division filled over time.';

COMMIT;
