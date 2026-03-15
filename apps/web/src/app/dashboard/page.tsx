"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import {
  Loader2,
  Trophy,
  Calendar,
  Users,
  Target,
  Crosshair,
} from "lucide-react";
import { SchoolSeasonSelector } from "@/components/SchoolSeasonSelector";
import { DashboardStats } from "@/components/DashboardStats";
import {
  getGames,
  getTeamStats,
  getPlayerLeaderboard,
} from "@/lib/api";
import type {
  GameSummary,
  TeamStatsAggregation,
  PlayerLeaderboard,
} from "@/lib/api";

interface PerGameData {
  label: string;
  goalsFor: number;
  goalsAgainst: number;
}

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
  return new Date(dateStr).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

export default function DashboardPage() {
  const [school, setSchool] = useState("");
  const [schoolName, setSchoolName] = useState("");
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [teamStats, setTeamStats] = useState<TeamStatsAggregation | null>(null);
  const [recentGames, setRecentGames] = useState<GameSummary[]>([]);
  const [allGames, setAllGames] = useState<GameSummary[]>([]);
  const [topPerformers, setTopPerformers] = useState<PlayerLeaderboard[]>([]);

  // Data for DashboardStats charts
  const [chartTopPlayers, setChartTopPlayers] = useState<
    { player: string; goals: number }[]
  >([]);
  const [chartGamePerformance, setChartGamePerformance] = useState<
    PerGameData[]
  >([]);

  const fetchData = useCallback(async (abbr: string, yr: number, name: string) => {
    setLoading(true);
    setError(null);
    try {
      const [gamesRes, statsRes, playersRes, topPerformersRes] =
        await Promise.all([
          getGames(abbr, yr, 100, 0),
          getTeamStats(abbr, yr),
          getPlayerLeaderboard(abbr, yr, "goals", 5, 0),
          getPlayerLeaderboard(abbr, yr, "goals", 3, 0),
        ]);

      // Team stats
      setTeamStats(statsRes.length > 0 ? statsRes[0] : null);

      // All games for record calculation
      setAllGames(gamesRes.items);

      // Recent games (last 5 by date descending)
      const sorted = [...gamesRes.items].sort(
        (a, b) => (b.date ?? "").localeCompare(a.date ?? "")
      );
      setRecentGames(sorted.slice(0, 5));

      // Top 3 performers
      setTopPerformers(topPerformersRes.items.slice(0, 3));

      // Chart data for DashboardStats
      setChartTopPlayers(
        playersRes.items.map((p) => ({
          player: p.player_name,
          goals: p.total_goals,
        }))
      );

      const perGame: PerGameData[] = gamesRes.items
        .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""))
        .slice(0, 20)
        .map((g, i) => {
          const isHome =
            g.home_team?.toLowerCase().includes(name.toLowerCase()) ?? false;
          return {
            label: g.date
              ? new Date(g.date).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })
              : `G${i + 1}`,
            goalsFor: (isHome ? g.home_score : g.away_score) ?? 0,
            goalsAgainst: (isHome ? g.away_score : g.home_score) ?? 0,
          };
        });
      setChartGamePerformance(perGame);
    } catch {
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelectionChange = useCallback(
    (abbr: string, yr: number, name: string) => {
      setSchool(abbr);
      setSchoolName(name);
      setSeason(yr);
      fetchData(abbr, yr, name);
    },
    [fetchData]
  );

  // Compute W-L-D record
  const record = { w: 0, l: 0, d: 0 };
  for (const game of allGames) {
    const r = getResult(game, schoolName);
    if (r?.label === "W") record.w++;
    else if (r?.label === "L") record.l++;
    else if (r?.label === "D") record.d++;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-primary-900">Overview</h2>
          <p className="text-muted-foreground">
            Your team at a glance
          </p>
        </div>
        <SchoolSeasonSelector onSelectionChange={handleSelectionChange} />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading dashboard...</span>
        </div>
      ) : (
        <>
          {/* Quick Stats Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-xl border bg-card p-4 text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="text-2xl font-bold text-primary-900 dark:text-white">
                {teamStats?.games_played ?? 0}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Games Played
              </div>
            </div>
            <div className="rounded-xl border bg-card p-4 text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Target className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="text-2xl font-bold text-primary-900 dark:text-white">
                {teamStats?.total_goals ?? 0}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Total Goals
              </div>
            </div>
            <div className="rounded-xl border bg-card p-4 text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Trophy className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="text-2xl font-bold text-primary-900 dark:text-white">
                <span className="text-green-700">{record.w}W</span>
                {" – "}
                <span className="text-red-700">{record.l}L</span>
                {" – "}
                <span className="text-yellow-700">{record.d}D</span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Season Record
              </div>
            </div>
            <div className="rounded-xl border bg-card p-4 text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Crosshair className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="text-2xl font-bold text-primary-900 dark:text-white">
                {teamStats?.total_shots ?? 0}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Total Shots
              </div>
            </div>
          </div>

          {/* Recent Games + Top Performers */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Games Feed */}
            <div className="lg:col-span-2 rounded-xl border bg-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-primary-900 dark:text-white">
                  Recent Games
                </h3>
                <Link
                  href="/dashboard/games"
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  View all
                </Link>
              </div>
              {recentGames.length > 0 ? (
                <div className="space-y-3">
                  {recentGames.map((game) => {
                    const result = getResult(game, schoolName);
                    return (
                      <Link
                        key={game.game_id}
                        href={`/dashboard/games/${game.game_id}`}
                        className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
                      >
                        <div className="flex items-center gap-3">
                          {result && (
                            <span
                              className={`inline-flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${result.color}`}
                            >
                              {result.label}
                            </span>
                          )}
                          <div>
                            <p className="text-sm font-semibold text-primary-900 dark:text-white">
                              {getOpponent(game, schoolName)}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatDate(game.date)}
                            </p>
                          </div>
                        </div>
                        <span className="text-base font-bold text-primary-900 dark:text-white">
                          {getScoreDisplay(game)}
                        </span>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground py-8 text-center">
                  No recent games for this selection.
                </p>
              )}
            </div>

            {/* Top Performers */}
            <div className="rounded-xl border bg-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-primary-900 dark:text-white">
                  Top Performers
                </h3>
                <Link
                  href="/dashboard/players"
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  View all
                </Link>
              </div>
              {topPerformers.length > 0 ? (
                <div className="space-y-3">
                  {topPerformers.map((player, idx) => (
                    <div
                      key={player.player_name}
                      className="flex items-center gap-3 rounded-lg border p-3"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-900 dark:bg-primary-900 dark:text-primary-100">
                        {idx + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-primary-900 dark:text-white truncate">
                          {player.player_name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {player.games_played} games
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1">
                          <Users className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="text-sm font-bold text-primary-900 dark:text-white">
                            {player.total_goals}G
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {player.total_assists}A
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground py-8 text-center">
                  No player data for this selection.
                </p>
              )}
            </div>
          </div>

          {/* Season Analytics Charts */}
          <DashboardStats
            school={school}
            season={season}
            loading={loading}
            error={error}
            topPlayers={chartTopPlayers}
            gamePerformance={chartGamePerformance}
            teamStats={teamStats}
          />
        </>
      )}
    </div>
  );
}
