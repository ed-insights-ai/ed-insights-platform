"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useGender } from "@/context/GenderContext";
import { getConferenceStandings, ConferenceStanding } from "@/lib/api";
import { FormBadgeStrip } from "@/components/stats/FormBadgeStrip";

export default function ExploreTeamsPage() {
  const { gender } = useGender();
  const [standings, setStandings] = useState<ConferenceStanding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const data = await getConferenceStandings("GAC", 2024, gender);
      if (!cancelled) {
        setStandings(data);
        setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [gender]);

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
          <h1 className="text-2xl font-bold text-slate-900">All Teams</h1>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${genderBadgeClass}`}
          >
            {genderLabel}
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Great American Conference &middot; 2024 Season
        </p>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-data-primary" />
        </div>
      ) : standings.length === 0 ? (
        <div className="text-center py-20 text-slate-500">
          No teams found.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {standings.map((team, idx) => (
            <Link
              key={team.school_id}
              href={`/explore/teams/${team.abbreviation}`}
              className="bento-card p-5 hover:shadow-md transition-shadow"
            >
              <p className="text-lg font-bold text-slate-900">
                {team.school_name}
              </p>
              <p className="text-sm text-slate-500 mt-0.5">
                {/* Mascot isn't in standings, so show record */}
              </p>
              <p className="text-sm font-semibold tabular-nums text-slate-700 mt-3">
                {team.wins}W-{team.losses}L-{team.draws}D
              </p>
              <div className="mt-2">
                <FormBadgeStrip
                  results={team.form.map((f) => ({
                    result: f.result as "W" | "L" | "D",
                    gameId: f.game_id,
                  }))}
                  size="sm"
                />
              </div>
              <p className="text-xs text-slate-500 mt-3 font-semibold">
                #{idx + 1} in GAC
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
