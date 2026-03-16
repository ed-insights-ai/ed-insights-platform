"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useGender } from "@/context/GenderContext";
import { getConferenceStandings, ConferenceStanding } from "@/lib/api";
import { FormBadgeStrip } from "@/components/stats/FormBadgeStrip";

type SortKey = keyof Pick<
  ConferenceStanding,
  | "school_name"
  | "games_played"
  | "wins"
  | "losses"
  | "draws"
  | "goals_for"
  | "goals_against"
  | "goal_diff"
  | "points"
  | "ppg"
>;

const COLUMNS: { label: string; key: SortKey | null; className?: string }[] = [
  { label: "#", key: null, className: "text-slate-400 text-xs w-8" },
  { label: "School", key: "school_name", className: "text-left" },
  { label: "GP", key: "games_played" },
  { label: "W", key: "wins" },
  { label: "L", key: "losses" },
  { label: "D", key: "draws" },
  { label: "GF", key: "goals_for" },
  { label: "GA", key: "goals_against" },
  { label: "GD", key: "goal_diff" },
  { label: "Pts", key: "points" },
  { label: "PPG", key: "ppg" },
  { label: "Form", key: null },
];

const SEASONS = Array.from({ length: 10 }, (_, i) => 2025 - i);

export default function ConferencePage() {
  const params = useParams();
  const abbr = (params.abbr as string) ?? "GAC";
  const { gender } = useGender();

  const [standings, setStandings] = useState<ConferenceStanding[]>([]);
  const [loading, setLoading] = useState(true);
  const [season, setSeason] = useState(2025);
  const [sortKey, setSortKey] = useState<SortKey>("points");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      let data = await getConferenceStandings(abbr, season, gender);
      if (!cancelled && data.length === 0 && season === 2025) {
        data = await getConferenceStandings(abbr, 2024, gender);
        if (!cancelled && data.length > 0) setSeason(2024);
      }
      if (!cancelled) {
        setStandings(data);
        setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [abbr, season, gender]);

  const sorted = [...standings].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === "string" && typeof bv === "string") {
      return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    return sortDir === "asc" ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  const handleSort = (key: SortKey | null) => {
    if (!key) return;
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "school_name" ? "asc" : "desc");
    }
  };

  const genderLabel = gender === "women" ? "Women's" : "Men's";
  const genderBadgeClass =
    gender === "women"
      ? "bg-purple-100 text-purple-700"
      : "bg-teal-100 text-teal-700";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-900">
            {abbr} Conference
          </h1>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${genderBadgeClass}`}
          >
            {genderLabel}
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Great American Conference &middot; {season} Season
        </p>
      </div>

      {/* Season selector */}
      <div>
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
      </div>

      {/* Standings table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-data-primary" />
        </div>
      ) : sorted.length === 0 ? (
        <div className="text-center py-20 text-slate-500">
          No standings data for {season}.
        </div>
      ) : (
        <div className="bento-card overflow-x-auto">
          <p className="stat-label mb-3">STANDINGS</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                {COLUMNS.map((col, i) => (
                  <th
                    key={i}
                    onClick={() => handleSort(col.key)}
                    className={`px-3 py-2 font-medium text-slate-500 whitespace-nowrap ${
                      col.key === "school_name" ? "text-left" : "text-center"
                    } ${col.key ? "cursor-pointer select-none hover:text-slate-900" : ""}`}
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
              {sorted.map((row, idx) => (
                <tr
                  key={row.school_id}
                  className={`
                    even:bg-surface-muted hover:bg-slate-50 cursor-pointer
                    ${idx === 0 ? "border-l-2 border-data-primary" : ""}
                  `}
                >
                  {/* Rank */}
                  <td className="px-3 py-2 text-center text-slate-400 text-xs">
                    {idx + 1}
                  </td>
                  {/* School */}
                  <td className="px-3 py-2 text-left font-medium text-slate-900 whitespace-nowrap">
                    <Link
                      href={`/explore/teams/${row.abbreviation}`}
                      className="hover:text-data-primary hover:underline"
                    >
                      {row.school_name}
                    </Link>
                  </td>
                  {/* GP */}
                  <td className="px-3 py-2 text-center tabular-nums">
                    {row.games_played}
                  </td>
                  {/* W */}
                  <td className="px-3 py-2 text-center tabular-nums text-data-positive font-semibold">
                    {row.wins}
                  </td>
                  {/* L */}
                  <td className="px-3 py-2 text-center tabular-nums text-data-negative font-semibold">
                    {row.losses}
                  </td>
                  {/* D */}
                  <td className="px-3 py-2 text-center tabular-nums text-data-neutral font-semibold">
                    {row.draws}
                  </td>
                  {/* GF */}
                  <td className="px-3 py-2 text-center tabular-nums">
                    {row.goals_for}
                  </td>
                  {/* GA */}
                  <td className="px-3 py-2 text-center tabular-nums">
                    {row.goals_against}
                  </td>
                  {/* GD */}
                  <td
                    className={`px-3 py-2 text-center tabular-nums font-semibold ${
                      row.goal_diff > 0
                        ? "text-data-positive"
                        : row.goal_diff < 0
                          ? "text-data-negative"
                          : "text-slate-400"
                    }`}
                  >
                    {row.goal_diff > 0 ? `+${row.goal_diff}` : row.goal_diff}
                  </td>
                  {/* Pts */}
                  <td className="px-3 py-2 text-center tabular-nums font-extrabold text-slate-900">
                    {row.points}
                  </td>
                  {/* PPG */}
                  <td className="px-3 py-2 text-center tabular-nums">
                    {row.ppg.toFixed(2)}
                  </td>
                  {/* Form */}
                  <td className="px-3 py-2">
                    <FormBadgeStrip
                      results={row.form.map((f) => ({
                        result: f.result as "W" | "L" | "D",
                        gameId: f.game_id,
                      }))}
                      size="sm"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
