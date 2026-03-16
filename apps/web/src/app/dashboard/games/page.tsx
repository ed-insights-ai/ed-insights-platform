"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { SchoolSeasonSelector } from "@/components/SchoolSeasonSelector";
import { useGender } from "@/context/GenderContext";
import { getGames } from "@/lib/api";
import type { GameSummary } from "@/lib/api";

type VenueFilter = "All" | "Home" | "Away";
type ResultFilter = "All" | "W" | "L" | "D";

function getResult(
  game: GameSummary,
  schoolName: string
): "W" | "L" | "D" | null {
  if (game.home_score == null || game.away_score == null) return null;
  const isHome =
    game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
  const schoolScore = isHome ? game.home_score : game.away_score;
  const opponentScore = isHome ? game.away_score : game.home_score;
  if (schoolScore > opponentScore) return "W";
  if (schoolScore < opponentScore) return "L";
  return "D";
}

function isHome(game: GameSummary, schoolName: string): boolean {
  return (
    game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false
  );
}

export default function GamesPage() {
  useGender(); // read from context per spec
  const [school, setSchool] = useState("");
  const [schoolName, setSchoolName] = useState("");
  const [season, setSeason] = useState(2025);
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const [venueFilter, setVenueFilter] = useState<VenueFilter>("All");
  const [resultFilter, setResultFilter] = useState<ResultFilter>("All");

  const fetchGames = useCallback(async (abbr: string, yr: number) => {
    setLoading(true);
    try {
      const res = await getGames(abbr, yr, 100, 0);
      const sorted = [...res.items].sort((a, b) =>
        (a.date ?? "").localeCompare(b.date ?? "")
      );
      setGames(sorted);
    } catch {
      setGames([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelectionChange = useCallback(
    (abbr: string, yr: number, name: string) => {
      setSchool(abbr);
      setSchoolName(name);
      setSeason(yr);
      setVenueFilter("All");
      setResultFilter("All");
      fetchGames(abbr, yr);
    },
    [fetchGames]
  );

  // Summary stats
  const summary = useMemo(() => {
    const s = { w: 0, l: 0, d: 0, hw: 0, hl: 0, hd: 0, aw: 0, al: 0, ad: 0 };
    for (const game of games) {
      const r = getResult(game, schoolName);
      if (!r) continue;
      const home = isHome(game, schoolName);
      if (r === "W") { s.w++; if (home) s.hw++; else s.aw++; }
      else if (r === "L") { s.l++; if (home) s.hl++; else s.al++; }
      else { s.d++; if (home) s.hd++; else s.ad++; }
    }
    return s;
  }, [games, schoolName]);

  // Filtered games
  const filteredGames = useMemo(() => {
    return games.filter((game) => {
      if (venueFilter !== "All") {
        const home = isHome(game, schoolName);
        if (venueFilter === "Home" && !home) return false;
        if (venueFilter === "Away" && home) return false;
      }
      if (resultFilter !== "All") {
        const r = getResult(game, schoolName);
        if (r !== resultFilter) return false;
      }
      return true;
    });
  }, [games, schoolName, venueFilter, resultFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-primary-900">
            Schedule &amp; Results
          </h2>
          <p className="text-muted-foreground text-sm">
            Full season timeline
          </p>
        </div>
        <SchoolSeasonSelector onSelectionChange={handleSelectionChange} />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading schedule...</span>
        </div>
      ) : !school ? (
        <div className="flex items-center justify-center py-16">
          <p className="text-muted-foreground">
            Select a school above to view their schedule.
          </p>
        </div>
      ) : games.length === 0 ? (
        <div className="flex items-center justify-center py-16">
          <p className="text-muted-foreground">
            No games found for this selection.
          </p>
        </div>
      ) : (
        <>
          {/* Summary strip */}
          <div className="bento-card p-4 flex flex-wrap gap-4">
            <SummaryBlock label="Wins" value={String(summary.w)} />
            <SummaryBlock label="Losses" value={String(summary.l)} />
            <SummaryBlock label="Draws" value={String(summary.d)} />
            <SummaryBlock
              label="Home"
              value={`${summary.hw}W-${summary.hl}L-${summary.hd}D`}
            />
            <SummaryBlock
              label="Away"
              value={`${summary.aw}W-${summary.al}L-${summary.ad}D`}
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <FilterGroup
              options={["All", "Home", "Away"] as VenueFilter[]}
              active={venueFilter}
              onChange={setVenueFilter}
            />
            <FilterGroup
              options={["All", "W", "L", "D"] as ResultFilter[]}
              active={resultFilter}
              onChange={setResultFilter}
            />
          </div>

          {/* Timeline table */}
          <div className="bento-card p-5">
            <p className="stat-label mb-4">{season} SEASON</p>
            <div className="divide-y">
              {filteredGames.map((game) => {
                const r = getResult(game, schoolName);
                const home = isHome(game, schoolName);
                const opponent = home ? game.away_team : game.home_team;
                const dateStr = game.date
                  ? new Date(game.date).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })
                  : "TBD";

                return (
                  <Link
                    key={game.game_id}
                    href={`/dashboard/games/${game.game_id}`}
                    className="flex items-center gap-3 py-3 px-2 hover:bg-surface-muted cursor-pointer transition-colors"
                  >
                    {/* Date */}
                    <span className="text-sm text-slate-500 w-28 shrink-0">
                      {dateStr}
                    </span>

                    {/* Result badge */}
                    <span
                      className={`w-8 h-8 rounded-md font-bold text-xs flex items-center justify-center shrink-0 ${
                        r === "W"
                          ? "bg-emerald-500 text-white"
                          : r === "L"
                            ? "bg-rose-500 text-white"
                            : r === "D"
                              ? "bg-amber-500 text-white"
                              : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      {r ?? "–"}
                    </span>

                    {/* H/A badge */}
                    <span
                      className={`text-xs font-semibold px-1.5 py-0.5 rounded shrink-0 ${
                        home
                          ? "bg-data-primary/10 text-data-primary"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {home ? "H" : "A"}
                    </span>

                    {/* Opponent */}
                    <span className="text-sm font-medium text-slate-700 truncate flex-1">
                      {opponent ?? "Unknown"}
                    </span>

                    {/* Score */}
                    <span className="tabular-nums font-bold text-sm text-slate-900 shrink-0">
                      {game.home_score != null && game.away_score != null
                        ? `${game.home_score} – ${game.away_score}`
                        : "—"}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function SummaryBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="bento-card px-4 py-3 min-w-[80px]">
      <p className="stat-label">{label}</p>
      <p className="stat-value text-lg">{value}</p>
    </div>
  );
}

function FilterGroup<T extends string>({
  options,
  active,
  onChange,
}: {
  options: T[];
  active: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex rounded-lg border overflow-hidden">
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`px-3 py-1.5 text-xs font-medium transition-colors ${
            active === opt
              ? "bg-data-primary text-white"
              : "bg-white text-slate-600 hover:bg-surface-muted"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
