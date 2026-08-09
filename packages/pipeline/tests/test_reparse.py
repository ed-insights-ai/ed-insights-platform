"""Tests for the offline cached-HTML reparse entry point."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts import reparse
from src.models import Game


def _write_config(path: Path) -> None:
    path.write_text(
        """
[[schools]]
name = "Harding"
abbreviation = "HU"
ordinal = 1
scraper = "statcrew"

[[schools]]
name = "East Central"
abbreviation = "ECU"
ordinal = 9
scraper = "sidearm"
""".strip(),
        encoding="utf-8",
    )


def _parsed_game(
    game_id: int,
    source_url: str,
    season_year: int,
) -> dict:
    return {
        "game": Game(
            game_id=game_id,
            source_url=source_url,
            season_year=season_year,
            date="01/01/24",
            venue="Test Field",
            attendance=100,
            home_team="Home",
            away_team="Away",
            home_score=1,
            away_score=0,
        ),
        "player_stats": [],
        "events": [],
        "team_stats": [],
    }


def test_parse_archive_path_and_game_id(tmp_path):
    raw_html = tmp_path / "raw_html"
    path = raw_html / "hu" / "2024" / "game_07.html"

    assert reparse._parse_archive_path(path, raw_html) == ("hu", 2024, 7)
    school = reparse.SchoolConfig(
        name="Harding",
        abbreviation="HU",
        conference="GAC",
        prefix="hu",
        base_url="",
        ordinal=1,
    )
    assert reparse._build_game_id(school, 2024, 7) == 1_202_407


@pytest.mark.parametrize(
    "relative_path",
    [
        "hu/not-a-year/game_01.html",
        "hu/2024/not-a-game.html",
        "hu/2024/game_100.html",
    ],
)
def test_parse_archive_path_rejects_invalid_layout(tmp_path, relative_path):
    raw_html = tmp_path / "raw_html"

    with pytest.raises(ValueError, match="Invalid raw HTML path|between 1 and 99"):
        reparse._parse_archive_path(raw_html / relative_path, raw_html)


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("game_id,source_url\n1202401,\n", "Blank source_url"),
        (
            "game_id,source_url\n1202401,https://example.test/1\n"
            "1202401,https://example.test/1\n",
            "Duplicate game_id",
        ),
        ("wrong,columns\n1202401,https://example.test/1\n", "exactly the columns"),
    ],
)
def test_load_source_urls_fails_closed(tmp_path, contents, message):
    manifest = tmp_path / "source_urls.csv"
    manifest.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        reparse._load_source_urls(manifest)


def test_reparse_routes_parsers_preserves_urls_and_writes_merges(
    tmp_path,
    monkeypatch,
):
    raw_html = tmp_path / "raw_html"
    hu_page = raw_html / "hu" / "2024" / "game_01.html"
    ecu_page = raw_html / "ecu" / "2025" / "game_02.html"
    hu_page.parent.mkdir(parents=True)
    ecu_page.parent.mkdir(parents=True)
    hu_page.write_text("statcrew", encoding="utf-8")
    ecu_page.write_text("sidearm", encoding="utf-8")

    config = tmp_path / "schools.toml"
    _write_config(config)
    manifest = tmp_path / "source_urls.csv"
    manifest.write_text(
        "game_id,source_url\n"
        "1202401,https://example.test/statcrew\n"
        "9202502,https://example.test/sidearm\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, int, str]] = []

    def fake_statcrew(html, game_id, source_url, season_year, school_name=""):
        calls.append(("statcrew", game_id, source_url))
        return _parsed_game(game_id, source_url, season_year)

    def fake_sidearm(
        html,
        game_id,
        source_url,
        season_year,
        school_abbrev="",
        school_name="",
    ):
        calls.append(("sidearm", game_id, source_url))
        return _parsed_game(game_id, source_url, season_year)

    monkeypatch.setattr(reparse, "parse_game", fake_statcrew)
    monkeypatch.setattr(reparse, "parse_sidearm_game", fake_sidearm)
    output_root = tmp_path / "output"

    count = reparse.reparse_archive(
        raw_html_dir=raw_html,
        source_urls_path=manifest,
        config_path=config,
        output_root=output_root,
    )

    assert count == 2
    assert calls == [
        ("sidearm", 9_202_502, "https://example.test/sidearm"),
        ("statcrew", 1_202_401, "https://example.test/statcrew"),
    ]
    structured = output_root / "data" / "structured"
    assert len(pd.read_parquet(structured / "hu" / "2024" / "games.parquet")) == 1
    assert len(pd.read_parquet(structured / "ecu" / "2025" / "games.parquet")) == 1
    merged = pd.read_parquet(structured / "all" / "games.parquet")
    assert len(merged) == 2
    assert dict(zip(merged["game_id"], merged["source_url"], strict=True)) == {
        1_202_401: "https://example.test/statcrew",
        9_202_502: "https://example.test/sidearm",
    }
    for kind in reparse.PARQUET_KINDS:
        assert (structured / "all" / f"{kind}.parquet").is_file()
    assert (structured / reparse.COMPLETION_MARKER).read_text() == "games=2\n"


def test_reparse_rejects_missing_source_url_before_writing(tmp_path):
    raw_html = tmp_path / "raw_html"
    page = raw_html / "hu" / "2024" / "game_01.html"
    page.parent.mkdir(parents=True)
    page.write_text("statcrew", encoding="utf-8")
    config = tmp_path / "schools.toml"
    _write_config(config)
    manifest = tmp_path / "source_urls.csv"
    manifest.write_text(
        "game_id,source_url\n9202502,https://example.test/other\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "output"

    with pytest.raises(ValueError, match="No source_url mapping for game_id 1202401"):
        reparse.reparse_archive(
            raw_html_dir=raw_html,
            source_urls_path=manifest,
            config_path=config,
            output_root=output_root,
        )

    assert not (output_root / "data" / "structured").exists()


def test_reparse_reports_parser_failure_before_writing(tmp_path, monkeypatch):
    raw_html = tmp_path / "raw_html"
    page = raw_html / "hu" / "2024" / "game_01.html"
    page.parent.mkdir(parents=True)
    page.write_text("corrupt", encoding="utf-8")
    config = tmp_path / "schools.toml"
    _write_config(config)
    manifest = tmp_path / "source_urls.csv"
    manifest.write_text(
        "game_id,source_url\n1202401,https://example.test/statcrew\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "output"

    def fail_parse(*args, **kwargs):
        raise ValueError("broken page")

    monkeypatch.setattr(reparse, "parse_game", fail_parse)

    with pytest.raises(RuntimeError, match="Failed to parse game_id 1202401"):
        reparse.reparse_archive(
            raw_html_dir=raw_html,
            source_urls_path=manifest,
            config_path=config,
            output_root=output_root,
        )

    assert not (output_root / "data" / "structured").exists()


def test_reparse_preserves_existing_output_when_staged_merge_is_incomplete(
    tmp_path,
    monkeypatch,
):
    raw_html = tmp_path / "raw_html"
    page = raw_html / "hu" / "2024" / "game_01.html"
    page.parent.mkdir(parents=True)
    page.write_text("statcrew", encoding="utf-8")
    config = tmp_path / "schools.toml"
    _write_config(config)
    manifest = tmp_path / "source_urls.csv"
    manifest.write_text(
        "game_id,source_url\n1202401,https://example.test/statcrew\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "output"
    structured = output_root / "data" / "structured"
    structured.mkdir(parents=True)
    prior_output = structured / "prior-output"
    prior_output.write_text("preserved", encoding="utf-8")

    monkeypatch.setattr(
        reparse,
        "parse_game",
        lambda html, game_id, source_url, season_year, school_name="": _parsed_game(
            game_id,
            source_url,
            season_year,
        ),
    )

    def write_partial_merge(*, config, structured_root):
        all_dir = Path(structured_root) / "all"
        all_dir.mkdir(parents=True)
        (all_dir / "games.parquet").write_bytes(b"partial")
        return all_dir

    monkeypatch.setattr(reparse, "merge_all_schools", write_partial_merge)

    with pytest.raises(RuntimeError, match="missing or has empty required outputs"):
        reparse.reparse_archive(
            raw_html_dir=raw_html,
            source_urls_path=manifest,
            config_path=config,
            output_root=output_root,
        )

    assert prior_output.read_text(encoding="utf-8") == "preserved"
    assert not list((output_root / "data").glob(".structured-staging-*"))


def test_publish_staged_output_restores_backup_when_install_fails(
    tmp_path,
    monkeypatch,
):
    structured = tmp_path / "structured"
    structured.mkdir()
    (structured / "version").write_text("prior", encoding="utf-8")
    staging = tmp_path / ".structured-staging-test"
    staging.mkdir()
    (staging / "version").write_text("replacement", encoding="utf-8")
    original_rename = Path.rename

    def fail_install(path, target):
        if path == staging and target == structured:
            raise OSError("install failed")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_install)

    with pytest.raises(OSError, match="install failed"):
        reparse._publish_staged_output(staging, structured)

    assert (structured / "version").read_text(encoding="utf-8") == "prior"
    assert (staging / "version").read_text(encoding="utf-8") == "replacement"
    assert not list(tmp_path.glob(".structured-backup-*"))
