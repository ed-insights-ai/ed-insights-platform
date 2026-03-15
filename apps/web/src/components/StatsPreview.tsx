"use client";

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
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  topTeamsByGoals,
  seasonPerformance,
  platformStats,
} from "@/lib/mock-data";

export function StatsPreview() {
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

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Bar Chart */}
          <div className="relative rounded-xl border bg-card p-6 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-primary-900 dark:text-white mb-4">
              Top 5 Teams by Goals Scored
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topTeamsByGoals}>
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
                  <Bar dataKey="goals" fill="#1a365d" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
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
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={seasonPerformance}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="week" tick={{ fontSize: 12 }} />
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
            </div>
            {/* Teaser blur overlay */}
            <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-gray-900 to-transparent rounded-b-xl pointer-events-none" />
          </div>
        </div>

        {/* Stats summary row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {platformStats.map((stat) => (
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
