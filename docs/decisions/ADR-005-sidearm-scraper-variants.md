# ADR-005: SideArm CMS Scraper Variant Strategy

**Date:** 2026-03-16
**Status:** Accepted
**Supersedes:** ADR-003 (StatCrew + SideArm scraper strategy)

## Context

After scraping all 28 GAC soccer programs (14 men's + 14 women's), we
discovered that SideArm Sports CMS — used by roughly 26 of the 28 GAC
programs — comes in **three distinct variants** with fundamentally
different scraping characteristics.

### Variant 1: StatCrew (Harding only)
- Static HTML pages hosted at `sidearmstats.com`
- Pattern: `/msoc/stats/{year}/{opponent}/boxscore.htm`
- Fully SSR; simple `requests` + `BeautifulSoup` works perfectly
- Our original scraper was built for this

### Variant 2: SideArm New (Nuxt 3 / Vue — ~50% of schools)
- Modern SPA with server-side-rendered schedule HTML
- Boxscore links appear inline in the initial HTTP response
- Pattern: `/sports/mens-soccer/stats/{year}/{opponent}/boxscore/{id}`
- `requests` + regex on the schedule page captures all boxscore URLs
- **Bonus:** These sites expose a full undocumented JSON API:
  - `GET /api/v2/Sports` → sport list with `scheduleId` per sport
  - `GET /api/v2/Schedule/{scheduleId}` → full season with scores + boxscore URLs
  - `GET /api/v2/Schedule/pasts?initialSportId=N&endSportId=N` → historical seasons
  - Verified on: OBU, SNU, FHSU, NU, NSU, RSU, NWOSU, OKBU, and several women's programs

### Variant 3: SideArm Legacy (KnockoutJS — ~50% of schools)
- Older SPA architecture using KnockoutJS for client-side rendering
- `/sports/mens-soccer/schedule/{year}` redirects → `/sports/mens-soccer/schedule` → `/index.aspx`
- Schedule data loaded via XHR at runtime; not present in initial HTML
- Boxscore links use legacy pattern: `/boxscore.aspx?id={game_id}`
- No `/api/v2/` endpoint — predates the Nuxt 3 migration
- Affected GAC schools: ATU, ECU, HSU, SOSU, SAU, SWOSU, UAM (+ women's equivalents)
- **Unresolved:** XHR endpoint for this variant has not been identified

### Discovery Method
We determined the variant by probing each school's schedule page:
- If `GET /schedule/{year}` returns HTML with `/stats/{year}/.*/boxscore/\d+` links → **New**
- If `GET /api/v2/Sports` returns 200 JSON → **New** (API available)
- If `GET /schedule/{year}` redirects to homepage → **Legacy**
- If base URL is `sidearmstats.com` → **StatCrew**

## Decision

Adopt a **three-tier scraper strategy** with a `scraper` field in `schools.toml`
controlling which tier is used per school:

### Tier 1: `statcrew` scraper
- Used for: Harding M/W
- Implementation: existing `StatCrewParser` + `discovery.py` — no changes needed

### Tier 2: `sidearm` scraper (current, handles New variant)
- Used for: all SideArm New schools where `/schedule/{year}` returns boxscore links
- Implementation: `sidearm_discovery.py` — regex on schedule HTML
- **Preferred enhancement:** Use `/api/v2/Schedule/{id}` when available; this
  returns clean JSON and eliminates the need to scrape HTML at all for discovery.
  Still parse the boxscore HTML pages themselves (they remain static).

### Tier 3: `sidearm_legacy` scraper (not yet implemented)
- Used for: ATU, ECU, HSU, SOSU, SAU, SWOSU, UAM + women's equivalents
- Strategy options (in order of preference):
  1. **Reverse-engineer the KnockoutJS XHR endpoint** — if there's a
     `services/*.ashx` or similar endpoint, use it directly (fast, no browser)
  2. **Playwright headless fallback** — render the page in Chromium, wait for
     KnockoutJS to populate the schedule, scrape the rendered DOM
- Until implemented, these 14 programs have `enabled = false` in config

## Consequences

**Good:**
- Decouples scraper logic per variant — changes to one don't break others
- The `scraper` field in `schools.toml` makes it explicit which strategy each school uses
- API-based discovery (Tier 2 enhancement) reduces discovery from page scraping
  to ~1 JSON call per season — cleaner and more resilient to HTML changes
- StatCrew and SideArm New programs (14 of 28) are fully working
- Clear upgrade path when Tier 3 is implemented: flip `enabled = true` + set `scraper = sidearm_legacy`

**Bad:**
- 14 programs (all Legacy SideArm) remain unscraped until Tier 3 is built
- Three scraper variants add complexity to the pipeline
- Legacy SideArm XHR endpoint is unknown — may require browser tool to intercept
- If SideArm migrates Legacy sites to Nuxt 3, schools may silently change variants

**Accepted tradeoff:** Ship what works now (14 SSR programs + Harding). Build
the legacy scraper as a separate bead once the XHR endpoint is understood.
Using Playwright as a fallback is acceptable but should be a last resort —
it's heavier and more brittle than a direct API/XHR approach.

## Implementation Notes

### `schools.toml` scraper values
```toml
scraper = "statcrew"       # Harding M/W
scraper = "sidearm"        # SideArm New (current regex-based)
scraper = "sidearm_api"    # SideArm New (preferred: use /api/v2/ JSON)
scraper = "sidearm_legacy" # SideArm Legacy KnockoutJS (not yet implemented)
```

### Detecting the variant programmatically
```python
def classify_sidearm_school(base_url: str) -> str:
    # Try API v2 first (cleanest)
    r = requests.get(f"{base_url}/api/v2/Sports", timeout=8)
    if r.status_code == 200:
        return "sidearm_api"

    # Try SSR HTML with new-format boxscore links
    r = requests.get(f"{base_url}/sports/mens-soccer/schedule/2024", timeout=15)
    if r.status_code == 200 and "/stats/" in r.text and "/boxscore/" in r.text:
        return "sidearm"

    # Legacy: redirects to homepage, no inline boxscore links
    return "sidearm_legacy"
```

### Future scale (300+ schools across Div I/II/III)
The three-tier strategy was designed with expansion in mind:
- Add `scraper = "presto"` when PrestoSports schools are added
- The `classify_sidearm_school()` function above automates per-school detection
- Re-classify quarterly — sites migrate from Legacy → New as SideArm pushes upgrades
