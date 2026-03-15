"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Loader2 } from "lucide-react";
import { SchoolSeasonSelector } from "@/components/SchoolSeasonSelector";
import { getTeamStats, getAllSeasonTeamStats } from "@/lib/api";
import type { TeamStatsAggregation } from "@/lib/api";

interface SeasonChartData {
  season: string;
  goals: number;
  shots: number;
  shots_on_goal: number;
  corners: number;
  saves: number;
}

export default function TeamsPage() {
  const [school, setSchool] = useState("");
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [teamStats, setTeamStats] = useState<TeamStatsAggregation | null>(null);
  const [seasonChartData, setSeasonChartData] = useState<SeasonChartData[]>([]);

  const fetchData = useCallback(async (abbr: string, yr: number) => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, allSeasonsRes] = await Promise.all([
        getTeamStats(abbr, yr),
        getAllSeasonTeamStats(abbr),
      ]);

      setTeamStats(statsRes.length > 0 ? statsRes[0] : null);

      const chartData: SeasonChartData[] = allSeasonsRes
        .sort((a, b) => a.season_year - b.season_year)
        .map((s) => ({
          season: `${s.season_year - 1}–${s.season_year}`,
          goals: s.total_goals,
          shots: s.total_shots,
          shots_on_goal: s.total_shots_on_goal,
          corners: s.total_corners,
          saves: s.total_saves,
        }));
      setSeasonChartData(chartData);
    } catch {
      setError("Failed to load team stats. Please try again.");
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
            Teams
          </h2>
          <p className="text-muted-foreground">
            Season aggregates and multi-season performance
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
        <>
          {/* Stat cards */}
          {teamStats ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {[
                { label: "Games Played", value: teamStats.games_played },
                { label: "Total Goals", value: teamStats.total_goals },
                { label: "Total Shots", value: teamStats.total_shots },
                {
                  label: "Shots on Goal",
                  value: teamStats.total_shots_on_goal,
                },
                { label: "Total Corners", value: teamStats.total_corners },
                { label: "Total Saves", value: teamStats.total_saves },
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
          ) : (
            <p className="text-muted-foreground text-sm py-4 text-center">
              No stats available for this selection.
            </p>
          )}

          {/* Multi-season bar chart */}
          <div className="rounded-xl border bg-card p-6">
            <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
              Stats Across Seasons
            </h3>
            {seasonChartData.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={seasonChartData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="season"
                      tick={{ fontSize: 11 }}
                      interval={0}
                      angle={-30}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey="goals"
                      name="Goals"
                      fill="#1a365d"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="shots_on_goal"
                      name="Shots on Goal"
                      fill="#0d9488"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="corners"
                      name="Corners"
                      fill="#d97706"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="saves"
                      name="Saves"
                      fill="#7c3aed"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm py-8 text-center">
                No season data available for this school.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
