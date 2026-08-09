"""Tests for the independent conference-game derivation."""

from __future__ import annotations

import pytest

from scripts.conference_audit import _raise_verdict, _verdict_for
from src.conference import audit_rows, derive, is_gac_member


@pytest.mark.parametrize(
    ("slug", "gender", "season_year", "expected"),
    [
        ("northeastern-state", "men", 2019, True),
        ("northeastern-state", "men", 2018, False),
        ("northeastern-state", "women", 2022, False),
        ("oklahoma-baptist", "men", 2022, False),
        ("oklahoma-baptist", "women", 2022, True),
    ],
)
def test_is_gac_member_respects_gender_and_season(
    slug,
    gender,
    season_year,
    expected,
):
    assert is_gac_member(slug, gender, season_year) is expected


@pytest.mark.parametrize(
    ("home_team", "away_team", "gender", "season_year", "expected"),
    [
        (
            "Southwestern Okla.",
            "Southern Nazarene",
            "women",
            2023,
            True,
        ),
        ("Newman", "CSU Pueblo", "men", 2022, False),
    ],
)
def test_derive_resolves_both_teams(
    home_team,
    away_team,
    gender,
    season_year,
    expected,
):
    assert derive(home_team, away_team, gender, season_year) == (expected, True)


def _correct_row(
    game_id: int,
    gender: str,
    season_year: int,
    home_team: str,
    away_team: str,
) -> dict[str, object]:
    derived, resolved = derive(home_team, away_team, gender, season_year)
    assert resolved is True
    assert derived is not None
    return {
        "game_id": game_id,
        "gender": gender,
        "season_year": season_year,
        "home_team": home_team,
        "away_team": away_team,
        "is_conference_game": derived,
    }


_FALSE_POSITIVE_CASES = [
    ("women", 2022, "Southern Nazarene", "Northeastern State", True),
    ("women", 2022, "Southern Nazarene", "Newman", True),
    ("women", 2022, "Southern Nazarene", "Rogers State", True),
    ("women", 2022, "Southern Nazarene", "Fort Hays State", False),
    ("men", 2022, "Southern Nazarene", "Oklahoma Baptist", True),
    ("men", 2018, "Southern Nazarene", "Fort Hays State", True),
    ("men", 2018, "Southern Nazarene", "Newman", True),
    ("men", 2018, "Southern Nazarene", "Northeastern State", True),
    ("men", 2018, "Southern Nazarene", "Rogers State", True),
]


def test_flipping_each_known_false_positive_alarms():
    rows = [
        _correct_row(index, gender, year, home_team, away_team)
        for index, (gender, year, home_team, away_team, _) in enumerate(
            _FALSE_POSITIVE_CASES,
            start=1,
        )
    ]

    clean = audit_rows(rows)
    assert clean.null_count == 0
    assert clean.unresolved == []
    assert clean.disagreements == []
    assert clean.standing_violations == []
    assert _verdict_for(clean) == "ok"

    for index, (*_, expects_standing_violation) in enumerate(_FALSE_POSITIVE_CASES):
        flipped_rows = [dict(row) for row in rows]
        flipped_rows[index]["is_conference_game"] = True

        result = audit_rows(flipped_rows)

        assert len(result.disagreements) == 1
        assert bool(result.standing_violations) is expects_standing_violation
        assert _verdict_for(result) == "alarm"


def test_null_stored_flag_warns_without_disagreement():
    row = _correct_row(
        1,
        "women",
        2023,
        "Southwestern Okla.",
        "Southern Nazarene",
    )
    row["is_conference_game"] = None

    result = audit_rows([row])

    assert result.null_count == 1
    assert result.disagreements == []
    assert result.unresolved == []
    assert _verdict_for(result) == "warn"


def test_artifact_identity_alarms_as_unresolved():
    result = audit_rows(
        [
            {
                "game_id": 1,
                "gender": "women",
                "season_year": 2023,
                "home_team": "Southern Nazarene",
                "away_team": "NU Cli",
                "is_conference_game": None,
            }
        ]
    )

    assert result.unresolved == [1]
    assert result.disagreements == []
    assert _verdict_for(result) == "alarm"


def test_verdict_escalation_never_downgrades_alarm():
    assert _raise_verdict("alarm", "warn") == "alarm"
