"""Canonical institution identity for team strings."""

from __future__ import annotations

import re
from typing import Literal, TypedDict

Classification = Literal["institution_slug", "non_member", "artifact"]


class Resolution(TypedDict):
    classification: Classification
    institution_slug: str | None
    adjudicated: bool
    note: str | None


class Adjudication(TypedDict):
    classification: Classification
    institution_slug: str | None
    note: str


REGISTRY = {
    "east-central": {
        "name": "East Central",
        "abbreviations": ["ECU"],
    },
    "fort-hays-state": {
        "name": "Fort Hays State",
        "abbreviations": ["FHSU"],
    },
    "harding": {
        "name": "Harding",
        "abbreviations": ["HU", "HUW"],
    },
    "newman": {
        "name": "Newman",
        "abbreviations": ["NU"],
    },
    "northeastern-state": {
        "name": "Northeastern State",
        "abbreviations": ["NSU"],
    },
    "northwestern-oklahoma-state": {
        "name": "Northwestern Oklahoma State",
        "abbreviations": ["NWOSU"],
    },
    "oklahoma-baptist": {
        "name": "Oklahoma Baptist",
        "abbreviations": ["OKBU"],
    },
    "ouachita-baptist": {
        "name": "Ouachita Baptist",
        "abbreviations": ["OBU", "OBUW"],
    },
    "rogers-state": {
        "name": "Rogers State",
        "abbreviations": ["RSU"],
    },
    "southern-nazarene": {
        "name": "Southern Nazarene",
        "abbreviations": ["SNU", "SNUW"],
    },
    "southwestern-oklahoma-state": {
        "name": "Southwestern Oklahoma State",
        "abbreviations": ["SWOSU"],
    },
}

# This is programme-presence metadata, not conference-membership data.
PROGRAMMES = {
    "east-central:women": {
        "institution_slug": "east-central",
        "gender": "women",
        "school_row": True,
        "enabled": True,
    },
    "fort-hays-state:men": {
        "institution_slug": "fort-hays-state",
        "gender": "men",
        "school_row": True,
        "enabled": True,
    },
    "fort-hays-state:women": {
        "institution_slug": "fort-hays-state",
        "gender": "women",
        "school_row": False,
        "enabled": None,
    },
    "harding:men": {
        "institution_slug": "harding",
        "gender": "men",
        "school_row": True,
        "enabled": True,
    },
    "harding:women": {
        "institution_slug": "harding",
        "gender": "women",
        "school_row": True,
        "enabled": True,
    },
    "newman:men": {
        "institution_slug": "newman",
        "gender": "men",
        "school_row": True,
        "enabled": True,
    },
    "newman:women": {
        "institution_slug": "newman",
        "gender": "women",
        "school_row": False,
        "enabled": None,
    },
    "northeastern-state:men": {
        "institution_slug": "northeastern-state",
        "gender": "men",
        "school_row": True,
        "enabled": False,
    },
    "northeastern-state:women": {
        "institution_slug": "northeastern-state",
        "gender": "women",
        "school_row": False,
        "enabled": None,
    },
    "northwestern-oklahoma-state:women": {
        "institution_slug": "northwestern-oklahoma-state",
        "gender": "women",
        "school_row": True,
        "enabled": True,
    },
    "oklahoma-baptist:men": {
        "institution_slug": "oklahoma-baptist",
        "gender": "men",
        "school_row": False,
        "enabled": None,
    },
    "oklahoma-baptist:women": {
        "institution_slug": "oklahoma-baptist",
        "gender": "women",
        "school_row": True,
        "enabled": True,
    },
    "ouachita-baptist:men": {
        "institution_slug": "ouachita-baptist",
        "gender": "men",
        "school_row": True,
        "enabled": True,
    },
    "ouachita-baptist:women": {
        "institution_slug": "ouachita-baptist",
        "gender": "women",
        "school_row": True,
        "enabled": True,
    },
    "rogers-state:men": {
        "institution_slug": "rogers-state",
        "gender": "men",
        "school_row": True,
        "enabled": True,
    },
    "rogers-state:women": {
        "institution_slug": "rogers-state",
        "gender": "women",
        "school_row": False,
        "enabled": None,
    },
    "southern-nazarene:men": {
        "institution_slug": "southern-nazarene",
        "gender": "men",
        "school_row": True,
        "enabled": True,
    },
    "southern-nazarene:women": {
        "institution_slug": "southern-nazarene",
        "gender": "women",
        "school_row": True,
        "enabled": True,
    },
    "southwestern-oklahoma-state:women": {
        "institution_slug": "southwestern-oklahoma-state",
        "gender": "women",
        "school_row": True,
        "enabled": True,
    },
}

_RANK_PREFIX = re.compile(r"^#\d+\s+")
_WHITESPACE = re.compile(r"\s+")
_TRAILING_SOURCE_CODE = re.compile(r"\s+(?:NU|OK|OKLA\.)$")
_TRAILING_UNIVERSITY = re.compile(r"\s+(?:Un|Univ|University)$", re.IGNORECASE)
_OKLAHOMA_ABBREVIATION = re.compile(r"\bOkla\.?(?=\s|$)", re.IGNORECASE)
_STATE_ABBREVIATION = re.compile(r"\bSt\.?(?=\s|$|\))", re.IGNORECASE)


def normalize(value: str) -> str:
    """Normalize a non-empty source team string for exact alias matching."""
    if not isinstance(value, str):
        raise TypeError("team string must be a string")

    normalized = _WHITESPACE.sub(" ", value.strip())
    if not normalized:
        raise ValueError("team string must not be empty")

    normalized = _RANK_PREFIX.sub("", normalized)
    normalized = _TRAILING_SOURCE_CODE.sub("", normalized)
    normalized = _TRAILING_UNIVERSITY.sub("", normalized)
    normalized = _OKLAHOMA_ABBREVIATION.sub("Oklahoma", normalized)
    normalized = _STATE_ABBREVIATION.sub("State", normalized)
    return normalized.casefold()


_RAW_ALIASES = {
    "east-central": {
        "East Central",
        "East Central Univ",
    },
    "fort-hays-state": {
        "Fort Hays St.",
        "Fort Hays State",
    },
    "harding": {
        "Harding",
        "Harding University",
        "HU",
    },
    "newman": {
        "Newman",
        "Newman  NU",
        "NU",
    },
    "northeastern-state": {
        "Northeastern St.",
        "Northeastern State",
    },
    "northwestern-oklahoma-state": {
        "Northwest Oklahoma",
        "Northwestern Okla St",
        "Northwestern Okla.",
        "Northwestern Oklahom",
        "Northwestern Oklahoma",
        "NW Oklahoma St.",
        "NW Oklahoma State",
        "NWOSU",
    },
    "oklahoma-baptist": {
        "OKBU",
        "Okla. Baptist",
        "Okla. Baptist  OKLA.",
        "Oklahoma Baptist",
    },
    "ouachita-baptist": {
        "OUA",
        "OUAM",
        "OUAW",
        "Ouachita",
        "Ouachita Baptist",
        "Ouachita Baptist (Ark.)",
    },
    "rogers-state": {
        "Rogers St.",
        "Rogers State",
    },
    "southern-nazarene": {
        "SNU",
        "Southern Nazarene",
        "Southern Nazarene Un",
        "Southern Nazarene University",
    },
    "southwestern-oklahoma-state": {
        "SW Oklahoma State",
        "SWOSU",
        "Southwestern Okla",
        "Southwestern Okla.",
        "Southwestern OKlahoma",
        "Southwestern Oklahoma State",
        "Southwestern Oklahoma State University",
    },
}

ALIASES = {
    slug: frozenset(normalize(alias) for alias in aliases)
    for slug, aliases in _RAW_ALIASES.items()
}


ADJUDICATIONS: dict[str, Adjudication] = {
    "CBC": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Central Baptist College abbreviation; not a mapped GAC institution.",
    },
    "Central Baptist": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Central Baptist College; not a mapped GAC institution.",
    },
    "Central Baptist (AR)": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Central Baptist College in Arkansas; not a mapped GAC institution.",
    },
    "Dallas Baptist": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Dallas Baptist University; distinct from Oklahoma and Ouachita Baptist.",
    },
    "DBU": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Dallas Baptist University abbreviation; 443 source rows identify a non-member.",
    },
    "ESU": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Emporia State abbreviation; evidence: game_id 12201601.",
    },
    "NC": {
        "classification": "institution_slug",
        "institution_slug": "newman",
        "note": "Truncated Newman team label in eight event rows; evidence: game_id 1201914.",
    },
    "NSU": {
        "classification": "institution_slug",
        "institution_slug": "northeastern-state",
        "note": "Northeastern State abbreviation in northeastern-state-university source data; evidence: game_id 12201704.",
    },
    "NU Cli": {
        "classification": "artifact",
        "institution_slug": None,
        "note": "Malformed context-only team label; evidence: game_id 3202103.",
    },
    "NWOSU18": {
        "classification": "artifact",
        "institution_slug": None,
        "note": "Season-tagged context-only team code; evidence: game_id 8201807.",
    },
    "Northwestern OSU": {
        "classification": "institution_slug",
        "institution_slug": "northwestern-oklahoma-state",
        "note": "Alternate Northwestern Oklahoma State spelling observed in source rows.",
    },
    "OKLA. BA": {
        "classification": "artifact",
        "institution_slug": None,
        "note": "Truncated context-only team label; evidence: game_id 11201812.",
    },
    "OU": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Ozarks (Arkansas), not Oklahoma or Ouachita; evidence: game_id 8202103.",
    },
    "OUAWSOC": {
        "classification": "artifact",
        "institution_slug": None,
        "note": "Source-system team code rather than an institution name; evidence: game_id 8201809.",
    },
    "SOUTHWES": {
        "classification": "institution_slug",
        "institution_slug": "southwestern-oklahoma-state",
        "note": "Truncated SWOSU label in Harding women's data; evidence: game_id 8201817.",
    },
    "SW Christian": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Southwestern Christian University; not Southwestern Oklahoma State.",
    },
    "Southwest Baptist": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Southwest Baptist University; distinct from Oklahoma and Ouachita Baptist.",
    },
    "Southwestern": {
        "classification": "institution_slug",
        "institution_slug": "southwestern-oklahoma-state",
        "note": "All 18 source rows occur in SWOSU context on swosuathletics.com.",
    },
    "Southwestern (KS)": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Southwestern College in Kansas; evidence: game_id 10202403.",
    },
    "Southwestern Christ.": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Southwestern Christian University; not Southwestern Oklahoma State.",
    },
    "Southwestern Christi": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "20-character truncation of Southwestern Christian University.",
    },
    "Southwestern OSU": {
        "classification": "institution_slug",
        "institution_slug": "southwestern-oklahoma-state",
        "note": "Alternate Southwestern Oklahoma State spelling observed in source rows.",
    },
    "UAPBWS17": {
        "classification": "artifact",
        "institution_slug": None,
        "note": "Season-tagged context-only team code; evidence: game_id 8201706.",
    },
    "WBC": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Williams Baptist College abbreviation; not a mapped GAC institution.",
    },
    "Western": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Western Colorado University; evidence: game_id 14202501.",
    },
    "Williams Baptist": {
        "classification": "non_member",
        "institution_slug": None,
        "note": "Williams Baptist University; not a mapped GAC institution.",
    },
}


def _build_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for slug, aliases in ALIASES.items():
        for alias in aliases:
            existing = index.get(alias)
            if existing is not None and existing != slug:
                raise ValueError(f"normalized alias {alias!r} maps to {existing!r} and {slug!r}")
            index[alias] = slug
    return index


_ALIAS_INDEX = _build_alias_index()


def resolve(value: str) -> Resolution:
    """Resolve one raw team string to one exhaustive identity classification."""
    normalized = normalize(value)
    adjudication = ADJUDICATIONS.get(value)
    if adjudication is not None:
        return {
            "classification": adjudication["classification"],
            "institution_slug": adjudication["institution_slug"],
            "adjudicated": True,
            "note": adjudication["note"],
        }

    slug = _ALIAS_INDEX.get(normalized)
    if slug is not None:
        return {
            "classification": "institution_slug",
            "institution_slug": slug,
            "adjudicated": False,
            "note": None,
        }

    return {
        "classification": "non_member",
        "institution_slug": None,
        "adjudicated": False,
        "note": None,
    }
