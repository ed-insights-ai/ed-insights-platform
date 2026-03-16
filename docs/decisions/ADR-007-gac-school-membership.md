# ADR-007: GAC Soccer School Membership — Authoritative List

**Date:** 2026-03-16
**Status:** Accepted

## Context

After multiple rounds of confusion (scraping 28 phantom schools, gender
corruption in the DB, duplicate abbreviations), we needed a single authoritative
reference for which schools actually compete in GAC soccer and in which programs.

**Source of truth:** GAC official standings
- Men's: `greatamericanconference.com/standings.aspx?path=msoc`
- Women's: `greatamericanconference.com/standings.aspx?path=wsoc`

Verified 2026-03-16 against 2025 season standings.

## Decision

The GAC runs **separate men's and women's soccer programs with different membership.**

### Men's Soccer — 7 programs (GAC/MIAA shared conference)

| Abbr | School | Mascot | Joined | Scraper |
|------|--------|--------|--------|---------|
| HU | Harding University | Bisons | 2016 | statcrew |
| FHSU | Fort Hays State | Tigers | 2019 | sidearm |
| NU | Newman | Jets | 2019 | sidearm |
| NSU | Northeastern State | RiverHawks | 2019 | sidearm_legacy ⚠️ |
| OBU | Ouachita Baptist | Tigers | 2016 | sidearm |
| RSU | Rogers State | Hillcats | 2019 | sidearm |
| SNU | Southern Nazarene | Crimson Storm | 2016 | sidearm |

Men's conference data starts 2016 for charter members, 2019 for affiliates
(FHSU, NU, NSU, RSU joined as GAC/MIAA affiliates in 2019).

### Women's Soccer — 7 programs (GAC only)

| Abbr | School | Mascot | Joined | Scraper |
|------|--------|--------|--------|---------|
| HUW | Harding University | Lady Bisons | 2016 | statcrew |
| ECU | East Central | Tigers | 2016 | sidearm |
| NWOSU | Northwestern Oklahoma State | Rangers | 2016 | sidearm |
| OKBU | Oklahoma Baptist | Bison | 2016 | sidearm |
| OBUW | Ouachita Baptist | Tigers | 2016 | sidearm |
| SNUW | Southern Nazarene | Crimson Storm | 2016 | sidearm |
| SWOSU | Southwestern Oklahoma State | Bulldogs | 2016 | sidearm |

Women's data goes back to 2016 for all programs.
**No women's affiliates** — all 7 are full GAC members.

## Key Distinctions

- **Men ≠ Women membership.** FHSU, NU, NSU, RSU have men's soccer but NO women's soccer in GAC.
  ECU, NWOSU, OKBU, SWOSU have women's soccer but NO men's soccer in GAC.
  Only HU/HUW, OBU/OBUW, SNU/SNUW appear in both.

- **Total: 14 programs** (7M + 7W). Not 28. Not more.

- **NSU is the only blocked program.** SideArm Legacy platform — confirmed
  via redirect chain. All 13 others are scrapeable today.

## Schools That Do NOT Play GAC Soccer (Common Confusion Sources)

These schools appear in the GAC for other sports or were incorrectly added
to early versions of `schools.toml`:

| School | Why they appear | Soccer status |
|--------|----------------|---------------|
| Arkansas Tech (ATU) | GAC affiliate (men's only, other sports) | No soccer on SideArm |
| Henderson State (HSU) | GAC member | No soccer scraper found |
| Southeastern Oklahoma (SOSU) | GAC member | No soccer in GAC standings |
| Southern Arkansas (SAU) | GAC member | No soccer in GAC standings |
| SW Oklahoma State — men's | GAC member | Women's only, no men's in GAC |
| East Central — men's | GAC member | Women's only, no men's in GAC |
| NW Oklahoma State — men's | GAC member | Women's only, no men's in GAC |
| OK Baptist — men's | GAC member | Women's only, no men's in GAC |

## DB Abbreviation Conventions

Women's programs use the following abbreviations:
- Harding → `HUW`
- East Central → `ECU` (not ECUW)
- Northwestern Oklahoma State → `NWOSU` (not NWOSUW)
- Oklahoma Baptist → `OKBU` (not OKBUW)
- Ouachita Baptist → `OBUW`
- Southern Nazarene → `SNUW`
- Southwestern Oklahoma State → `SWOSU` (not SWOSUW)

The `W` suffix is used only when the same school has BOTH a men's and women's
program (HU/HUW, OBU/OBUW, SNU/SNUW). Schools with only a women's program
use their natural abbreviation without suffix.

## Consequences

- `schools.toml` is the config file. It must match this ADR exactly.
- The DB `schools` table must reflect these 14 programs with correct names,
  genders, abbreviations, and conference values.
- Any future addition of a school requires verifying against GAC standings API
  first — not assumptions about conference membership.
- This ADR is the single source of truth for "what schools do we track."
  When confused, come here first.
