"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Loader2 } from "lucide-react";
import { SchoolSeasonSelector } from "@/components/SchoolSeasonSelector";
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

export function DashboardStats() {
  const [school, setSchool] = useState("");
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [topPlayers, setTopPlayers] = useState<
    { player: string; goals: number }[]
  >([]);
  const [gamePerformance, setGamePerformance] = useState<PerGameData[]>([]);
  const [teamStats, setTeamStats] = useState<TeamStatsAggregation | null>(null);

  const fetchData = useCallback(async (abbr: string, yr: number) => {
    setLoading(true);
    setError(null);
    try {
      const [gamesRes, statsRes, playersRes] = await Promise.all([
        getGames(abbr, yr, 100, 0),
        getTeamStats(abbr, yr),
        getPlayerLeaderboard(abbr, yr, "goals", 5, 0),
      ]);

      // Top 5 players by goals
      setTopPlayers(
        playersRes.items.map((p: PlayerLeaderboard) => ({
          player: p.player_name,
          goals: p.total_goals,
        }))
      );

      // Per-game performance (goals for / against) from game results
      const perGame: PerGameData[] = gamesRes.items
        .sort(
          (a: GameSummary, b: GameSummary) =>
            (a.date ?? "").localeCompare(b.date ?? "")
        )
        .slice(0, 20)
        .map((g: GameSummary, i: number) => {
          const isHome =
            g.home_team?.toLowerCase().includes("harding") ?? false;
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
      setGamePerformance(perGame);

      // Aggregate team stats
      setTeamStats(statsRes.length > 0 ? statsRes[0] : null);
    } catch {
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelectionChange = useCallback(
    (abbr: string, yr: number) => {
      setSchool(abbr);
      setSeason(yr);
      fetchData(abbr, yr);
    },
    [fetchData]
  );

  // Don't fetch on mount — the selector triggers the initial load
  useEffect(() => {
    if (school) fetchData(school, season);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="text-lg font-semibold text-primary-900 dark:text-white">
          Season Analytics
        </h3>
        <SchoolSeasonSelector onSelectionChange={handleSelectionChange} />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Summary cards */}
      {teamStats && !loading && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Games Played", value: teamStats.games_played },
            { label: "Total Goals", value: teamStats.total_goals },
            { label: "Total Shots", value: teamStats.total_shots },
            { label: "Saves", value: teamStats.total_saves },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-xl border bg-card p-4 text-center"
            >
              <div className="text-2xl font-bold text-primary-900 dark:text-white">
                {s.value}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {s.label}
              </div>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading data...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top players bar chart */}
          <div className="rounded-xl border bg-card p-6">
            <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
              Top 5 Scorers
            </h3>
            {topPlayers.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topPlayers}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="player"
                      tick={{ fontSize: 11 }}
                      interval={0}
                      angle={-20}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                    <Tooltip />
                    <Bar
                      dataKey="goals"
                      fill="#1a365d"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm py-8 text-center">
                No player data available for this selection.
              </p>
            )}
          </div>

          {/* Game-by-game performance */}
          <div className="rounded-xl border bg-card p-6">
            <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
              Game-by-Game Performance
            </h3>
            {gamePerformance.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={gamePerformance}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="goalsFor"
                      stroke="#0d9488"
                      strokeWidth={2}
                      dot={{ fill: "#0d9488", r: 3 }}
                      name="Goals For"
                    />
                    <Line
                      type="monotone"
                      dataKey="goalsAgainst"
                      stroke="#ea580c"
                      strokeWidth={2}
                      dot={{ fill: "#ea580c", r: 3 }}
                      name="Goals Against"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm py-8 text-center">
                No game data available for this selection.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
