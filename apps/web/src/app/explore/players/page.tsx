"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { useGender } from "@/context/GenderContext";
import {
  getPlayerLeaderboard,
  getSchools,
  PlayerLeaderboard,
} from "@/lib/api";

type SortKey =
  | "games_played"
  | "total_goals"
  | "total_assists"
  | "points"
  | "total_shots"
  | "conv_pct"
  | "g_per_90";

const SEASONS = Array.from({ length: 10 }, (_, i) => 2025 - i);
const MIN_GAMES_OPTIONS = [1, 3, 5, 8, 10];

const COLUMNS: { label: string; key: SortKey | null; className?: string }[] = [
  { label: "#", key: null, className: "text-slate-400 text-xs w-8" },
  { label: "Player", key: null, className: "text-left" },
  { label: "School", key: null, className: "text-left" },
  { label: "GP", key: "games_played" },
  { label: "G", key: "total_goals" },
  { label: "A", key: "total_assists" },
  { label: "Pts", key: "points" },
  { label: "Shots", key: "total_shots" },
  { label: "Conv%", key: "conv_pct" },
  { label: "G/90", key: "g_per_90" },
];

function computeValue(p: PlayerLeaderboard, key: SortKey): number {
  switch (key) {
    case "total_goals":
      return p.total_goals;
    case "total_assists":
      return p.total_assists;
    case "points":
      return p.total_goals + p.total_assists;
    case "total_shots":
      return p.total_shots;
    case "games_played":
      return p.games_played;
    case "conv_pct":
      return p.total_shots > 0
        ? (p.total_goals / p.total_shots) * 100
        : 0;
    case "g_per_90":
      return p.total_minutes > 0
        ? (p.total_goals / p.total_minutes) * 90
        : 0;
  }
}

export default function ExplorePlayersPage() {
  const { gender } = useGender();
  const [players, setPlayers] = useState<PlayerLeaderboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [season, setSeason] = useState(2025);
  const [sortKey, setSortKey] = useState<SortKey>("total_goals");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [minGames, setMinGames] = useState(5);
  const [genderSchools, setGenderSchools] = useState<Set<string>>(new Set());

  // Fetch schools for gender filtering
  useEffect(() => {
    getSchools({ gender }).then((schools) => {
      setGenderSchools(new Set(schools.map((s) => s.name)));
    });
  }, [gender]);

  // Fetch players (no school filter = all schools)
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const data = await getPlayerLeaderboard("", season, "goals", 100, 0);
      if (!cancelled) {
        setPlayers(data.items);
        setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [season, gender]);

  // Client-side filter + sort
  const filtered = useMemo(() => {
    const result = players
      .filter((p) => p.games_played >= minGames)
      .filter(
        (p) => genderSchools.size === 0 || genderSchools.has(p.school_name)
      );

    result.sort((a, b) => {
      const av = computeValue(a, sortKey);
      const bv = computeValue(b, sortKey);
      return sortDir === "asc" ? av - bv : bv - av;
    });

    return result;
  }, [players, minGames, sortKey, sortDir, genderSchools]);

  const handleSort = useCallback(
    (key: SortKey | null) => {
      if (!key) return;
      if (sortKey === key) {
        setSortDir(sortDir === "asc" ? "desc" : "asc");
      } else {
        setSortKey(key);
        setSortDir("desc");
      }
    },
    [sortKey, sortDir]
  );

  const genderLabel = gender === "women" ? "Women's" : "Men's";
  const genderBadgeClass =
    gender === "women"
      ? "bg-purple-100 text-purple-700"
      : "bg-teal-100 text-teal-700";

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold text-slate-900">Players</h2>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${genderBadgeClass}`}
          >
            {genderLabel}
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          GAC Conference &middot; {season} Season
        </p>
      </div>

      {/* Controls row */}
      <div className="flex items-center justify-between">
        <select
          value={season}
          onChange={(e) => setSeason(Number(e.target.value))}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm focus:border-data-primary focus:outline-none focus:ring-1 focus:ring-data-primary"
        >
          {SEASONS.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>

        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>Min GP:</span>
          <select
            value={minGames}
            onChange={(e) => setMinGames(Number(e.target.value))}
            className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-700 shadow-sm focus:border-data-primary focus:outline-none focus:ring-1 focus:ring-data-primary"
          >
            {MIN_GAMES_OPTIONS.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-data-primary" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-slate-500">
          No player data for this selection.
        </div>
      ) : (
        <div className="bento-card overflow-x-auto">
          <p className="stat-label mb-3">PLAYER LEADERBOARD</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                {COLUMNS.map((col, i) => (
                  <th
                    key={i}
                    onClick={() => handleSort(col.key)}
                    className={`table-header px-3 py-2 whitespace-nowrap ${
                      col.className?.includes("text-left")
                        ? "text-left"
                        : "text-center"
                    } ${
                      col.key
                        ? "cursor-pointer select-none hover:text-slate-900"
                        : ""
                    } ${
                      col.key && sortKey === col.key
                        ? "!font-extrabold !text-slate-900"
                        : ""
                    }`}
                  >
                    {col.label}
                    {col.key && sortKey === col.key && (
                      <span className="ml-1">
                        {sortDir === "asc" ? "▲" : "▼"}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((p, idx) => {
                const pts = p.total_goals + p.total_assists;
                const convPct =
                  p.total_shots > 0
                    ? ((p.total_goals / p.total_shots) * 100).toFixed(1) + "%"
                    : "0.0%";
                const gPer90 =
                  p.total_minutes > 0
                    ? ((p.total_goals / p.total_minutes) * 90).toFixed(2)
                    : "–";

                return (
                  <tr
                    key={`${p.player_name}-${p.school_id}`}
                    className="even:bg-surface-muted hover:bg-slate-50"
                  >
                    <td className="px-3 py-2 text-center text-slate-400 text-xs">
                      {idx + 1}
                    </td>
                    <td className="px-3 py-2 text-left font-medium text-slate-900 whitespace-nowrap">
                      <Link
                        href={`/explore/players/${p.school_abbreviation}/${encodeURIComponent(p.player_name)}`}
                        className="hover:text-data-primary hover:underline"
                      >
                        {p.player_name}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-left text-slate-500 text-sm whitespace-nowrap">
                      {p.school_name}
                    </td>
                    <td className="px-3 py-2 text-center tabular-nums">
                      {p.games_played}
                    </td>
                    <td
                      className={`px-3 py-2 text-center tabular-nums ${
                        sortKey === "total_goals" ? "font-bold" : ""
                      }`}
                    >
                      {p.total_goals}
                    </td>
                    <td
                      className={`px-3 py-2 text-center tabular-nums ${
                        sortKey === "total_assists" ? "font-bold" : ""
                      }`}
                    >
                      {p.total_assists}
                    </td>
                    <td
                      className={`px-3 py-2 text-center tabular-nums ${
                        sortKey === "points" ? "font-bold" : ""
                      }`}
                    >
                      {pts}
                    </td>
                    <td className="px-3 py-2 text-center tabular-nums">
                      {p.total_shots}
                    </td>
                    <td className="px-3 py-2 text-center tabular-nums">
                      {convPct}
                    </td>
                    <td className="px-3 py-2 text-center tabular-nums">
                      {gPer90}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
