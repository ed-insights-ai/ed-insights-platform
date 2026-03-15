"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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
import { ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getSchools, getTeamStats, getGames } from "@/lib/api";

export function StatsPreview() {
  const [loading, setLoading] = useState(true);
  const [schoolCount, setSchoolCount] = useState(0);
  const [gamesCount, setGamesCount] = useState(0);
  const [totalGoals, setTotalGoals] = useState(0);
  const [topTeams, setTopTeams] = useState<{ team: string; goals: number }[]>(
    []
  );
  const [seasonTrend, setSeasonTrend] = useState<
    { season: string; goalsFor: number; goalsAgainst: number }[]
  >([]);

  useEffect(() => {
    async function loadPreview() {
      try {
        const schools = await getSchools();
        setSchoolCount(schools.length);

        if (schools.length === 0) {
          setLoading(false);
          return;
        }

        // Fetch stats across all schools and recent seasons to build preview data
        const seasons = [2025, 2024, 2023, 2022, 2021];
        const statsPromises = schools.flatMap((s) =>
          seasons.map((yr) => getTeamStats(s.abbreviation, yr))
        );
        const allStats = (await Promise.all(statsPromises)).flat();

        // Aggregate total games and goals
        const totalGames = allStats.reduce(
          (sum, s) => sum + s.games_played,
          0
        );
        const goals = allStats.reduce((sum, s) => sum + s.total_goals, 0);
        setGamesCount(totalGames);
        setTotalGoals(goals);

        // Top teams by goals (aggregate across seasons per school)
        const bySchool = new Map<string, number>();
        for (const s of allStats) {
          bySchool.set(
            s.school_name,
            (bySchool.get(s.school_name) ?? 0) + s.total_goals
          );
        }
        const sorted = Array.from(bySchool.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([team, goals]) => ({ team, goals }));
        setTopTeams(sorted);

        // Season trend for the first school (as representative data)
        const firstSchool = schools[0];
        const trendPromises = seasons.map(async (yr) => {
          const games = await getGames(firstSchool.abbreviation, yr, 100, 0);
          let goalsFor = 0;
          let goalsAgainst = 0;
          for (const g of games.items) {
            const isHome =
              g.home_team
                ?.toLowerCase()
                .includes(firstSchool.name.split(" ")[0].toLowerCase()) ??
              false;
            goalsFor += (isHome ? g.home_score : g.away_score) ?? 0;
            goalsAgainst += (isHome ? g.away_score : g.home_score) ?? 0;
          }
          return {
            season: `${yr - 1}-${String(yr).slice(2)}`,
            goalsFor,
            goalsAgainst,
          };
        });
        const trend = (await Promise.all(trendPromises))
          .filter((t) => t.goalsFor > 0 || t.goalsAgainst > 0)
          .reverse();
        setSeasonTrend(trend);
      } catch (err) {
        console.error("Error loading preview data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadPreview();
  }, []);

  const stats = [
    { label: "Partner Schools", value: String(schoolCount) },
    {
      label: "Total Goals",
      value: totalGoals > 0 ? totalGoals.toLocaleString() : "--",
    },
    {
      label: "Matches Analyzed",
      value: gamesCount > 0 ? gamesCount.toLocaleString() : "--",
    },
    { label: "Seasons of Data", value: "10" },
  ];

  return (
    <section className="py-20 dark:bg-gray-900">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-primary-900 dark:text-white mb-4">
            Platform Preview
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Get a glimpse of the NCAA D2 soccer analytics powering smarter
            decisions for coaches and programs.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <span className="ml-3 text-muted-foreground">
              Loading preview...
            </span>
          </div>
        ) : (
          <>
            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
              {/* Bar Chart */}
              <div className="relative rounded-xl border bg-card p-6 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
                  Top Schools by Goals Scored
                </h3>
                <div className="h-64">
                  {topTeams.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={topTeams}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                        <XAxis
                          dataKey="team"
                          tick={{ fontSize: 12 }}
                          interval={0}
                          angle={-20}
                          textAnchor="end"
                          height={50}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip />
                        <Bar
                          dataKey="goals"
                          fill="#1a365d"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                      No data available yet
                    </div>
                  )}
                </div>
                {/* Teaser blur overlay */}
                <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-gray-900 to-transparent rounded-b-xl pointer-events-none" />
              </div>

              {/* Line Chart */}
              <div className="relative rounded-xl border bg-card p-6 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
                  Season Performance Trend
                </h3>
                <div className="h-64">
                  {seasonTrend.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={seasonTrend}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                        <XAxis dataKey="season" tick={{ fontSize: 12 }} />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="goalsFor"
                          stroke="#0d9488"
                          strokeWidth={2}
                          dot={{ fill: "#0d9488", r: 4 }}
                          name="Goals For"
                        />
                        <Line
                          type="monotone"
                          dataKey="goalsAgainst"
                          stroke="#ea580c"
                          strokeWidth={2}
                          dot={{ fill: "#ea580c", r: 4 }}
                          name="Goals Against"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                      No data available yet
                    </div>
                  )}
                </div>
                {/* Teaser blur overlay */}
                <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-gray-900 to-transparent rounded-b-xl pointer-events-none" />
              </div>
            </div>

            {/* Stats summary row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-xl border bg-card p-6 text-center dark:border-gray-700"
                >
                  <div className="text-3xl font-bold text-primary-900 dark:text-white">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* CTA */}
        <div className="text-center">
          <Link href="/signup">
            <Button
              size="lg"
              className="bg-accent hover:bg-accent-700 text-lg px-8 transition-transform duration-200 hover:scale-105"
            >
              Sign up to explore the full dataset
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
