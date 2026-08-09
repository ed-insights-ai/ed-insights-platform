"""Venue-city helpers for deriving a scraping school's home/away side."""

import re
from difflib import SequenceMatcher
from typing import Literal


HOME_CITY: dict[str, str] = {
    "HU": "Searcy",
    "HUW": "Searcy",
    "FHSU": "Hays",
    "NU": "Wichita",
    "NSU": "Tahlequah",
    "OBU": "Arkadelphia",
    "OBUW": "Arkadelphia",
    "RSU": "Claremore",
    "SNU": "Bethany",
    "SNUW": "Bethany",
    "ECU": "Ada",
    "NWOSU": "Alva",
    "OKBU": "Shawnee",
    "SWOSU": "Weatherford",
}

_TEAM_HOME_CITY = {
    "harding": "Searcy",
    "oua": "Arkadelphia",
    "fort hays state": "Hays",
    "fort hays st.": "Hays",
    "newman": "Wichita",
    "northeastern state": "Tahlequah",
    "northeastern st.": "Tahlequah",
    "ouachita": "Arkadelphia",
    "ouachita baptist": "Arkadelphia",
    "rogers state": "Claremore",
    "rogers st.": "Claremore",
    "southern nazarene": "Bethany",
    "southern nazarene university": "Bethany",
    "snu": "Bethany",
    "east central": "Ada",
    "northwestern oklahoma state": "Alva",
    "northwestern oklahoma": "Alva",
    "northwest oklahoma": "Alva",
    "northwestern oklahom": "Alva",
    "northwestern okla.": "Alva",
    "oklahoma baptist": "Shawnee",
    "okla. baptist": "Shawnee",
    "okla. baptist okla.": "Shawnee",
    "southwestern oklahoma state": "Weatherford",
    "southwestern oklahoma": "Weatherford",
    "southwestern okla.": "Weatherford",
    "sw oklahoma state": "Weatherford",
}
_NOISE_CITIES = {"", "0", "NAN", "NONE", "U", "UNITED STATE", "UNITED STATES"}
_CITY_ALIASES = {"goddard": "wichita", "maize": "wichita"}
_STATE_SUFFIX = re.compile(
    r"(?:[.,]\s*|\s+)(?:AR|Ark|KS|Kan|OK|Okla)\.?$",
    flags=re.IGNORECASE,
)


def venue_city(raw: str | None) -> str | None:
    """Return the city in the first comma-delimited venue segment."""
    if raw is None:
        return None

    city = str(raw).split(",", 1)[0].strip()
    city = _STATE_SUFFIX.sub("", city).strip()
    if city.upper().rstrip(".") in _NOISE_CITIES:
        return None
    return city or None


def team_home_city(team_abbrev: str = "", team_name: str = "") -> str | None:
    """Resolve a team's curated home city, preferring its unambiguous name."""
    normalized_name = " ".join(team_name.casefold().split())
    if normalized_name in _TEAM_HOME_CITY:
        return _TEAM_HOME_CITY[normalized_name]
    return HOME_CITY.get(team_abbrev.upper())


def _canonical_city(city: str) -> str:
    normalized = city.casefold()
    return _CITY_ALIASES.get(normalized, normalized)


def _looks_like_city_typo(city: str, expected: str) -> bool:
    def letters(value: str) -> str:
        normalized = "".join(character for character in value.casefold() if character.isalpha())
        for suffix in ("highschool", "high"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
        return normalized

    return SequenceMatcher(None, letters(city), letters(expected)).ratio() >= 0.8


def resolve_home_away(
    scraping_home_city: str,
    venue_raw: str | None,
    opponent_home_city: str | None,
    school_is_row0: bool,
    order_says_school_home: bool,
) -> tuple[
    Literal["home", "away", "neutral"],
    Literal[
        "resolved-by-venue",
        "resolved-by-order-fallback",
        "neutral",
        "venue-city-unmatched",
    ],
]:
    """Resolve the scraping school's side and report the evidence used."""
    order_side: Literal["home", "away"] = (
        "home" if school_is_row0 == order_says_school_home else "away"
    )
    city = venue_city(venue_raw)
    if city is None:
        return order_side, "resolved-by-order-fallback"

    home_city = venue_city(scraping_home_city)
    opponent_city = venue_city(opponent_home_city)
    normalized_city = _canonical_city(city)
    normalized_home_city = _canonical_city(home_city) if home_city else None
    normalized_opponent_city = (
        _canonical_city(opponent_city) if opponent_city else None
    )

    if normalized_home_city and normalized_city == normalized_home_city:
        return "home", "resolved-by-venue"
    if normalized_opponent_city and normalized_city == normalized_opponent_city:
        return "away", "resolved-by-venue"
    if home_city and opponent_city is None:
        return order_side, "resolved-by-order-fallback"
    if home_city and opponent_city:
        if _looks_like_city_typo(city, home_city) or _looks_like_city_typo(
            city, opponent_city
        ):
            return order_side, "venue-city-unmatched"
        return "neutral", "neutral"

    return order_side, "venue-city-unmatched"
