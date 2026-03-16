"""School configuration loader — reads config/schools.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "schools.toml"


@dataclass
class SchoolConfig:
    """Configuration for a single school's data source."""

    name: str
    abbreviation: str
    conference: str
    prefix: str
    base_url: str
    years: list[int] = field(default_factory=list)
    enabled: bool = False
    data_status: str = "unverified"
    notes: str = ""
    mascot: str = ""
    ordinal: int = 0
    gender: str = "men"
    scraper: str = "statcrew"

    def build_game_url(self, year: int, game_num: int) -> str:
        """Build a game URL from the template, substituting {year}, {prefix}, {num:02d}."""
        return self.base_url.format(year=year, prefix=self.prefix, num=game_num)


def load_schools(path: str | Path = DEFAULT_CONFIG) -> list[SchoolConfig]:
    """Load school configurations from a TOML file.

    Raises ``FileNotFoundError`` if the file doesn't exist.
    Raises ``ValueError`` if an enabled school has an empty ``base_url``.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    schools: list[SchoolConfig] = []
    for idx, entry in enumerate(data.get("schools", []), start=1):
        school = SchoolConfig(
            name=entry["name"],
            abbreviation=entry["abbreviation"],
            conference=entry.get("conference", ""),
            prefix=entry.get("prefix", ""),
            base_url=entry.get("base_url", ""),
            years=entry.get("years", []),
            enabled=entry.get("enabled", False),
            data_status=entry.get("data_status", "unverified"),
            notes=entry.get("notes", ""),
            mascot=entry.get("mascot", ""),
            ordinal=idx,
            gender=entry.get("gender", "men"),
            scraper=entry.get("scraper", "statcrew"),
        )
        if school.enabled and not school.base_url:
            raise ValueError(
                f"School '{school.name}' ({school.abbreviation}) is enabled "
                f"but has no base_url configured"
            )
        schools.append(school)

    return schools
