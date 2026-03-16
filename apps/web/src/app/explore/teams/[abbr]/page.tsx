"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { ArrowLeft } from "lucide-react";
import { ContextualMetricCard } from "@/components/stats";
import { FormBadgeStrip } from "@/components/stats/FormBadgeStrip";
import { getTeamProfile } from "@/lib/api";
import type { TeamProfile } from "@/lib/api";

export default function TeamProfilePage() {
  const params = useParams();
  const abbr = params.abbr as string;

  const [profile, setProfile] = useState<TeamProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const data = await getTeamProfile(abbr);
      if (cancelled) return;
      setProfile(data);
      if (data) {
        setSelectedSeason(data.season.year);
      }
      setLoading(false);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [abbr]);

  const handleSeasonChange = useCallback(
    async (year: number) => {
      setSelectedSeason(year);
      setLoading(true);
      const data = await getTeamProfile(abbr, year);
      setProfile(data);
      setLoading(false);
    },
    [abbr]
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-data-primary" />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="space-y-6">
        <Link
          href="/explore/teams"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Teams
        </Link>
        <div className="text-center py-20 text-slate-500">Team not found.</div>
      </div>
    );
  }

  const s = profile.season;
  const kpis = profile.kpis;

  const genderBadgeClass =
    profile.gender === "women"
      ? "bg-purple-100 text-purple-700"
      : "bg-teal-100 text-teal-700";
  const genderLabel = profile.gender === "women" ? "Women's" : "Men's";

  // Trend chart data: reverse results_by_game so oldest first
  const trendData = [...profile.results_by_game].reverse().map((g, idx) => ({
    game: idx + 1,
    GF: g.goals_for,
    GA: g.goals_against,
    date: g.date
      ? new Date(g.date).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        })
      : "",
    opponent: g.opponent,
    score: `${g.home_score}-${g.away_score}`,
  }));

  // Top scorer max for bar scaling
  const maxGoals =
    profile.top_scorers.length > 0
      ? Math.max(...profile.top_scorers.map((s) => s.goals))
      : 1;

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/explore/teams"
        className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Teams
      </Link>

      {/* Identity Header */}
      <div className="bento-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                {profile.name} {profile.mascot}
              </h1>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${genderBadgeClass}`}
              >
                {genderLabel}
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              {profile.conference} {genderLabel} Soccer
            </p>
            <div className="flex items-center gap-3 mt-2">
              <span className="text-sm font-semibold tabular-nums text-slate-700">
                {s.wins}W-{s.losses}L-{s.draws}D
              </span>
              <span className="text-xs text-slate-400">&middot;</span>
              <span className="text-sm font-semibold text-data-primary">
                #{s.conf_rank} in {profile.conference}
              </span>
            </div>
          </div>
          <div>
            <select
              value={selectedSeason ?? ""}
              onChange={(e) => handleSeasonChange(Number(e.target.value))}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm focus:border-data-primary focus:outline-none focus:ring-1 focus:ring-data-primary"
            >
              {profile.available_seasons.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Form Strip */}
      <div className="flex items-center gap-2">
        <span className="stat-label">FORM</span>
        <FormBadgeStrip
          results={s.form.map((f) => ({
            result: f.result as "W" | "L" | "D",
            gameId: f.game_id,
          }))}
        />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <ContextualMetricCard
          label="Goals / Game"
          value={kpis.goals_per_game.toFixed(2)}
          delta={kpis.goals_per_game_delta}
          deltaUnit=""
          baseline="vs conf avg"
        />
        <ContextualMetricCard
          label="Shot Conversion"
          value={`${kpis.shot_conversion.toFixed(1)}%`}
          delta={kpis.shot_conversion_delta}
          deltaUnit="%"
          baseline="vs conf avg"
        />
        <ContextualMetricCard
          label="GA / Game"
          value={kpis.goals_against_per_game.toFixed(2)}
          delta={
            kpis.goals_against_per_game_delta !== 0
              ? -kpis.goals_against_per_game_delta
              : 0
          }
          deltaUnit=""
          baseline="vs conf avg"
        />
        <ContextualMetricCard
          label="Clean Sheets"
          value={kpis.clean_sheets}
        />
      </div>

      {/* Trend Chart + Top Scorers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* GF vs GA Trend */}
        <div className="bento-card p-5">
          <p className="stat-label mb-3">GF vs GA TREND</p>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="game"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  label={{
                    value: "Game #",
                    position: "insideBottom",
                    offset: -5,
                    fontSize: 11,
                    fill: "#94a3b8",
                  }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  allowDecimals={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0].payload;
                    return (
                      <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-md text-sm">
                        <p className="font-semibold text-slate-900">
                          {d.date} vs {d.opponent}
                        </p>
                        <p className="tabular-nums text-slate-600">
                          Score: {d.score}
                        </p>
                        <p className="text-data-primary tabular-nums">
                          GF: {d.GF}
                        </p>
                        <p className="text-data-opponent tabular-nums">
                          GA: {d.GA}
                        </p>
                      </div>
                    );
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="GF"
                  stroke="#0D9488"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Goals For"
                />
                <Line
                  type="monotone"
                  dataKey="GA"
                  stroke="#F97316"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Goals Against"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400 py-8 text-center">
              No game data.
            </p>
          )}
        </div>

        {/* Top Scorers */}
        <div className="bento-card p-5">
          <p className="stat-label mb-3">TOP SCORERS</p>
          {profile.top_scorers.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">
              No scorer data.
            </p>
          ) : (
            <div className="space-y-4">
              {profile.top_scorers.map((scorer) => (
                <div key={scorer.player_name}>
                  <div className="flex items-center justify-between mb-1">
                    <Link
                      href={`/explore/players/${profile.abbreviation}/${encodeURIComponent(scorer.player_name)}`}
                      className="text-sm font-medium text-slate-900 hover:text-data-primary hover:underline"
                    >
                      {scorer.player_name}
                    </Link>
                    <span className="text-sm tabular-nums text-slate-600">
                      {scorer.goals}G {scorer.assists}A
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-data-primary"
                      style={{
                        width: `${(scorer.goals / maxGoals) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Results Table */}
      <div className="bento-card p-5">
        <p className="stat-label mb-3">
          RESULTS &mdash; {selectedSeason} Season
        </p>
        {profile.results_by_game.length === 0 ? (
          <p className="text-sm text-slate-400 py-4 text-center">
            No games for this season.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  {["Date", "Opponent", "H/A", "Result", "Score"].map((h) => (
                    <th
                      key={h}
                      className="table-header px-3 py-2 text-left whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {profile.results_by_game.map((g) => {
                  const resultColor =
                    g.result === "W"
                      ? "text-data-positive"
                      : g.result === "L"
                        ? "text-data-negative"
                        : "text-data-neutral";
                  return (
                    <tr
                      key={g.game_id}
                      className="even:bg-surface-muted hover:bg-slate-50"
                    >
                      <td className="px-3 py-2 whitespace-nowrap tabular-nums">
                        {g.date
                          ? new Date(g.date).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            })
                          : "\u2014"}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {g.opponent}
                      </td>
                      <td className="px-3 py-2">{g.home_away}</td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <Link
                          href={`/dashboard/games/${g.game_id}`}
                          className="hover:underline"
                        >
                          <span className={`font-semibold ${resultColor}`}>
                            {g.result}
                          </span>
                        </Link>
                      </td>
                      <td className="px-3 py-2 tabular-nums">
                        <Link
                          href={`/dashboard/games/${g.game_id}`}
                          className="hover:underline"
                        >
                          {g.home_score}-{g.away_score}
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
