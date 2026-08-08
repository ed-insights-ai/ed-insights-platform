"""Check stored SideArm roster labels against cached goalie captions."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Literal

import pandas as pd
from bs4 import BeautifulSoup

from src.config import load_schools
from src.sidearm_parser import _classify_tables, _parse_player_table

Bucket = Literal["aligned", "swapped", "ambiguous", "unmatched", "missing_pages"]
PLAYER_KEYS = (
    "game_id",
    "season_year",
    "jersey_number",
    "player_name",
    "position",
    "is_starter",
    "minutes",
    "shots",
    "shots_on_goal",
    "goals",
    "assists",
)


@dataclass
class CaptionCheckResult:
    """Bucket counts for the complete stored SideArm game population."""

    aligned: int = 0
    swapped: int = 0
    ambiguous: int = 0
    unmatched: int = 0
    missing_pages: int = 0

    @property
    def total(self) -> int:
        return self.aligned + self.swapped + self.ambiguous + self.unmatched + self.missing_pages

    def record(self, bucket: Bucket) -> None:
        setattr(self, bucket, getattr(self, bucket) + 1)

    def report(self) -> dict:
        denominator = self.total
        return {
            "check": "sidearm-caption-attribution",
            "total": denominator,
            "buckets": {
                bucket: {
                    "count": getattr(self, bucket),
                    "denominator": denominator,
                }
                for bucket in ("aligned", "swapped", "ambiguous", "unmatched", "missing_pages")
            },
        }


def extract_goalie_captions(html: str) -> tuple[str, ...]:
    """Return SideArm goalie-statistics team captions in page order."""
    soup = BeautifulSoup(html, "html.parser")
    captions: list[str] = []
    for caption in soup.find_all("caption"):
        match = re.fullmatch(
            r"\s*(.+?)\s*-\s*Goalie Statistics\s*",
            caption.get_text(" ", strip=True),
            flags=re.IGNORECASE,
        )
        if match:
            captions.append(match.group(1).strip())
    return tuple(captions)


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _prefix_matches(caption: str, stored_label: str) -> bool:
    normalized_caption = _normalize(caption)
    normalized_label = _normalize(stored_label)
    return normalized_label.startswith(normalized_caption) or normalized_caption.startswith(
        normalized_label
    )


def _classify_orientation(captions: tuple[str, str], labels: tuple[str, str]) -> Bucket:
    aligned = all(_prefix_matches(caption, label) for caption, label in zip(captions, labels))
    swapped = all(
        _prefix_matches(caption, label)
        for caption, label in zip(captions, reversed(labels))
    )
    if aligned and swapped:
        return "ambiguous"
    if aligned:
        return "aligned"
    if swapped:
        return "swapped"
    return "unmatched"


def _parsed_player_key(player: object) -> tuple[str, ...]:
    return tuple(str(getattr(player, key)) for key in PLAYER_KEYS)


def _stored_player_key(row: pd.Series) -> tuple[str, ...]:
    return tuple(str(row[key]) for key in PLAYER_KEYS)


def classify_game_caption_attribution(
    html: str,
    stored_players: pd.DataFrame,
    game_id: int,
    season_year: int,
) -> Bucket:
    """Compare each page-order source roster caption with its stored team label."""
    captions = extract_goalie_captions(html)
    tables = _classify_tables(pd.read_html(StringIO(html)))["player_stats"]
    if len(captions) != 2 or len(tables) != 2 or stored_players.empty:
        return "unmatched"

    labels_by_player: dict[tuple[str, ...], deque[str]] = defaultdict(deque)
    for _, row in stored_players.iterrows():
        labels_by_player[_stored_player_key(row)].append(str(row["team"]))

    roster_labels: list[str] = []
    for table in tables:
        labels: list[str] = []
        for player in _parse_player_table(table, "", game_id, season_year):
            candidates = labels_by_player[_parsed_player_key(player)]
            if not candidates:
                return "unmatched"
            labels.append(candidates.popleft())
        if not labels or len(set(labels)) != 1:
            return "unmatched"
        roster_labels.append(labels[0])

    if any(labels_by_player.values()):
        return "unmatched"
    return _classify_orientation(
        (captions[0], captions[1]),
        (roster_labels[0], roster_labels[1]),
    )


def run_caption_check(
    raw_dir: Path,
    structured_dir: Path,
    config_path: Path,
) -> CaptionCheckResult:
    """Measure caption attribution for every stored game from enabled SideArm schools."""
    schools = [
        school
        for school in load_schools(config_path)
        if school.enabled and school.scraper == "sidearm"
    ]
    if not schools:
        raise RuntimeError(f"No enabled SideArm schools found in {config_path}")

    result = CaptionCheckResult()
    seen_game_ids: set[int] = set()

    for school in schools:
        school_dir = structured_dir / school.abbreviation.lower()
        if not school_dir.is_dir():
            raise FileNotFoundError(f"Structured school directory not found: {school_dir}")
        season_dirs = sorted(
            path for path in school_dir.iterdir() if path.is_dir() and path.name.isdigit()
        )
        if not season_dirs:
            raise RuntimeError(f"No structured seasons found for {school.abbreviation}")

        for season_dir in season_dirs:
            games_path = season_dir / "games.parquet"
            players_path = season_dir / "player_stats.parquet"
            if not games_path.is_file() or not players_path.is_file():
                raise FileNotFoundError(
                    f"Expected games and player_stats parquet in {season_dir}"
                )

            games = pd.read_parquet(games_path)
            players = pd.read_parquet(players_path)
            players_by_game = {
                int(game_id): frame
                for game_id, frame in players.groupby("game_id", sort=False)
            }

            for game in games.itertuples(index=False):
                game_id = int(game.game_id)
                if game_id in seen_game_ids:
                    raise ValueError(f"Duplicate SideArm game_id across parquets: {game_id}")
                seen_game_ids.add(game_id)

                cache_year = (game_id % 1_000_000) // 100
                if game_id // 1_000_000 != school.ordinal or cache_year != int(season_dir.name):
                    raise ValueError(
                        f"Game {game_id} does not match {school.abbreviation}/{season_dir.name}"
                    )

                page_path = (
                    raw_dir
                    / school.abbreviation.lower()
                    / str(cache_year)
                    / f"game_{game_id % 100:02d}.html"
                )
                if not page_path.is_file():
                    result.record("missing_pages")
                    continue

                html = page_path.read_text(encoding="utf-8", errors="replace")
                bucket = classify_game_caption_attribution(
                    html,
                    players_by_game.get(game_id, pd.DataFrame()),
                    game_id,
                    int(game.season_year),
                )
                result.record(bucket)

    if result.total == 0:
        raise RuntimeError("No stored SideArm games were measured")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare SideArm goalie captions with stored player roster labels"
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw_html"))
    parser.add_argument("--structured-dir", type=Path, default=Path("data/structured"))
    parser.add_argument("--config", type=Path, default=Path("config/schools.toml"))
    args = parser.parse_args()

    result = run_caption_check(args.raw_dir, args.structured_dir, args.config)
    print(json.dumps(result.report(), sort_keys=True))
    if result.aligned != result.total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
