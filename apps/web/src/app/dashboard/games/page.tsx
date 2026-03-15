"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { Loader2, Calendar, MapPin, Trophy } from "lucide-react";
import { SchoolSeasonSelector } from "@/components/SchoolSeasonSelector";
import { getGames } from "@/lib/api";
import type { GameSummary, PaginatedGames } from "@/lib/api";
import { Button } from "@/components/ui/button";

const PAGE_SIZE = 20;

function getResult(
  game: GameSummary,
  schoolName: string
): { label: string; color: string } | null {
  if (game.home_score == null || game.away_score == null) return null;

  const isHome =
    game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
  const schoolScore = isHome ? game.home_score : game.away_score;
  const opponentScore = isHome ? game.away_score : game.home_score;

  if (schoolScore > opponentScore)
    return { label: "W", color: "bg-green-100 text-green-800" };
  if (schoolScore < opponentScore)
    return { label: "L", color: "bg-red-100 text-red-800" };
  return { label: "D", color: "bg-yellow-100 text-yellow-800" };
}

function getOpponent(game: GameSummary, schoolName: string): string {
  const isHome =
    game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
  const opponent = isHome ? game.away_team : game.home_team;
  const prefix = isHome ? "vs" : "@";
  return `${prefix} ${opponent ?? "Unknown"}`;
}

function getScoreDisplay(game: GameSummary): string {
  if (game.home_score == null || game.away_score == null) return "—";
  return `${game.home_score} – ${game.away_score}`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "TBD";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function GamesPage() {
  const [data, setData] = useState<PaginatedGames | null>(null);
  const [allGames, setAllGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [school, setSchool] = useState("");
  const [schoolName, setSchoolName] = useState("");
  const [season, setSeason] = useState(0);
  const [page, setPage] = useState(0);

  const fetchGames = useCallback(
    async (abbr: string, yr: number, pg: number, refreshAll: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const requests: Promise<PaginatedGames>[] = [
          getGames(abbr, yr, PAGE_SIZE, pg * PAGE_SIZE),
        ];
        if (refreshAll) {
          requests.push(getGames(abbr, yr, 100, 0));
        }
        const [pageResult, allResult] = await Promise.all(requests);
        setData(pageResult);
        if (allResult) setAllGames(allResult.items);
      } catch {
        setError("Failed to load games. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleSelectionChange = useCallback(
    (abbr: string, yr: number, name: string) => {
      setSchool(abbr);
      setSchoolName(name);
      setSeason(yr);
      setPage(0);
      fetchGames(abbr, yr, 0, true);
    },
    [fetchGames]
  );

  const handlePageChange = useCallback(
    (newPage: number) => {
      setPage(newPage);
      fetchGames(school, season, newPage, false);
    },
    [school, season, fetchGames]
  );

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  // Compute full season record from all games
  const record = { w: 0, l: 0, d: 0 };
  for (const game of allGames) {
    const r = getResult(game, schoolName);
    if (r?.label === "W") record.w++;
    else if (r?.label === "L") record.l++;
    else if (r?.label === "D") record.d++;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary-900">Games</h2>
        <p className="text-muted-foreground">
          Browse game results by school and season
        </p>
      </div>

      <SchoolSeasonSelector onSelectionChange={handleSelectionChange} />

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading games...</span>
        </div>
      )}

      {!loading && !error && data && (
        <>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-xl border bg-card px-4 py-3">
              <Trophy className="h-5 w-5 text-primary-900" />
              <span className="text-sm font-semibold text-primary-900">
                Season Record:
              </span>
              <span className="text-sm font-bold text-green-700">
                {record.w}W
              </span>
              <span className="text-sm text-muted-foreground">–</span>
              <span className="text-sm font-bold text-red-700">
                {record.l}L
              </span>
              <span className="text-sm text-muted-foreground">–</span>
              <span className="text-sm font-bold text-yellow-700">
                {record.d}D
              </span>
            </div>
            <span className="text-sm text-muted-foreground">
              {data.total} game{data.total !== 1 ? "s" : ""} total
            </span>
          </div>

          {data.items.length === 0 ? (
            <div className="rounded-xl border bg-card p-12 text-center">
              <Calendar className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium text-primary-900">
                No games found
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Try selecting a different school or season.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.items.map((game) => {
                const result = getResult(game, schoolName);
                return (
                  <Link
                    key={game.game_id}
                    href={`/dashboard/games/${game.game_id}`}
                    className="group rounded-xl border bg-card p-4 transition-shadow hover:shadow-md"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Calendar className="h-3.5 w-3.5" />
                        {formatDate(game.date)}
                      </div>
                      {result && (
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold ${result.color}`}
                        >
                          {result.label}
                        </span>
                      )}
                    </div>

                    <p className="mt-2 text-base font-semibold text-primary-900 group-hover:text-primary-700">
                      {getOpponent(game, schoolName)}
                    </p>

                    <p className="mt-1 text-xl font-bold text-primary-900">
                      {getScoreDisplay(game)}
                    </p>

                    {game.venue && (
                      <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <MapPin className="h-3.5 w-3.5" />
                        <span className="truncate">{game.venue}</span>
                      </div>
                    )}
                  </Link>
                );
              })}
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0}
                onClick={() => handlePageChange(page - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page + 1} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages - 1}
                onClick={() => handlePageChange(page + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
