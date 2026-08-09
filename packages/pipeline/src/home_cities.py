"""Venue-city helpers for deriving a scraping school's home/away side."""

from typing import Literal


HOME_CITY: dict[str, str] = {
    "HU": "Searcy",
    "HUW": "Searcy",
    "FHSU": "Hays",
    "NU": "Wichita",
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

_NOISE_CITIES = {"", "0", "NAN", "NONE", "U", "UNITED STATE", "UNITED STATES"}
_KNOWN_HOME_CITIES = {city.casefold() for city in HOME_CITY.values()}


def venue_city(raw: str | None) -> str | None:
    """Return the city in the first comma-delimited venue segment."""
    if raw is None:
        return None

    city = str(raw).split(",", 1)[0].strip()
    if city.upper().rstrip(".") in _NOISE_CITIES:
        return None
    return city or None


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
    normalized_city = city.casefold()

    if home_city and normalized_city == home_city.casefold():
        return "home", "resolved-by-venue"
    if opponent_city and normalized_city == opponent_city.casefold():
        return "away", "resolved-by-venue"
    if (
        home_city
        and opponent_city
        and normalized_city in _KNOWN_HOME_CITIES
    ):
        return "neutral", "neutral"

    return order_side, "venue-city-unmatched"
