-- Ed Insights Platform — Initial Schema
-- Migration 001: Create core tables for soccer statistics

BEGIN;

-- Schools
CREATE TABLE IF NOT EXISTS schools (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(20) NOT NULL UNIQUE,
    conference  VARCHAR(100),
    mascot      VARCHAR(100)
);

-- Games
CREATE TABLE IF NOT EXISTS games (
    game_id     INTEGER PRIMARY KEY,
    school_id   INTEGER NOT NULL REFERENCES schools(id),
    season_year INTEGER NOT NULL,
    source_url  TEXT,
    date        DATE,
    venue       VARCHAR(255),
    attendance  INTEGER,
    home_team   VARCHAR(255),
    away_team   VARCHAR(255),
    home_score  INTEGER,
    away_score  INTEGER
);

CREATE INDEX IF NOT EXISTS idx_games_school_season
    ON games (school_id, season_year);

-- Team Game Stats
CREATE TABLE IF NOT EXISTS team_game_stats (
    id              SERIAL PRIMARY KEY,
    game_id         INTEGER NOT NULL REFERENCES games(game_id),
    school_id       INTEGER NOT NULL REFERENCES schools(id),
    team            VARCHAR(255),
    is_home         BOOLEAN,
    shots           INTEGER,
    shots_on_goal   INTEGER,
    goals           INTEGER,
    corners         INTEGER,
    saves           INTEGER
);

CREATE INDEX IF NOT EXISTS idx_team_game_stats_school_season
    ON team_game_stats (school_id);

-- Player Game Stats
CREATE TABLE IF NOT EXISTS player_game_stats (
    id              SERIAL PRIMARY KEY,
    game_id         INTEGER NOT NULL REFERENCES games(game_id),
    school_id       INTEGER NOT NULL REFERENCES schools(id),
    team            VARCHAR(255),
    jersey_number   VARCHAR(10),
    player_name     VARCHAR(255),
    position        VARCHAR(50),
    is_starter      BOOLEAN,
    minutes         INTEGER,
    shots           INTEGER,
    shots_on_goal   INTEGER,
    goals           INTEGER,
    assists         INTEGER
);

CREATE INDEX IF NOT EXISTS idx_player_game_stats_school_season
    ON player_game_stats (school_id);

-- Game Events
CREATE TABLE IF NOT EXISTS game_events (
    id              SERIAL PRIMARY KEY,
    game_id         INTEGER NOT NULL REFERENCES games(game_id),
    school_id       INTEGER NOT NULL REFERENCES schools(id),
    event_type      VARCHAR(50),
    clock           VARCHAR(20),
    team            VARCHAR(255),
    player          VARCHAR(255),
    assist1         VARCHAR(255),
    assist2         VARCHAR(255),
    description     TEXT
);

CREATE INDEX IF NOT EXISTS idx_game_events_school_season
    ON game_events (school_id);

COMMIT;
