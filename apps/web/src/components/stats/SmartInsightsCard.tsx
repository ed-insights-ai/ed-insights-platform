"use client";

import { useEffect, useState } from "react";
import { getInsights } from "@/lib/api";
import type { Insight } from "@/lib/api";

interface SmartInsightsCardProps {
  schoolAbbr: string;
  season: number;
}

export function SmartInsightsCard({ schoolAbbr, season }: SmartInsightsCardProps) {
  const requestKey = `${schoolAbbr}:${season}`;
  const [result, setResult] = useState<{
    requestKey: string;
    insights: Insight[];
  } | null>(null);

  useEffect(() => {
    if (!schoolAbbr) {
      return;
    }

    let ignore = false;
    getInsights(schoolAbbr, season).then((insights) => {
      if (!ignore) {
        setResult({ requestKey, insights });
      }
    });

    return () => {
      ignore = true;
    };
  }, [requestKey, schoolAbbr, season]);

  const isCurrentResult = result?.requestKey === requestKey;
  const insights = isCurrentResult ? result.insights : [];
  const loading = Boolean(schoolAbbr) && !isCurrentResult;

  return (
    <div className="lg:col-span-1 bento-card p-5 bg-teal-50 border-teal-200">
      <p className="stat-label">SMART INSIGHTS</p>
      {loading ? (
        <div className="mt-3 space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-4 bg-teal-100 rounded animate-pulse" />
          ))}
        </div>
      ) : insights.length === 0 ? (
        <p className="text-sm text-teal-600/60 mt-2">
          No notable trends this season.
        </p>
      ) : (
        <div className="mt-2 space-y-2">
          {insights.map((insight) => (
            <div key={insight.type} className="flex items-start gap-2 text-sm text-teal-800">
              <span className="shrink-0">{insight.icon}</span>
              <span className="leading-snug">{insight.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
