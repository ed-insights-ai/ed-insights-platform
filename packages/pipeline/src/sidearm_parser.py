"""SideArm Sports box score parser — static HTML tables.

Modern SideArm box scores (2020+) typically contain 10 tables:
  0: Score by period (Team | 1 | 2 | Total)
  1: Scoring summary (Time | Team | Description)
  2: Cautions/ejections (Time | Team | Type | Player)
  3: Team statistics (Shots, Saves, Corner Kicks, Fouls by period)
  4: Home player stats (Pos | # | Player | SH | SOG | G | A | MIN)
  5: Home goalie stats
  6: Away player stats
  7: Away goalie stats
  8-9: Play-by-play (not used for structured data)

Older layouts (pre-2020) may omit the cautions table or reorder tables.
Tables are identified by column signatures rather than hardcoded indexes.
"""

from __future__ import annotations

import logging
import re
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup

from src.models import (
    Game,
    GameEvent,
    PlayerGameStats,
    TeamGameStats,
)
from src.parser import safe_int

logger = logging.getLogger(__name__)

# Column signatures for table identification
_PLAYER_COLS = {"Pos", "#", "Player", "SH", "SOG", "G", "A", "MIN"}
_GOALIE_COLS = {"Position", "#", "Goalie", "Minutes", "GA", "Saves"}
_SCORING_COLS = {"Time", "Team", "Description"}


def _classify_tables(tables: list[pd.DataFrame]) -> dict:
    """Identify SideArm tables by column headers instead of hardcoded indexes.

    Returns a dict with keys: score, scoring_summary, cautions, team_stats,
    player_stats (list of 2), goalie_stats (list of 2).
    """
    result: dict = {
        "score": None,
        "scoring_summary": None,
        "cautions": None,
        "team_stats": None,
        "player_stats": [],
        "goalie_stats": [],
    }

    for i, df in enumerate(tables):
        cols = set(str(c) for c in df.columns)

        if cols >= _PLAYER_COLS and len(result["player_stats"]) < 2:
            result["player_stats"].append(df)
        elif cols >= _GOALIE_COLS and len(result["goalie_stats"]) < 2:
            result["goalie_stats"].append(df)
        elif cols >= _SCORING_COLS and result["scoring_summary"] is None:
            result["scoring_summary"] = df
        elif "Statistic" in cols and result["team_stats"] is None:
            result["team_stats"] = df
        elif "Team" in cols and result["score"] is None and i == 0:
            result["score"] = df
        elif (
            result["cautions"] is None
            and df.shape[1] == 4
            and "Type" in cols
        ):
            result["cautions"] = df

    return result


def _normalize_name(name: str) -> str:
    """Convert ``Last, First`` to ``First Last``.  Pass through other formats."""
    if "," in name:
        parts = name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name.strip()


def _strip_jersey_prefix(raw: str) -> str:
    """Remove leading jersey-number prefix like ``3 Lovoy, James`` → ``Lovoy, James``."""
    m = re.match(r"^\d+\s+(.+)$", raw.strip())
    return m.group(1) if m else raw.strip()


def _parse_score_table(df: pd.DataFrame) -> dict:
    """Table 0 — extract team names, abbreviations, and final score."""
    info: dict = {
        "home_team": None,
        "away_team": None,
        "home_abbrev": None,
        "away_abbrev": None,
        "home_score": 0,
        "away_score": 0,
    }
    if df.shape[0] < 2 or df.shape[1] < 3:
        return info

    # The "Team" column contains text like "Winner  Ouachita Baptist  OBU"
    # or just "Harding  HU"
    for idx in range(min(2, df.shape[0])):
        raw = str(df.iloc[idx, 0]).strip()
        total = safe_int(df.iloc[idx, df.shape[1] - 1])

        # Remove "Winner" prefix
        raw = re.sub(r"^Winner\s+", "", raw, flags=re.IGNORECASE).strip()

        # Last token is the abbreviation
        tokens = raw.rsplit(None, 1)
        if len(tokens) == 2:
            full_name, abbrev = tokens
        else:
            full_name = raw
            abbrev = raw

        if idx == 0:
            info["home_team"] = full_name.strip()
            info["home_abbrev"] = abbrev.strip()
            info["home_score"] = total
        else:
            info["away_team"] = full_name.strip()
            info["away_abbrev"] = abbrev.strip()
            info["away_score"] = total

    return info


def _parse_team_stats_table(df: pd.DataFrame) -> dict[str, dict]:
    """Table 3 — team statistics with sub-header rows (Shots, Saves, etc.)."""
    stats: dict[str, dict] = {}
    current_stat: str | None = None

    stat_key_map = {
        "shots": "shots",
        "saves": "saves",
        "corner kicks": "corners",
        "fouls": "fouls",
    }

    for _, row in df.iterrows():
        label = str(row.iloc[0]).strip().lower()

        # Check if this is a stat header row
        matched_key = None
        for keyword, key in stat_key_map.items():
            if label == keyword:
                matched_key = key
                break
        if matched_key:
            current_stat = matched_key
            continue

        # Skip non-data rows
        if current_stat is None:
            continue
        if label in {"", "nan"} or "shots on goal" in label:
            continue

        team_abbrev = str(row.iloc[0]).strip()
        if not team_abbrev or team_abbrev.lower() == "nan":
            continue

        total_raw = str(row.iloc[-1]).strip()
        # Handle "9  (4)" format — total with SOG in parens
        m = re.match(r"(\d+)\s*\((\d+)\)", total_raw)
        if m:
            total_val = int(m.group(1))
            sog_val = int(m.group(2))
        else:
            total_val = safe_int(total_raw)
            sog_val = None

        if team_abbrev not in stats:
            stats[team_abbrev] = {
                "shots": 0,
                "shots_on_goal": 0,
                "corners": 0,
                "saves": 0,
                "fouls": 0,
            }

        stats[team_abbrev][current_stat] = total_val
        if sog_val is not None:
            stats[team_abbrev]["shots_on_goal"] = sog_val

    return stats


def _parse_player_table(
    df: pd.DataFrame,
    team_name: str,
    game_id: int,
    season_year: int,
) -> list[PlayerGameStats]:
    """Parse a SideArm player stats table (tables 4 or 6)."""
    players: list[PlayerGameStats] = []
    is_starter = True

    for _, row in df.iterrows():
        pos_raw = str(row.iloc[0]).strip()
        player_raw = str(row.iloc[2]).strip()

        # Detect section headers
        if pos_raw.lower() in {"starters", "substitutes", "goalkeeping"}:
            if pos_raw.lower() == "substitutes":
                is_starter = False
            continue

        # Skip totals row
        if player_raw.lower() == "totals":
            continue

        jersey = safe_int(row.iloc[1])
        if jersey == 0 and str(row.iloc[1]).strip().lower() in {"", "nan"}:
            continue

        # Strip jersey prefix from player name: "3 Lovoy, James" → "Lovoy, James"
        name_raw = _strip_jersey_prefix(player_raw)
        name = _normalize_name(name_raw)

        position = pos_raw.upper() if pos_raw and pos_raw.lower() != "nan" else "UNK"

        players.append(
            PlayerGameStats(
                game_id=game_id,
                season_year=season_year,
                team=team_name,
                jersey_number=jersey,
                player_name=name,
                position=position,
                is_starter=is_starter,
                minutes=safe_int(row.iloc[7]),
                shots=safe_int(row.iloc[3]),
                shots_on_goal=safe_int(row.iloc[4]),
                goals=safe_int(row.iloc[5]),
                assists=safe_int(row.iloc[6]),
            )
        )

    return players


def _parse_scoring_summary(
    df: pd.DataFrame,
    game_id: int,
    season_year: int,
    abbrev_to_name: dict[str, str],
) -> list[GameEvent]:
    """Table 1 — scoring summary (Time | Team | Description)."""
    events: list[GameEvent] = []

    for _, row in df.iterrows():
        clock = str(row.iloc[0]).strip()
        if not re.match(r"^\d+:\d+$", clock):
            continue

        team_abbrev = str(row.iloc[1]).strip()
        team_name = abbrev_to_name.get(team_abbrev, team_abbrev)
        description = str(row.iloc[2]).strip()

        # Parse scorer from description: "James Lovoy (1)  Assisted By: ..."
        # or "Xavier O'Dwyer (1)  Assisted By: Alexis Murillo  header..."
        scorer = ""
        assist1: str | None = None

        # Extract scorer: everything before "(N)" goal count
        scorer_match = re.match(r"^(.+?)\s*\(\d+\)", description)
        if scorer_match:
            scorer_raw = scorer_match.group(1).strip()
            # Name is already "First Last" in SideArm scoring summary
            scorer = scorer_raw

        # Extract assist
        assist_match = re.search(r"Assisted By:\s*(.+?)(?:\s{2,}|$)", description)
        if assist_match:
            assist1 = assist_match.group(1).strip()

        events.append(
            GameEvent(
                game_id=game_id,
                season_year=season_year,
                event_type="goal",
                clock=clock,
                team=team_name,
                player=scorer,
                assist1=assist1,
                description=description,
            )
        )

    return events


def _parse_cautions_table(
    df: pd.DataFrame,
    game_id: int,
    season_year: int,
    abbrev_to_name: dict[str, str],
) -> list[GameEvent]:
    """Table 2 — cautions/ejections (shifted columns: NaN | Time | Team | Type | Player)."""
    events: list[GameEvent] = []

    for _, row in df.iterrows():
        # The SideArm cautions table has columns [Time, Team, Type, Player]
        # but Time is NaN and the actual time is in column index 1
        # Layout: [NaN, "32:15", "OBU", "#9 Nael Shalabi"]
        # — but pandas sees: Time=NaN, Team="32:15", Type="OBU", Player="#9 Nael..."
        clock = str(row.iloc[1]).strip()
        if not re.match(r"^\d+:\d+$", clock):
            continue

        team_abbrev = str(row.iloc[2]).strip()
        team_name = abbrev_to_name.get(team_abbrev, team_abbrev)

        player_raw = str(row.iloc[3]).strip()
        # Strip jersey prefix: "#9 Nael Shalabi" → "Nael Shalabi"
        player_name = re.sub(r"^#\d+\s+", "", player_raw).strip()

        # All entries in this table are yellow cards unless marked otherwise
        events.append(
            GameEvent(
                game_id=game_id,
                season_year=season_year,
                event_type="yellow_card",
                clock=clock,
                team=team_name,
                player=player_name,
            )
        )

    return events


def _parse_header_metadata(html: str) -> dict:
    """Extract date and venue from page title/headers."""
    metadata: dict = {"date": None, "venue": None, "attendance": None}
    soup = BeautifulSoup(html, "html.parser")

    # Title: "Men's Soccer vs Harding on 10/16/2025 - Box Score - ..."
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        date_match = re.search(r"on\s+(\d{1,2}/\d{1,2}/\d{4})", title_text)
        if date_match:
            metadata["date"] = date_match.group(1)

    # Attendance from page text
    text = soup.get_text(" ", strip=True)
    att_match = re.search(r"Attendance:\s*(\d+)", text)
    if att_match:
        metadata["attendance"] = int(att_match.group(1))

    return metadata


def parse_sidearm_game(
    html: str,
    game_id: int,
    source_url: str,
    season_year: int,
) -> dict:
    """Parse a SideArm box score HTML page into structured data.

    Returns the same dict format as ``parse_game`` from the StatCrew parser:
    ``game``, ``player_stats``, ``team_stats``, ``events``, ``abbrev_map``.
    """
    logger.info("Parsing SideArm game %s (season %d)", game_id, season_year)

    tables = pd.read_html(StringIO(html))
    if len(tables) < 7:
        raise ValueError(f"Expected ≥7 tables in SideArm box score, found {len(tables)}")

    classified = _classify_tables(tables)

    # Score table (always table 0) → team names and final score
    score_info = _parse_score_table(classified["score"] if classified["score"] is not None else tables[0])
    home_team = score_info["home_team"] or "Unknown"
    away_team = score_info["away_team"] or "Unknown"
    home_abbrev = score_info["home_abbrev"] or ""
    away_abbrev = score_info["away_abbrev"] or ""

    # Build abbreviation → full name map
    abbrev_to_name: dict[str, str] = {}
    if home_abbrev:
        abbrev_to_name[home_abbrev] = home_team
    if away_abbrev:
        abbrev_to_name[away_abbrev] = away_team

    # Header metadata (date, venue, attendance)
    metadata = _parse_header_metadata(html)

    # Team stats — identified by 'Statistic' column
    team_stats_raw: dict[str, dict] = {}
    if classified["team_stats"] is not None:
        team_stats_raw = _parse_team_stats_table(classified["team_stats"])

    # Player stats — identified by column signature
    player_stats: list[PlayerGameStats] = []
    if len(classified["player_stats"]) >= 2:
        home_players = _parse_player_table(classified["player_stats"][0], home_team, game_id, season_year)
        away_players = _parse_player_table(classified["player_stats"][1], away_team, game_id, season_year)
        player_stats = home_players + away_players
    elif len(classified["player_stats"]) == 1:
        logger.warning("Only found 1 player stats table for game %s", game_id)
        player_stats = _parse_player_table(classified["player_stats"][0], home_team, game_id, season_year)

    # Scoring summary → goal events
    goal_events: list[GameEvent] = []
    if classified["scoring_summary"] is not None:
        goal_events = _parse_scoring_summary(classified["scoring_summary"], game_id, season_year, abbrev_to_name)

    # Cautions → card events (may be absent in older layouts)
    card_events: list[GameEvent] = []
    if classified["cautions"] is not None:
        card_events = _parse_cautions_table(classified["cautions"], game_id, season_year, abbrev_to_name)

    events = goal_events + card_events

    def _clock_to_seconds(clock: str) -> int:
        try:
            parts = clock.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            return 0

    events.sort(key=lambda e: _clock_to_seconds(e.clock))

    # Build Game object
    game = Game(
        game_id=game_id,
        season_year=season_year,
        source_url=source_url,
        date=metadata["date"] or "Unknown",
        venue=metadata.get("venue"),
        attendance=metadata.get("attendance"),
        home_team=home_team,
        away_team=away_team,
        home_score=score_info["home_score"],
        away_score=score_info["away_score"],
    )

    # Build TeamGameStats from table 3 data
    team_stats_list: list[TeamGameStats] = []
    for abbrev, full_name, is_home in [
        (home_abbrev, home_team, True),
        (away_abbrev, away_team, False),
    ]:
        raw = team_stats_raw.get(abbrev, {})
        team_stats_list.append(
            TeamGameStats(
                game_id=game_id,
                season_year=season_year,
                team=full_name,
                is_home=is_home,
                shots=raw.get("shots", 0),
                shots_on_goal=raw.get("shots_on_goal", 0),
                goals=score_info["home_score"] if is_home else score_info["away_score"],
                corners=raw.get("corners", 0),
                saves=raw.get("saves", 0),
            )
        )

    return {
        "game": game,
        "player_stats": player_stats,
        "team_stats": team_stats_list,
        "events": events,
        "abbrev_map": abbrev_to_name,
    }
