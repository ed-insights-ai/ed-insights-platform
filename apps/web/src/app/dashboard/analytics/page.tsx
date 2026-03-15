"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  Cell,
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
import { getGames, getTeamStats, getPlayerLeaderboard } from "@/lib/api";
import type { GameSummary, TeamStatsAggregation, PlayerLeaderboard } from "@/lib/api";

interface TrendPoint {
  label: string;
  goals_for: number;
  goals_against: number;
}

interface FunnelPoint {
  name: string;
  value: number;
}

interface ScorerData {
  name: string;
  goals: number;
}

export default function AnalyticsPage() {
  const [school, setSchool] = useState("");
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [funnelData, setFunnelData] = useState<FunnelPoint[]>([]);
  const [scorerData, setScorerData] = useState<ScorerData[]>([]);

  const fetchData = useCallback(async (abbr: string, yr: number) => {
    setLoading(true);
    setError(null);
    try {
      const [gamesRes, teamRes, playersRes] = await Promise.all([
        getGames(abbr, yr, 100, 0),
        getTeamStats(abbr, yr),
        getPlayerLeaderboard(abbr, yr, "goals", 10, 0),
      ]);

      // 1. Season trend: goals for vs goals against per game
      const games = gamesRes.items
        .filter((g: GameSummary) => g.home_score !== null && g.away_score !== null)
        .sort((a: GameSummary, b: GameSummary) =>
          (a.date ?? "").localeCompare(b.date ?? "")
        );

      const trend: TrendPoint[] = games.map((g: GameSummary, i: number) => {
        const isHome = g.home_team?.toUpperCase().includes(abbr.toUpperCase());
        return {
          label: `G${i + 1}`,
          goals_for: isHome ? (g.home_score ?? 0) : (g.away_score ?? 0),
          goals_against: isHome ? (g.away_score ?? 0) : (g.home_score ?? 0),
        };
      });
      setTrendData(trend);

      // 2. Shot funnel: shots -> shots on goal -> goals
      if (teamRes.length > 0) {
        const stats: TeamStatsAggregation = teamRes[0];
        setFunnelData([
          { name: "Shots", value: stats.total_shots },
          { name: "Shots on Goal", value: stats.total_shots_on_goal },
          { name: "Goals", value: stats.total_goals },
        ]);
      } else {
        setFunnelData([]);
      }

      // 3. Top scorers horizontal bar
      const scorers: ScorerData[] = playersRes.items.map((p: PlayerLeaderboard) => ({
        name: p.player_name,
        goals: p.total_goals,
      }));
      setScorerData(scorers);
    } catch {
      setError("Failed to load analytics data. Please try again.");
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

  useEffect(() => {
    if (school) fetchData(school, season);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-primary-900 dark:text-white">
            Analytics
          </h2>
          <p className="text-muted-foreground">
            Season trends, shot efficiency, and top scorers
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
          <span className="ml-3 text-muted-foreground">Loading data...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Season Trend: Goals For vs Goals Against */}
          <div className="rounded-xl border bg-card p-6 lg:col-span-2">
            <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
              Season Trend &mdash; Goals For vs Against
            </h3>
            {trendData.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="goals_for"
                      name="Goals For"
                      stroke="#0d9488"
                      strokeWidth={2}
                      dot={{ fill: "#0d9488", r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="goals_against"
                      name="Goals Against"
                      stroke="#ea580c"
                      strokeWidth={2}
                      dot={{ fill: "#ea580c", r: 3 }}
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

          {/* Shot Funnel */}
          <div className="rounded-xl border bg-card p-6">
            <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
              Shot Funnel
            </h3>
            {funnelData.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={funnelData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                    <YAxis
                      dataKey="name"
                      type="category"
                      width={110}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip />
                    <Bar dataKey="value" name="Count" radius={[0, 4, 4, 0]}>
                      {funnelData.map((_, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={["#1a365d", "#0d9488", "#d97706"][index]}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm py-8 text-center">
                No team stats available for this selection.
              </p>
            )}
          </div>

          {/* Top Scorers */}
          <div className="rounded-xl border bg-card p-6">
            <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
              Top Scorers
            </h3>
            {scorerData.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={scorerData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                    <YAxis
                      dataKey="name"
                      type="category"
                      width={120}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip />
                    <Bar
                      dataKey="goals"
                      name="Goals"
                      fill="#1a365d"
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm py-8 text-center">
                No scorer data available for this selection.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
