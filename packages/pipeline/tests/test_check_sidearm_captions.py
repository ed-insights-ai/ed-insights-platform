"""Tests for the offline SideArm caption-attribution checker."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from scripts.check_sidearm_captions import (
    _classify_orientation,
    _prefix_matches,
    classify_game_caption_attribution,
    extract_goalie_captions,
    run_caption_check,
)
from src.sidearm_parser import parse_sidearm_game

FIXTURE = Path("tests/fixtures/sidearm_boxscore_6126.html")


def _stored_fixture_players() -> tuple[str, pd.DataFrame]:
    html = FIXTURE.read_text(encoding="utf-8")
    result = parse_sidearm_game(
        html,
        game_id=302501,
        source_url="http://test/6126",
        season_year=2025,
    )
    return html, pd.DataFrame(asdict(player) for player in result["player_stats"])


def test_extracts_goalie_captions_in_page_order():
    html = FIXTURE.read_text(encoding="utf-8")

    assert extract_goalie_captions(html) == ("Ouachita Baptist", "Harding")


def test_prefix_matching_handles_truncated_sidearm_caption():
    assert _prefix_matches("Southwestern Oklahom", "Southwestern Oklahoma State")
    assert not _prefix_matches("Northwestern Oklahoma", "Southwestern Oklahoma State")


def test_classifies_aligned_and_swapped_rosters():
    html, players = _stored_fixture_players()

    assert classify_game_caption_attribution(html, players, 302501, 2025) == "aligned"

    players["team"] = players["team"].map(
        {
            "Ouachita Baptist": "Harding",
            "Harding": "Ouachita Baptist",
        }
    )
    assert classify_game_caption_attribution(html, players, 302501, 2025) == "swapped"


def test_classifies_ambiguous_and_unmatched_labels():
    assert _classify_orientation(("Tigers", "Tigers"), ("Tigers", "Tigers")) == "ambiguous"
    assert _classify_orientation(("Alpha", "Beta"), ("Gamma", "Delta")) == "unmatched"


def test_reports_missing_page_with_denominator(tmp_path):
    config_path = tmp_path / "schools.toml"
    config_path.write_text(
        """
[[schools]]
name = "Example"
abbreviation = "EX"
ordinal = 2
base_url = "https://example.test/soccer"
scraper = "sidearm"
enabled = true
""".strip(),
        encoding="utf-8",
    )
    season_dir = tmp_path / "structured" / "ex" / "2025"
    season_dir.mkdir(parents=True)
    pd.DataFrame([{"game_id": 2202501, "season_year": 2025}]).to_parquet(
        season_dir / "games.parquet",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "game_id": 2202501,
                "season_year": 2025,
                "team": "Example",
            }
        ]
    ).to_parquet(season_dir / "player_stats.parquet", index=False)

    result = run_caption_check(
        tmp_path / "raw_html",
        tmp_path / "structured",
        config_path,
    )

    assert result.missing_pages == 1
    assert result.total == 1
    assert result.report()["buckets"]["missing_pages"] == {
        "count": 1,
        "denominator": 1,
    }
