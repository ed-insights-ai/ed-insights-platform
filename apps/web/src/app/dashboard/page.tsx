"use client";

import { useCallback, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { SchoolSeasonSelector } from "@/components/SchoolSeasonSelector";
import { ContextualMetricCard, FormBadgeStrip } from "@/components/stats";
import { useGender } from "@/context/GenderContext";
import {
  getGames,
  getTeamStats,
  getPlayerLeaderboard,
  getConferenceAverages,
} from "@/lib/api";
import type {
  GameSummary,
  TeamStatsAggregation,
  PlayerLeaderboard,
  ConferenceAverages,
} from "@/lib/api";

export default function DashboardPage() {
  const { gender } = useGender();
  const [schoolName, setSchoolName] = useState("");
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [teamStats, setTeamStats] = useState<TeamStatsAggregation | null>(null);
  const [allGames, setAllGames] = useState<GameSummary[]>([]);
  const [topPerformers, setTopPerformers] = useState<PlayerLeaderboard[]>([]);
  const [confAvg, setConfAvg] = useState<ConferenceAverages | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const fetchData = useCallback(async (abbr: string, yr: number, _name: string) => {
    setLoading(true);
    setError(null);
    try {
      const [gamesRes, statsRes, topPerformersRes, confAvgRes] = await Promise.all([
        getGames(abbr, yr, 100, 0),
        getTeamStats(abbr, yr),
        getPlayerLeaderboard(abbr, yr, "goals", 5, 0),
        getConferenceAverages("GAC", yr, gender),
      ]);

      setTeamStats(statsRes.length > 0 ? statsRes[0] : null);
      setAllGames(gamesRes.items);
      setTopPerformers(topPerformersRes.items.slice(0, 5));
      setConfAvg(confAvgRes);
    } catch {
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [gender]);

  const handleSelectionChange = useCallback(
    (abbr: string, yr: number, name: string) => {
      setSchoolName(name);
      setSeason(yr);
      fetchData(abbr, yr, name);
    },
    [fetchData]
  );

  // --- Computed values ---

  // W-L-D record
  const record = { w: 0, l: 0, d: 0 };
  for (const game of allGames) {
    if (game.home_score == null || game.away_score == null) continue;
    const isHome = game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
    const schoolScore = isHome ? game.home_score : game.away_score;
    const opponentScore = isHome ? game.away_score : game.home_score;
    if (schoolScore > opponentScore) record.w++;
    else if (schoolScore < opponentScore) record.l++;
    else record.d++;
  }

  // KPI metrics
  const gamesPlayed = teamStats?.games_played ?? 0;
  const totalGoals = teamStats?.total_goals ?? 0;
  const totalShots = teamStats?.total_shots ?? 0;
  const goalsPerGame = gamesPlayed > 0 ? totalGoals / gamesPlayed : 0;
  const shotConversion = totalShots > 0 ? (totalGoals / totalShots) * 100 : 0;

  // Clean sheets: games where opponent scored 0
  const cleanSheets = allGames.filter((game) => {
    if (game.home_score == null || game.away_score == null) return false;
    const isHome = game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
    const opponentScore = isHome ? game.away_score : game.home_score;
    return opponentScore === 0;
  }).length;

  // Form badges (last 5 completed games)
  const formResults = [...allGames]
    .filter((g) => g.date != null && g.home_score != null && g.away_score != null)
    .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""))
    .slice(-5)
    .map((game) => {
      const isHome = game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
      const schoolScore = isHome ? game.home_score! : game.away_score!;
      const opponentScore = isHome ? game.away_score! : game.home_score!;
      const result: "W" | "L" | "D" =
        schoolScore > opponentScore ? "W" : schoolScore < opponentScore ? "L" : "D";
      return { result, gameId: game.game_id };
    });

  // Season trend chart data
  const trendData = [...allGames]
    .filter((g) => g.date != null && g.home_score != null && g.away_score != null)
    .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""))
    .map((g, i) => {
      const isHome = g.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
      return {
        label: g.date
          ? new Date(g.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })
          : `G${i + 1}`,
        gf: isHome ? (g.home_score ?? 0) : (g.away_score ?? 0),
        ga: isHome ? (g.away_score ?? 0) : (g.home_score ?? 0),
      };
    });

  // Conference average deltas
  const goalsPerGameDelta = confAvg
    ? parseFloat((goalsPerGame - confAvg.avg_goals_per_game).toFixed(2))
    : undefined;

  const shotConvDelta = confAvg
    ? parseFloat((shotConversion - confAvg.avg_shot_conversion).toFixed(1))
    : undefined;

  const cleanSheetPctDelta = confAvg && gamesPlayed > 0
    ? parseFloat(((cleanSheets / gamesPlayed * 100) - confAvg.avg_clean_sheet_pct).toFixed(1))
    : undefined;

  // Top contributors max goals for progress bar
  const maxGoals = topPerformers.length > 0 ? topPerformers[0].total_goals : 1;

  return (
    <div className="space-y-6">
      {/* Header row with compact selector */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-primary-900">War Room</h2>
          <p className="text-muted-foreground text-sm">Your team at a glance</p>
        </div>
        <SchoolSeasonSelector onSelectionChange={handleSelectionChange} />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading dashboard...</span>
        </div>
      ) : !schoolName ? (
        <div className="flex items-center justify-center py-16">
          <p className="text-muted-foreground">
            Select a school and season above to load the War Room.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Row 1 — Season Record (left 2 cols) */}
          <div className="lg:col-span-2 bento-card p-5">
            <p className="stat-label">SEASON RECORD</p>
            <p className="text-3xl font-extrabold tabular-nums text-slate-900 mt-1">
              <span className="text-data-positive">{record.w}</span>
              {" – "}
              <span className="text-data-negative">{record.l}</span>
              {" – "}
              <span className="text-data-neutral">{record.d}</span>
            </p>
            <div className="mt-3">
              <FormBadgeStrip results={formResults} />
            </div>
            <p className="text-xs text-slate-400 mt-2">{season} Season</p>
          </div>

          {/* Row 1 — Smart Insights placeholder (right 1 col) */}
          <div className="lg:col-span-1 bento-card p-5 bg-teal-50 border-teal-200">
            <p className="stat-label">SMART INSIGHTS</p>
            <p className="text-sm text-teal-700 mt-2">
              Insights powered by real data coming soon. Track scoring streaks,
              conversion trends, and conference benchmarks.
            </p>
          </div>

          {/* Row 2 — KPI Cards (3 cards spanning left 2 cols) */}
          <div className="lg:col-span-2 grid grid-cols-3 gap-4">
            <ContextualMetricCard
              label="Goals / Game"
              value={goalsPerGame.toFixed(2)}
              delta={goalsPerGameDelta}
              deltaUnit=""
              baseline="vs Conference Avg"
            />
            <ContextualMetricCard
              label="Shot Conversion"
              value={`${shotConversion.toFixed(1)}%`}
              delta={shotConvDelta}
              deltaUnit="%"
              baseline="vs Conference Avg"
            />
            <ContextualMetricCard
              label="Clean Sheets"
              value={cleanSheets}
              delta={cleanSheetPctDelta}
              deltaUnit="%"
              baseline="vs Conference Avg"
            />
          </div>

          {/* Row 2 right — intentionally empty (insights card spans from row 1) */}

          {/* Row 3 — Season Trend (left 2 cols) */}
          <div className="lg:col-span-2 bento-card p-5">
            <p className="stat-label mb-3">SEASON TREND</p>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trendData}>
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                  <YAxis width={24} tick={{ fontSize: 10 }} allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="gf"
                    stroke="#0D9488"
                    strokeWidth={2}
                    dot={{ fill: "#0D9488", r: 3 }}
                    name="Goals For"
                  />
                  <Line
                    type="monotone"
                    dataKey="ga"
                    stroke="#F97316"
                    strokeWidth={2}
                    dot={{ fill: "#F97316", r: 3 }}
                    name="Goals Against"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No game data available.
              </p>
            )}
          </div>

          {/* Row 3 — Top Contributors (right 1 col) */}
          <div className="lg:col-span-1 bento-card p-5">
            <p className="stat-label mb-3">TOP CONTRIBUTORS</p>
            {topPerformers.length > 0 ? (
              <div className="space-y-3">
                {topPerformers.map((player, idx) => (
                  <div key={player.player_name}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600 font-medium truncate mr-2">
                        <span className="text-slate-400 mr-1">{idx + 1}.</span>
                        {player.player_name}
                      </span>
                      <span className="shrink-0 text-xs font-semibold text-slate-700">
                        {player.total_goals}G {player.total_assists}A
                      </span>
                    </div>
                    <div className="mt-1 bg-slate-100 rounded-full h-1.5">
                      <div
                        className="h-1.5 rounded-full bg-data-primary"
                        style={{
                          width: `${maxGoals > 0 ? (player.total_goals / maxGoals) * 100 : 0}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No player data available.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
