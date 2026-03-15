"""Storage layer — save parsed games to per-season and merged Parquet files."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import asdict
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def _build_event_id(row: pd.Series) -> str:
    """Deterministic SHA-1 event ID for deduplication."""
    parts = [
        str(row.get("game_id", "")),
        str(row.get("event_type", "")),
        str(row.get("clock", "")),
        str(row.get("team", "")),
        str(row.get("player", "")),
        str(row.get("assist1", "") or ""),
        str(row.get("assist2", "") or ""),
    ]
    raw = "|".join(parts).lower()
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def save_season(parsed_games: list[dict], year: int) -> Path:
    """Write ``games.parquet``, ``player_stats.parquet``, ``events.parquet`` for *year*.

    Returns the output directory path.
    """
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
        events_df["event_id"] = events_df.apply(_build_event_id, axis=1)

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


def merge_all_seasons(years: list[int]) -> Path:
    """Read per-season parquets, concatenate, and write to ``data/structured/all/``."""
    out = Path("data/structured/all")
    out.mkdir(parents=True, exist_ok=True)

    for kind in ("games", "player_stats", "events", "team_stats"):
        frames: list[pd.DataFrame] = []
        for year in years:
            path = Path("data/structured") / str(year) / f"{kind}.parquet"
            if path.exists():
                frames.append(pd.read_parquet(path))
        if frames:
            merged = pd.concat(frames, ignore_index=True)
            if kind == "events" and "event_id" in merged.columns:
                merged = merged.drop_duplicates(subset=["event_id"])
            merged.to_parquet(out / f"{kind}.parquet", index=False)
            logger.info("Merged %s: %d rows across %d seasons", kind, len(merged), len(frames))

    return out
