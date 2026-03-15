"""Parsing layer — tables first, play-by-play second, regex last.

Ported from reference/100_soccer_stats_sample.py with multi-season support
(season_year parameter added to all functions that produce dataclass instances).
"""

from __future__ import annotations

import json
import logging
import re
import traceback
from datetime import datetime
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from src.models import Game, GameEvent, PlayerGameStats, TeamGameStats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def safe_int(val: object, default: int = 0) -> int:
    """Convert a value to int, returning *default* on failure."""
    try:
        if pd.isna(val):  # type: ignore[arg-type]
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Table detection helpers
# ---------------------------------------------------------------------------


def has_jersey_number_column(df: pd.DataFrame) -> bool:
    """True if *df* has a column where >= 70 % of values look like jersey numbers."""
    for col in df.columns:
        try:
            col_data = df[col].dropna().astype(str)
            if len(col_data) < 3:
                continue
            digit_count = sum(1 for v in col_data if v.strip().isdigit() and len(v.strip()) <= 2)
            if digit_count / len(col_data) >= 0.70:
                return True
        except (ValueError, TypeError):
            continue
    return False


def find_jersey_col(df: pd.DataFrame) -> str | None:
    """Return the column name most likely to contain jersey numbers."""
    best_col: str | None = None
    best_ratio = 0.0
    for col in df.columns:
        try:
            col_data = df[col].dropna().astype(str).str.strip()
            if len(col_data) < 3:
                continue
            ratio = (col_data.str.isdigit() & (col_data.str.len() <= 2)).mean()
            if ratio > best_ratio:
                best_ratio = ratio
                best_col = col
        except (ValueError, TypeError):
            continue
    return best_col if best_ratio >= 0.70 else None


def identify_table_type(df: pd.DataFrame) -> str:
    """Classify a table by column heuristics (player_stats, scoring_summary, etc.)."""
    cols = {str(c).lower().strip() for c in df.columns}
    if len(df) > 0:
        first_row_vals = {str(v).lower().strip() for v in df.iloc[0].values}
        cols = cols | first_row_vals

    # Goalie stats (check first to avoid player_stats false-positive)
    if len({"goalie", "minutes", "ga", "saves"} & cols) >= 3:
        return "goalie_stats"

    # Player stats
    has_player = "player" in cols
    has_stats = len({"sh", "sog", "g", "a"} & cols) >= 2
    if has_player and has_stats and has_jersey_number_column(df):
        return "player_stats"

    # Scoring summary
    has_time_hint = any("time" in c for c in cols)
    has_team_hint = any(c == "team" or "team" in c for c in cols)
    has_scorer_hint = any("scorer" in c for c in cols)
    has_goal_hint = any(c in {"goal", "goals"} or "goal" in c for c in cols)
    has_assist_hint = any("assist" in c for c in cols)
    if has_time_hint and (has_scorer_hint or has_goal_hint) and (has_assist_hint or has_team_hint):
        time_col_name = None
        for c in df.columns:
            if str(c).lower().strip() == "time":
                time_col_name = c
                break
        if time_col_name is None and len(df) > 0:
            for i, v in enumerate(df.iloc[0].values):
                if str(v).lower().strip() == "time":
                    time_col_name = df.columns[i]
                    break
        if time_col_name is not None:
            time_vals = df[time_col_name].dropna()
            has_time_format = (
                sum(bool(re.match(r"^\d+:\d+$", str(v).strip())) for v in time_vals) >= 2
            )
            if has_time_format:
                return "scoring_summary"

    # Period stats
    if "1" in cols and "2" in cols and "total" in cols:
        return "period_stats"

    return "unknown"


def is_cautions_table(df: pd.DataFrame) -> bool:
    """True if *df* looks like the 5-column cautions/discipline table."""
    if df.shape[1] != 5 or df.shape[0] < 1:
        return False
    for _, row in df.iterrows():
        cell = str(row.iloc[3]).lower()
        if "yellow card" in cell or "red card" in cell:
            return True
    return False


# ---------------------------------------------------------------------------
# Header / metadata
# ---------------------------------------------------------------------------


def parse_game_header(html: str) -> dict:
    """Extract game metadata (teams, date, venue, attendance) from the page header."""
    metadata: dict[str, object] = {
        "home_team": None,
        "away_team": None,
        "date": None,
        "venue": None,
        "attendance": None,
    }
    soup = BeautifulSoup(html, "html.parser")

    # Try <title> first (most reliable)
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        title_match = re.search(r"(.+?)\s+vs\.?\s+(.+?)\s+\((\d{2}/\d{2}/\d{2})\)", title_text)
        if title_match:
            metadata["home_team"] = title_match.group(1).strip()
            metadata["away_team"] = title_match.group(2).strip()
            metadata["date"] = title_match.group(3)

    text = soup.get_text(" ", strip=True)

    # Fallback: broader regex on visible text
    if not metadata["home_team"]:
        pat = (
            r"([A-Za-z][A-Za-z\s\.\'&-]+?)\s+vs\.?\s+"
            r"([A-Za-z][A-Za-z\s\.\'&\(\)-]+?)\s+"
            r"\((\d{2}/\d{2}/\d{2})(?:\s+at\s+([^)]+))?\)"
        )
        match = re.search(pat, text)
        if match:
            metadata["home_team"] = match.group(1).strip()
            metadata["away_team"] = match.group(2).strip()
            metadata["date"] = match.group(3)
            if match.group(4):
                metadata["venue"] = match.group(4).strip()

    # Attendance
    att_match = re.search(r"Attendance:\s*(\d+)", text)
    if att_match:
        metadata["attendance"] = int(att_match.group(1))

    # Venue fallback
    if not metadata["venue"]:
        venue_match = re.search(r"\d{2}/\d{2}/\d{2}\s+at\s+([^)]+)\)", text)
        if venue_match:
            metadata["venue"] = venue_match.group(1).strip()

    return metadata


# ---------------------------------------------------------------------------
# Abbreviation mapping
# ---------------------------------------------------------------------------


def build_team_abbrev_map(html: str, team_names: list[str]) -> dict[str, str]:
    """Map team abbreviations (e.g. 'HU', 'CBU') to full team names."""
    abbrev_map: dict[str, str] = {"HU": "Harding"}

    for full_name in team_names:
        if not full_name or full_name == "Harding":
            continue
        clean_name = full_name.replace("(", "").replace(")", "").strip()
        words = clean_name.split()
        initials = "".join(w[0].upper() for w in words if w and w[0].isalpha())
        if len(initials) >= 2:
            abbrev_map[initials] = full_name
            abbrev_map[initials + "U"] = full_name
        if words and len(words[0]) >= 3:
            abbrev_map[words[0][:3].upper()] = full_name
        if words:
            tok = words[0][:3].upper() if len(words[0]) >= 3 else words[0].upper()
            abbrev_map[tok] = full_name

    # Scan HTML for abbreviation usage in context
    try:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        abbrev_context = re.findall(r"\b([A-Z]{2,4})\s+(?:#\d|substitution|shot|corner|foul)", text)
        for abbrev in set(abbrev_context):
            if abbrev not in abbrev_map and abbrev != "TEAM":
                for full_name in team_names:
                    if full_name in abbrev_map.values():
                        continue
                    clean_upper = full_name.replace("(", "").replace(")", "").strip().upper()
                    if clean_upper.startswith(abbrev[:2]) or abbrev in clean_upper:
                        abbrev_map[abbrev] = full_name
                        break
    except (ValueError, TypeError, AttributeError):
        pass

    return abbrev_map


# ---------------------------------------------------------------------------
# Player stats table
# ---------------------------------------------------------------------------


def parse_player_stats_table(
    df: pd.DataFrame,
    team_name: str,
    game_id: int,
    season_year: int,
) -> list[PlayerGameStats]:
    """Parse a player-stats table into a list of :class:`PlayerGameStats`."""
    players: list[PlayerGameStats] = []
    is_starter = True

    # Normalise headers
    if all(isinstance(c, (int, np.integer)) for c in df.columns):
        df.columns = [str(c).lower().strip() for c in df.iloc[0]]
        df = df.iloc[1:].reset_index(drop=True)
    else:
        df.columns = [str(c).lower().strip() for c in df.columns]

    col_map: dict[str, str] = {}
    jersey_col = find_jersey_col(df)
    if jersey_col:
        col_map["number"] = jersey_col
    for col in df.columns:
        if "pos" in col:
            col_map["position"] = col
        elif col_map.get("number") is None and col in {"##", "#", "no", "no."}:
            col_map["number"] = col
        elif "player" in col or "name" in col:
            col_map["name"] = col
        elif col == "sh":
            col_map["shots"] = col
        elif col == "sog":
            col_map["sog"] = col
        elif col in {"g", "goals"}:
            col_map["goals"] = col
        elif col in {"a", "assists"}:
            col_map["assists"] = col
        elif col in {"min", "minutes"}:
            col_map["minutes"] = col

    for _, row in df.iterrows():
        row_text = " ".join(str(v) for v in row.values).lower()
        if "substitutes" in row_text or "subs" in row_text:
            is_starter = False
            continue
        if "total" in row_text or "opponents" in row_text:
            continue
        try:
            number_val = row.get(col_map.get("number", "##"), None)
            if pd.isna(number_val) or not str(number_val).strip().isdigit():
                continue
            jersey = int(number_val)
            name = str(row.get(col_map.get("name", "player"), "")).strip()
            if not name or name == "nan":
                continue
            position = str(row.get(col_map.get("position", "pos"), "")).strip()
            if not position or position == "nan":
                position = "SUB" if not is_starter else "UNK"

            players.append(
                PlayerGameStats(
                    game_id=game_id,
                    season_year=season_year,
                    team=team_name,
                    jersey_number=jersey,
                    player_name=name,
                    position=position,
                    is_starter=is_starter,
                    minutes=safe_int(row.get(col_map.get("minutes", "min"), 0)),
                    shots=safe_int(row.get(col_map.get("shots", "sh"), 0)),
                    shots_on_goal=safe_int(row.get(col_map.get("sog", "sog"), 0)),
                    goals=safe_int(row.get(col_map.get("goals", "g"), 0)),
                    assists=safe_int(row.get(col_map.get("assists", "a"), 0)),
                )
            )
        except (ValueError, TypeError, KeyError, IndexError):
            continue

    return players


# ---------------------------------------------------------------------------
# Scoring summary table
# ---------------------------------------------------------------------------


def parse_scoring_summary_table(
    df: pd.DataFrame,
    game_id: int,
    season_year: int,
    abbrev_map: dict[str, str],
) -> list[GameEvent]:
    """Parse the scoring summary TABLE into goal :class:`GameEvent` objects."""
    goal_events: list[GameEvent] = []

    df_n = df.copy()
    if all(isinstance(c, (int, np.integer)) for c in df_n.columns) and len(df_n) > 0:
        header_candidate = [str(v).strip().lower() for v in df_n.iloc[0].values]
        if any("time" in h or "goal" in h or "scorer" in h for h in header_candidate):
            df_n.columns = header_candidate
            df_n = df_n.iloc[1:].reset_index(drop=True)
    else:
        df_n.columns = [str(c).strip().lower() for c in df_n.columns]

    def _find(columns: list[str], keywords: list[str]) -> str | None:
        for c in columns:
            for kw in keywords:
                if kw in c:
                    return c
        return None

    columns = list(df_n.columns)
    time_col = _find(columns, ["time"])
    team_col = _find(columns, ["team"])
    scorer_col = _find(columns, ["goal scorer", "scorer"])
    if scorer_col is None:
        goalish = _find(columns, ["goal"])
        if goalish:
            sample_vals = df_n[goalish].dropna().head(5).astype(str)
            if any(re.search(r"[A-Za-z]", v) for v in sample_vals):
                scorer_col = goalish
    assists_col = _find(columns, ["assist"])
    desc_col = _find(columns, ["description", "desc"])

    # Fallback: detect time column by mm:ss pattern
    if time_col is None:
        for col in columns:
            if any(re.match(r"\d+:\d+", str(v)) for v in df_n[col].dropna()):
                time_col = col
                break

    for _, row in df_n.iterrows():
        try:
            if not time_col or not scorer_col:
                continue
            clock = str(row.get(time_col, "")).strip()
            team_abbrev = str(row.get(team_col, "")).strip() if team_col else ""
            scorer_raw = str(row.get(scorer_col, "")).strip()
            assists_raw = ""
            if assists_col and pd.notna(row.get(assists_col)):
                assists_raw = str(row.get(assists_col)).strip()
            if assists_raw.lower() == "nan":
                assists_raw = ""
            description = None
            if desc_col and pd.notna(row.get(desc_col)) and str(row.get(desc_col)) != "nan":
                description = str(row.get(desc_col)).strip()

            if not re.match(r"^\d+:\d+$", clock):
                continue
            scorer = re.sub(r"\s*\(\d+\)\s*$", "", scorer_raw).strip()
            if not re.search(r"[A-Za-z]", scorer):
                continue

            team_full = (
                abbrev_map.get(team_abbrev.upper(), team_abbrev) if team_abbrev else team_abbrev
            )

            assist1: str | None = None
            assist2: str | None = None
            if assists_raw and assists_raw != "(unassisted)" and assists_raw != "nan":
                parts = [a.strip() for a in assists_raw.split(";") if a.strip()]
                if len(parts) >= 1:
                    assist1 = parts[0]
                if len(parts) >= 2:
                    assist2 = parts[1]

            goal_events.append(
                GameEvent(
                    game_id=game_id,
                    season_year=season_year,
                    event_type="goal",
                    clock=clock,
                    team=team_full,
                    player=scorer,
                    assist1=assist1,
                    assist2=assist2,
                    description=description,
                )
            )
        except (ValueError, TypeError, KeyError, IndexError):
            continue

    return goal_events


# ---------------------------------------------------------------------------
# Cautions table
# ---------------------------------------------------------------------------


def parse_cautions_table(
    df: pd.DataFrame,
    game_id: int,
    season_year: int,
    abbrev_map: dict[str, str],
) -> list[GameEvent]:
    """Parse the cautions/discipline TABLE into card :class:`GameEvent` objects."""
    card_events: list[GameEvent] = []
    for _, row in df.iterrows():
        try:
            if df.shape[1] < 5:
                continue
            team_abbrev = str(row.iloc[0]).strip()
            player_name = str(row.iloc[2]).strip()
            card_text = str(row.iloc[3]).strip().lower()
            clock = str(row.iloc[4]).strip()
            if not re.match(r"^\d+:\d+$", clock):
                continue
            if "yellow" in card_text:
                event_type = "yellow_card"
            elif "red" in card_text:
                event_type = "red_card"
            else:
                continue
            team_full = abbrev_map.get(team_abbrev.upper(), team_abbrev)
            card_events.append(
                GameEvent(
                    game_id=game_id,
                    season_year=season_year,
                    event_type=event_type,
                    clock=clock,
                    team=team_full,
                    player=player_name,
                )
            )
        except (ValueError, TypeError, KeyError, IndexError):
            continue
    return card_events


# ---------------------------------------------------------------------------
# Period stats tables → team totals
# ---------------------------------------------------------------------------


def parse_period_stats_tables(
    tables: list[pd.DataFrame],
    team_names: list[str],
) -> dict[str, dict]:
    """Parse period-stats tables (goals, shots, corners, saves) into per-team totals."""
    team_totals: dict[str, dict] = {}
    for name in team_names:
        team_totals[name] = {
            "goals": 0,
            "shots": 0,
            "shots_on_goal": None,
            "corners": 0,
            "saves": 0,
        }

    stat_map = {
        "goals by period": "goals",
        "shots by period": "shots",
        "shots on goal by period": "shots_on_goal",
        "shots on goal": "shots_on_goal",
        "sog by period": "shots_on_goal",
        "corner kicks": "corners",
        "saves by period": "saves",
    }

    for df in tables:
        if df.shape[1] < 3 or df.shape[0] < 3:
            continue
        first_val = str(df.iloc[0, 0]).lower().strip()
        for prefix, key in stat_map.items():
            if first_val.startswith(prefix):
                try:
                    total_col = df.shape[1] - 1
                    team1_name = str(df.iloc[1, 0]).strip()
                    team2_name = str(df.iloc[2, 0]).strip()
                    team1_val = int(df.iloc[1, total_col])
                    team2_val = int(df.iloc[2, total_col])
                    if team1_name in team_totals:
                        team_totals[team1_name][key] = team1_val
                    if team2_name in team_totals:
                        team_totals[team2_name][key] = team2_val
                except (ValueError, IndexError):
                    pass
                break

    return team_totals


# ---------------------------------------------------------------------------
# Boxscore dispatcher
# ---------------------------------------------------------------------------


def parse_boxscore_tables(
    html: str,
    game_id: int,
    season_year: int,
    header_metadata: dict | None = None,
) -> dict:
    """Orchestrate parsing of every HTML table on the page."""
    result: dict = {
        "player_stats": [],
        "team_totals": {},
        "score_info": {"team1": None, "team2": None, "team1_score": 0, "team2_score": 0},
        "goal_events": [],
        "card_events": [],
        "abbrev_map": {},
    }

    try:
        tables = pd.read_html(StringIO(html))
        logger.info("Found %d tables in HTML", len(tables))

        # Step 1 — goals-by-period table → team names + score
        team_names: list[str] = []
        for df in tables:
            if df.shape[1] >= 3 and df.shape[0] >= 3:
                first_val = str(df.iloc[0, 0]).lower().strip()
                if "goals by period" in first_val:
                    try:
                        team1 = str(df.iloc[1, 0]).strip()
                        team2 = str(df.iloc[2, 0]).strip()
                        total_col = df.shape[1] - 1
                        team_names = [team1, team2]
                        result["score_info"] = {
                            "team1": team1,
                            "team2": team2,
                            "team1_score": int(df.iloc[1, total_col]),
                            "team2_score": int(df.iloc[2, total_col]),
                        }
                    except (ValueError, IndexError):
                        pass
                    break

        if not team_names and header_metadata:
            if header_metadata.get("home_team"):
                team_names = [
                    header_metadata.get("home_team", "Home"),
                    header_metadata.get("away_team", "Away"),
                ]

        # Step 2 — abbreviation map
        result["abbrev_map"] = build_team_abbrev_map(html, team_names)

        # Step 3 — route each table
        team_index = 0
        for df in tables:
            ttype = identify_table_type(df)
            if ttype == "player_stats":
                tname = (
                    team_names[team_index]
                    if team_index < len(team_names)
                    else f"Team_{team_index + 1}"
                )
                team_index += 1
                result["player_stats"].extend(
                    parse_player_stats_table(df, tname, game_id, season_year)
                )
            elif ttype == "scoring_summary":
                result["goal_events"] = parse_scoring_summary_table(
                    df, game_id, season_year, result["abbrev_map"]
                )
            elif is_cautions_table(df):
                result["card_events"] = parse_cautions_table(
                    df, game_id, season_year, result["abbrev_map"]
                )

        # Step 4 — period stats → team totals
        if team_names:
            result["team_totals"] = parse_period_stats_tables(tables, team_names)
            for tname in team_names:
                team_players = [p for p in result["player_stats"] if p.team == tname]
                if tname in result["team_totals"]:
                    if result["team_totals"][tname].get("shots_on_goal") is None:
                        result["team_totals"][tname]["shots_on_goal"] = (
                            sum(p.shots_on_goal for p in team_players) if team_players else 0
                        )

    except (ValueError, TypeError, KeyError, IndexError):
        logger.exception("pd.read_html failed for game %s", game_id)

    return result


# ---------------------------------------------------------------------------
# Play-by-play
# ---------------------------------------------------------------------------


def parse_play_by_play(
    html: str,
    game_id: int,
    season_year: int,
    team_names: list[str] | None = None,
) -> list[GameEvent]:
    """Parse the play-by-play section for goals, cards, and substitutions."""
    events: list[GameEvent] = []
    team_names = team_names or []
    abbrev_map = build_team_abbrev_map(html, team_names)

    def _map_team(token: str) -> str:
        return abbrev_map.get(token.strip().upper(), token.strip())

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # GOAL patterns
    p1 = (
        r"\[(\d+:\d+)\]\s*GOAL by ([A-Z]{2,6}|[A-Za-z]{3,})\s+"
        r"([\w ]+(?:,\s*[\w ]+)?)\s*\(([^)]+)\)"
        r"(?:,?\s*\(unassisted\)|,\s*Assist by ([A-Za-z ]+?)"
        r"(?:\s+and\s+([A-Za-z ]+?))?(?:,|$))?"
    )
    p2 = (
        r"\[(\d+:\d+)\]\s*GOAL by ([A-Z]{2,6}|[A-Za-z]{3,})\s+"
        r"([\w, ]+?),\s*(?:Assist by ([A-Za-z ]+?)"
        r"(?:\s+and\s+([A-Za-z ]+?))?,\s*)?goal number"
    )

    goals_found: set[str] = set()

    for match in re.finditer(p1, text, re.IGNORECASE):
        clock = match.group(1)
        if clock in goals_found:
            continue
        goals_found.add(clock)
        events.append(
            GameEvent(
                game_id=game_id,
                season_year=season_year,
                event_type="goal",
                clock=clock,
                team=_map_team(match.group(2)),
                player=match.group(3).strip().rstrip(","),
                assist1=match.group(5).strip() if match.group(5) else None,
                assist2=match.group(6).strip() if match.group(6) else None,
                description=match.group(0),
            )
        )

    for match in re.finditer(p2, text, re.IGNORECASE):
        clock = match.group(1)
        if clock in goals_found:
            continue
        goals_found.add(clock)
        events.append(
            GameEvent(
                game_id=game_id,
                season_year=season_year,
                event_type="goal",
                clock=clock,
                team=_map_team(match.group(2)),
                player=match.group(3).strip().rstrip(","),
                assist1=match.group(4).strip() if match.group(4) else None,
                assist2=match.group(5).strip() if match.group(5) else None,
                description=match.group(0),
            )
        )

    # Yellow cards
    for match in re.finditer(r"\[(\d+:\d+)\]\s*Yellow card on ([A-Z]{2,6})\s+(.+?)(?:\.|$)", text):
        events.append(
            GameEvent(
                game_id=game_id,
                season_year=season_year,
                event_type="yellow_card",
                clock=match.group(1),
                team=_map_team(match.group(2)),
                player=match.group(3).strip(),
            )
        )

    # Red cards
    for match in re.finditer(r"\[(\d+:\d+)\]\s*Red card on ([A-Z]{2,6})\s+(.+?)(?:\.|$)", text):
        events.append(
            GameEvent(
                game_id=game_id,
                season_year=season_year,
                event_type="red_card",
                clock=match.group(1),
                team=_map_team(match.group(2)),
                player=match.group(3).strip(),
            )
        )

    # Substitutions
    for match in re.finditer(
        r"\[(\d+:\d+)\]\s*([A-Z]{2,6})\s+substitution:\s*(.+?)\s+for\s+(.+?)(?:\.|$)", text
    ):
        events.append(
            GameEvent(
                game_id=game_id,
                season_year=season_year,
                event_type="substitution",
                clock=match.group(1),
                team=_map_team(match.group(2)),
                player=match.group(3).strip(),
                description=f"Replaced {match.group(4).strip()}",
            )
        )

    def _clock_to_seconds(clock: str) -> int:
        try:
            parts = clock.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            return 0

    events.sort(key=lambda e: _clock_to_seconds(e.clock))
    return events


# ---------------------------------------------------------------------------
# Error logging
# ---------------------------------------------------------------------------


def log_parse_error(
    game_id: int,
    season_year: int,
    error: Exception,
    html: str | None = None,
) -> None:
    """Write a JSON error report to ``data/errors/{year}/game_{NN}.json``."""
    error_dir = Path("data/errors") / str(season_year)
    error_dir.mkdir(parents=True, exist_ok=True)

    error_info: dict = {
        "game_id": game_id,
        "season_year": season_year,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "timestamp": datetime.now().isoformat(),
        "tables": [],
    }

    if html:
        try:
            tables = pd.read_html(StringIO(html))
            error_info["table_count"] = len(tables)
            for i, df in enumerate(tables):
                error_info["tables"].append(
                    {
                        "index": i,
                        "shape": list(df.shape),
                        "columns": [str(c) for c in df.columns],
                        "first_row": [str(v)[:50] for v in df.iloc[0].values]
                        if len(df) > 0
                        else [],
                    }
                )
        except (ValueError, TypeError, IndexError):
            error_info["table_parse_error"] = str(error)

    error_file = error_dir / f"game_{game_id}.json"
    with open(error_file, "w") as f:
        json.dump(error_info, f, indent=2)

    logger.error("Error logged to %s", error_file)


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------


def parse_game(
    html: str,
    game_id: int,
    source_url: str,
    season_year: int,
) -> dict:
    """Parse a complete game HTML page into structured data.

    Returns a dict with keys: ``game``, ``player_stats``, ``team_stats``, ``events``.
    """
    logger.info("Parsing game %s (season %d)", game_id, season_year)

    # 1. Header metadata
    metadata = parse_game_header(html)

    # 2. Box score tables
    box = parse_boxscore_tables(html, game_id, season_year, metadata)
    player_stats = box["player_stats"]
    team_totals = box["team_totals"]
    score_info = box["score_info"]
    goal_events = box["goal_events"]
    card_events = box["card_events"]
    abbrev_map = box["abbrev_map"]

    # 3. Play-by-play
    team_names_pbp = [score_info.get("team1", ""), score_info.get("team2", "")]
    pbp_events = parse_play_by_play(html, game_id, season_year, team_names_pbp)
    pbp_goals = [e for e in pbp_events if e.event_type == "goal"]
    pbp_cards = [e for e in pbp_events if "card" in e.event_type]
    sub_events = [e for e in pbp_events if e.event_type == "substitution"]

    # 4. Merge events — tables first, PBP fallback
    events: list[GameEvent] = []
    events.extend(goal_events if goal_events else pbp_goals)
    events.extend(card_events if card_events else pbp_cards)
    events.extend(sub_events)

    def _clock_to_seconds(clock: str) -> int:
        try:
            parts = clock.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            return 0

    events.sort(key=lambda e: _clock_to_seconds(e.clock))

    # 5. Score
    home_team = score_info.get("team1") or metadata.get("home_team") or "Unknown"
    away_team = score_info.get("team2") or metadata.get("away_team") or "Unknown"
    home_score = score_info.get("team1_score", 0)
    away_score = score_info.get("team2_score", 0)

    game = Game(
        game_id=game_id,
        season_year=season_year,
        source_url=source_url,
        date=metadata["date"] or "Unknown",
        venue=metadata["venue"],
        attendance=metadata["attendance"],
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
    )

    # 6. Build TeamGameStats from team_totals dict
    team_stats_list: list[TeamGameStats] = []
    for tname in [home_team, away_team]:
        totals = team_totals.get(tname, {})
        sog = totals.get("shots_on_goal", 0)
        if sog is None:
            sog = 0
        team_stats_list.append(
            TeamGameStats(
                game_id=game_id,
                season_year=season_year,
                team=tname,
                is_home=(tname == home_team),
                shots=totals.get("shots", 0),
                shots_on_goal=sog,
                goals=totals.get("goals", 0),
                corners=totals.get("corners", 0),
                saves=totals.get("saves", 0),
            )
        )

    return {
        "game": game,
        "player_stats": player_stats,
        "team_stats": team_stats_list,
        "events": events,
        "abbrev_map": abbrev_map,
    }
