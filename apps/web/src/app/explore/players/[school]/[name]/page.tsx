"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { ArrowLeft } from "lucide-react";
import { ContextualMetricCard } from "@/components/stats";
import { getPlayerProfile } from "@/lib/api";
import type { PlayerProfile, PlayerProfileSeason } from "@/lib/api";

export default function PlayerProfilePage() {
  const params = useParams();
  const school = params.school as string;
  const name = decodeURIComponent(params.name as string);

  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  // Initial load
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const data = await getPlayerProfile(school, name);
      if (cancelled) return;
      setProfile(data);
      if (data) {
        setSelectedSeason(data.seasons[0]?.season_year ?? null);
      }
      setLoading(false);
    }
    load();
    return () => { cancelled = true; };
  }, [school, name]);

  const handleSeasonChange = useCallback(
    async (year: number) => {
      setSelectedSeason(year);
      setLoading(true);
      const data = await getPlayerProfile(school, name, year);
      setProfile(data);
      setLoading(false);
    },
    [school, name]
  );

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-data-primary" />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8">
        <Link
          href="/explore/players"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-6"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Players
        </Link>
        <div className="text-center py-20 text-slate-500">
          Player not found.
        </div>
      </div>
    );
  }

  const currentSeason = profile.seasons.find(
    (s) => s.season_year === selectedSeason
  );
  const confAvg = profile.conf_averages;
  const genderBadgeClass =
    profile.gender === "women"
      ? "bg-purple-100 text-purple-700"
      : "bg-teal-100 text-teal-700";
  const genderLabel = profile.gender === "women" ? "Women's" : "Men's";

  // KPI values from selected season
  const goalsPerGame =
    currentSeason && currentSeason.games_played > 0
      ? currentSeason.goals / currentSeason.games_played
      : 0;
  const assistsPerGame =
    currentSeason && currentSeason.games_played > 0
      ? currentSeason.assists / currentSeason.games_played
      : 0;
  const shotConv = currentSeason?.shot_conversion ?? 0;
  const sogAcc = currentSeason?.sog_accuracy ?? 0;

  // Deltas vs conf average
  const goalsPerGameDelta =
    confAvg != null
      ? parseFloat((goalsPerGame - confAvg.goals_per_game).toFixed(2))
      : undefined;
  const shotConvDelta =
    confAvg != null
      ? parseFloat((shotConv - confAvg.shot_conversion).toFixed(1))
      : undefined;
  const sogAccDelta =
    confAvg != null
      ? parseFloat((sogAcc - confAvg.sog_accuracy).toFixed(1))
      : undefined;
  const assistsDelta =
    confAvg != null
      ? parseFloat((assistsPerGame - confAvg.assists_per_game).toFixed(2))
      : undefined;

  // Radar chart data
  const radarData = profile.radar
    ? [
        { axis: "Goals", player: profile.radar.goals_pct, avg: 50 },
        { axis: "Assists", player: profile.radar.assists_pct, avg: 50 },
        { axis: "Shots", player: profile.radar.shots_pct, avg: 50 },
        { axis: "SOG", player: profile.radar.sog_pct, avg: 50 },
        { axis: "Conv%", player: profile.radar.shot_conversion_pct, avg: 50 },
      ]
    : null;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 space-y-6">
      {/* Back link */}
      <Link
        href="/explore/players"
        className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Players
      </Link>

      {/* Identity Header */}
      <div className="bento-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                {profile.player_name}
              </h1>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${genderBadgeClass}`}
              >
                {genderLabel}
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              {profile.school_name}
            </p>
            <p className="text-sm text-slate-400 mt-0.5">
              {profile.career.seasons} season
              {profile.career.seasons !== 1 ? "s" : ""} &middot;{" "}
              {profile.career.goals}G {profile.career.assists}A &middot;{" "}
              {profile.career.shots} shots
            </p>
          </div>
          <div>
            <select
              value={selectedSeason ?? ""}
              onChange={(e) => handleSeasonChange(Number(e.target.value))}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm focus:border-data-primary focus:outline-none focus:ring-1 focus:ring-data-primary"
            >
              {profile.seasons.map((s) => (
                <option key={s.season_year} value={s.season_year}>
                  {s.season_year}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <ContextualMetricCard
          label="Goals / Game"
          value={goalsPerGame.toFixed(2)}
          delta={goalsPerGameDelta}
          deltaUnit=""
          baseline="vs conf avg"
        />
        <ContextualMetricCard
          label="Shot Conversion"
          value={`${shotConv.toFixed(1)}%`}
          delta={shotConvDelta}
          deltaUnit="%"
          baseline="vs conf avg"
        />
        <ContextualMetricCard
          label="SOG Accuracy"
          value={`${sogAcc.toFixed(1)}%`}
          delta={sogAccDelta}
          deltaUnit="%"
          baseline="vs conf avg"
        />
        <ContextualMetricCard
          label="Assists / Game"
          value={assistsPerGame.toFixed(2)}
          delta={assistsDelta}
          deltaUnit=""
          baseline="vs conf avg"
        />
      </div>

      {/* Radar + Career Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar Chart */}
        <div className="bento-card p-5">
          <p className="stat-label mb-3">PERCENTILE vs CONFERENCE</p>
          {radarData ? (
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis
                  dataKey="axis"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                />
                <Tooltip />
                <Radar
                  name="Conf Avg"
                  dataKey="avg"
                  stroke="#94a3b8"
                  strokeDasharray="4 4"
                  fill="none"
                  strokeWidth={1.5}
                />
                <Radar
                  name={profile.player_name}
                  dataKey="player"
                  stroke="#0D9488"
                  fill="#0D9488"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400 py-8 text-center">
              Not enough data for radar chart.
            </p>
          )}
        </div>

        {/* Career Stats Table */}
        <div className="bento-card p-5">
          <p className="stat-label mb-3">CAREER STATS BY SEASON</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  {["Season", "GP", "G", "A", "Sh", "SOG", "G/90", "Conv%"].map(
                    (h) => (
                      <th
                        key={h}
                        className="table-header px-2 py-2 text-center whitespace-nowrap"
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {profile.seasons.map((s: PlayerProfileSeason) => (
                  <tr
                    key={s.season_year}
                    onClick={() => handleSeasonChange(s.season_year)}
                    className={`cursor-pointer hover:bg-slate-50 ${
                      s.season_year === selectedSeason
                        ? "bg-teal-50 font-semibold"
                        : "even:bg-surface-muted"
                    }`}
                  >
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.season_year}
                    </td>
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.games_played}
                    </td>
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.goals}
                    </td>
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.assists}
                    </td>
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.shots}
                    </td>
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.shots_on_goal}
                    </td>
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.goals_per_90}
                    </td>
                    <td className="px-2 py-2 text-center tabular-nums">
                      {s.shot_conversion.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Game Log */}
      <div className="bento-card p-5">
        <p className="stat-label mb-3">
          GAME LOG &mdash; {selectedSeason} Season
        </p>
        {profile.game_log.length === 0 ? (
          <p className="text-sm text-slate-400 py-4 text-center">
            No games for this season.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  {["Date", "Opponent", "H/A", "Result", "G", "A", "Sh", "SOG"].map(
                    (h) => (
                      <th
                        key={h}
                        className="table-header px-3 py-2 text-left whitespace-nowrap"
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {profile.game_log.map((g) => {
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
                          : "—"}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {g.opponent}
                        {g.is_starter && (
                          <span className="ml-1 text-xs text-slate-400">
                            (S)
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2">{g.home_away}</td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <Link
                          href={`/dashboard/games/${g.game_id}`}
                          className="hover:underline"
                        >
                          <span className={`font-semibold ${resultColor}`}>
                            {g.result}
                          </span>{" "}
                          <span className="tabular-nums">{g.score}</span>
                        </Link>
                      </td>
                      <td className="px-3 py-2 text-center tabular-nums">
                        {g.goals}
                      </td>
                      <td className="px-3 py-2 text-center tabular-nums">
                        {g.assists}
                      </td>
                      <td className="px-3 py-2 text-center tabular-nums">
                        {g.shots}
                      </td>
                      <td className="px-3 py-2 text-center tabular-nums">
                        {g.shots_on_goal}
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
