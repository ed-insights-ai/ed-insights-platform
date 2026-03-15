# ADR-003: StatCrew + SideArm Scraper Strategy

**Date:** 2025-02-01
**Status:** Accepted

## Context

We need to collect athletic data from multiple collegiate sources. Two
main providers:

- **StatCrew** — Serves static HTML pages. Harding University uses this.
  We already have a working scraper (BeautifulSoup, no JS needed).
- **SideArm** — Used by many schools including OBU. Unknown whether
  pages are server-rendered HTML or JavaScript-rendered SPAs.

If SideArm content is JS-rendered, we'd need a headless browser
(Playwright/Selenium), which adds significant complexity and cost.

## Decision

1. **StatCrew first** — ship what works. Our BeautifulSoup scraper handles
   static HTML and is already proven.
2. **Research SideArm before building** — investigate whether SideArm pages
   need JS rendering before committing to a scraping approach.
3. **Use the simplest tool that works** — if SideArm serves usable HTML,
   stick with BeautifulSoup. Only bring in Playwright if truly necessary.

## Consequences

**Good:**
- Ship value immediately with the working StatCrew scraper
- Avoid over-engineering (no Playwright until we prove it's needed)
- Research-first prevents building the wrong scraper

**Bad:**
- SideArm support is delayed until research is complete
- If SideArm does require Playwright, we'll need to add browser
  dependencies to the pipeline

**Accepted tradeoff:** Delivering working data from one source now is
better than delayed data from two sources. Research is cheap; rework
is expensive.
