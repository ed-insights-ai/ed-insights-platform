"""Storage layer — save parsed games to per-season and merged Parquet files."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from src.config import load_schools

logger = logging.getLogger(__name__)


def _assign_event_ids(events: pd.DataFrame) -> pd.Series:
    """Build deterministic event IDs that preserve repeated same-clock events."""
    identity_fields = (
        "game_id",
        "event_type",
        "clock",
        "team",
        "player",
        "assist1",
        "assist2",
        "description",
    )
    identity = (
        events.reindex(columns=identity_fields)
        .fillna("")
        .astype(str)
        .apply(lambda column: column.str.lower())
        .agg("|".join, axis=1)
    )
    occurrence = identity.groupby(identity, sort=False, dropna=False).cumcount()
    raw_ids = identity + "|" + occurrence.astype(str)
    return raw_ids.map(lambda raw: hashlib.sha1(raw.encode("utf-8")).hexdigest())


def save_season(parsed_games: list[dict], year: int, school_abbrev: str = "") -> Path:
    """Write ``games.parquet``, ``player_stats.parquet``, ``events.parquet`` for *year*.

    When *school_abbrev* is provided, output is namespaced under
    ``data/structured/{abbrev}/{year}/`` to avoid collisions between schools.

    Returns the output directory path.
    """
    if school_abbrev:
        out = Path("data/structured") / school_abbrev.lower() / str(year)
    else:
        out = Path("data/structured") / str(year)
    out.mkdir(parents=True, exist_ok=True)

    games = [asdict(g["game"]) for g in parsed_games]
    player_stats = [asdict(p) for g in parsed_games for p in g["player_stats"]]
    events = [asdict(e) for g in parsed_games for e in g["events"]]
    team_stats = [asdict(t) for g in parsed_games for t in g["team_stats"]]

    games_df = pd.DataFrame(games)
    player_df = pd.DataFrame(player_stats)
    events_df = pd.DataFrame(events)
    team_df = pd.DataFrame(team_stats)

    if not events_df.empty:
        events_df["event_id"] = _assign_event_ids(events_df)

    games_df.to_parquet(out / "games.parquet", index=False)
    player_df.to_parquet(out / "player_stats.parquet", index=False)
    events_df.to_parquet(out / "events.parquet", index=False)
    team_df.to_parquet(out / "team_stats.parquet", index=False)

    logger.info(
        "Saved season %d: %d games, %d players, %d events, %d team_stats",
        year,
        len(games_df),
        len(player_df),
        len(events_df),
        len(team_df),
    )
    return out


def merge_all_seasons(years: list[int] | None = None, school_abbrev: str = "") -> Path:
    """Read all on-disk season parquets, concatenate, and write merged files.

    When *school_abbrev* is provided, reads from ``data/structured/{abbrev}/{year}/``
    and writes to ``data/structured/{abbrev}/all/``.

    The *years* parameter is deprecated and ignored. Every numeric season
    directory on disk is included so updating one season cannot truncate the
    merged archive.
    """
    if school_abbrev:
        base = Path("data/structured") / school_abbrev.lower()
        out = base / "all"
    else:
        base = Path("data/structured")
        out = base / "all"
    out.mkdir(parents=True, exist_ok=True)

    season_dirs = sorted(
        directory
        for directory in base.iterdir()
        if directory.is_dir() and directory.name != "all" and directory.name.isdigit()
    )

    for kind in ("games", "player_stats", "events", "team_stats"):
        frames: list[pd.DataFrame] = []
        for season_dir in season_dirs:
            path = season_dir / f"{kind}.parquet"
            if path.exists():
                frames.append(pd.read_parquet(path))
        if frames:
            merged = pd.concat(frames, ignore_index=True)
            if kind == "events":
                merged["event_id"] = _assign_event_ids(merged)
                merged = merged.drop_duplicates(subset=["event_id"])
            merged.to_parquet(out / f"{kind}.parquet", index=False)
            logger.info("Merged %s: %d rows across %d seasons", kind, len(merged), len(frames))

    return out


def merge_all_schools() -> Path:
    """Merge parquets across all schools into ``data/structured/all/``."""
    out = Path("data/structured/all")
    out.mkdir(parents=True, exist_ok=True)

    base = Path("data/structured")
    configured_ordinals = {school.ordinal for school in load_schools()}
    for kind in ("games", "player_stats", "events", "team_stats"):
        frames: list[pd.DataFrame] = []
        # Walk school dirs (skip 'all' dir)
        for school_dir in sorted(base.iterdir()):
            if not school_dir.is_dir() or school_dir.name == "all":
                continue
            school_all = school_dir / "all" / f"{kind}.parquet"
            if school_all.exists():
                frames.append(pd.read_parquet(school_all))
            else:
                # Fallback: gather per-year files
                for year_dir in sorted(school_dir.iterdir()):
                    if year_dir.is_dir() and year_dir.name != "all" and year_dir.name.isdigit():
                        path = year_dir / f"{kind}.parquet"
                        if path.exists():
                            frames.append(pd.read_parquet(path))
        if frames:
            merged = pd.concat(frames, ignore_index=True)
            ordinals = merged["game_id"] // 1_000_000
            merged = merged.loc[ordinals.isin(configured_ordinals)].copy()
            if kind == "events":
                merged["event_id"] = _assign_event_ids(merged)
                merged = merged.drop_duplicates(subset=["event_id"])
            merged.to_parquet(out / f"{kind}.parquet", index=False)
            logger.info("Merged all schools %s: %d rows", kind, len(merged))

    return out
