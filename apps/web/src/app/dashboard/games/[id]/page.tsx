"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
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
import {
  Loader2,
  ArrowLeft,
  Calendar,
  MapPin,
  Users,
  Clock,
} from "lucide-react";
import { getGameDetail } from "@/lib/api";
import type {
  GameDetail,
  TeamGameStatsResponse,
  PlayerGameStatsResponse,
  GameEventResponse,
} from "@/lib/api";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "TBD";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function getEventIcon(eventType: string | null): string {
  switch (eventType?.toLowerCase()) {
    case "goal":
      return "\u26BD";
    case "yellow card":
    case "caution":
      return "\uD83D\uDFE8";
    case "red card":
    case "ejection":
      return "\uD83D\uDFE5";
    case "substitution":
    case "sub":
      return "\uD83D\uDD04";
    default:
      return "\u25CF";
  }
}

interface TeamStatsChartData {
  stat: string;
  home: number;
  away: number;
}

function buildTeamStatsChart(
  teamStats: TeamGameStatsResponse[]
): TeamStatsChartData[] {
  const home = teamStats.find((t) => t.is_home === true);
  const away = teamStats.find((t) => t.is_home === false);

  if (!home && !away) return [];

  return [
    { stat: "Shots", home: home?.shots ?? 0, away: away?.shots ?? 0 },
    {
      stat: "Shots on Goal",
      home: home?.shots_on_goal ?? 0,
      away: away?.shots_on_goal ?? 0,
    },
    { stat: "Corners", home: home?.corners ?? 0, away: away?.corners ?? 0 },
    { stat: "Saves", home: home?.saves ?? 0, away: away?.saves ?? 0 },
  ];
}

function groupPlayersByTeam(
  players: PlayerGameStatsResponse[],
  game: GameDetail
): { home: PlayerGameStatsResponse[]; away: PlayerGameStatsResponse[] } {
  const home: PlayerGameStatsResponse[] = [];
  const away: PlayerGameStatsResponse[] = [];

  for (const p of players) {
    if (
      p.team?.toLowerCase() === game.home_team?.toLowerCase() ||
      (game.team_stats.find((t) => t.is_home && t.team === p.team) !==
        undefined)
    ) {
      home.push(p);
    } else {
      away.push(p);
    }
  }

  return { home, away };
}

function PlayerStatsTable({
  players,
  teamName,
}: {
  players: PlayerGameStatsResponse[];
  teamName: string | null;
}) {
  if (players.length === 0) return null;

  const sorted = [...players].sort((a, b) => {
    if (a.is_starter && !b.is_starter) return -1;
    if (!a.is_starter && b.is_starter) return 1;
    return (a.jersey_number ?? "99").localeCompare(b.jersey_number ?? "99", undefined, { numeric: true });
  });

  return (
    <div className="rounded-xl border bg-card overflow-hidden">
      <div className="border-b bg-muted/50 px-4 py-3">
        <h4 className="font-semibold text-primary-900">{teamName ?? "Unknown Team"}</h4>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs text-muted-foreground">
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Pos</th>
              <th className="px-3 py-2 text-center">Min</th>
              <th className="px-3 py-2 text-center">Shots</th>
              <th className="px-3 py-2 text-center">SOG</th>
              <th className="px-3 py-2 text-center">G</th>
              <th className="px-3 py-2 text-center">A</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((p) => (
              <tr
                key={p.id}
                className="border-b last:border-0 hover:bg-muted/30"
              >
                <td className="px-3 py-2 font-mono text-xs">
                  {p.jersey_number ?? "—"}
                </td>
                <td className="px-3 py-2 font-medium">
                  {p.player_name ?? "Unknown"}
                  {p.is_starter && (
                    <span className="ml-1.5 text-[10px] text-muted-foreground">
                      (S)
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-muted-foreground">
                  {p.position ?? "—"}
                </td>
                <td className="px-3 py-2 text-center">{p.minutes ?? "—"}</td>
                <td className="px-3 py-2 text-center">{p.shots ?? 0}</td>
                <td className="px-3 py-2 text-center">
                  {p.shots_on_goal ?? 0}
                </td>
                <td className="px-3 py-2 text-center font-semibold">
                  {p.goals ?? 0}
                </td>
                <td className="px-3 py-2 text-center">{p.assists ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EventsTimeline({ events }: { events: GameEventResponse[] }) {
  if (events.length === 0) {
    return (
      <p className="text-muted-foreground text-sm py-4 text-center">
        No events recorded for this game.
      </p>
    );
  }

  const sorted = [...events].sort((a, b) => {
    const clockA = a.clock ?? "99:99";
    const clockB = b.clock ?? "99:99";
    return clockA.localeCompare(clockB);
  });

  return (
    <div className="space-y-2">
      {sorted.map((event) => (
        <div
          key={event.id}
          className="flex items-start gap-3 rounded-lg border bg-card px-4 py-3"
        >
          <span className="text-lg leading-none mt-0.5">
            {getEventIcon(event.event_type)}
          </span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-muted-foreground">
                {event.clock ?? "—"}
              </span>
              <span className="text-xs font-medium uppercase text-muted-foreground">
                {event.event_type ?? "Event"}
              </span>
            </div>
            <p className="text-sm font-medium text-primary-900 mt-0.5">
              {event.player ?? "Unknown"}
              {event.assist1 && (
                <span className="text-muted-foreground font-normal">
                  {" "}
                  (assist: {event.assist1}
                  {event.assist2 ? `, ${event.assist2}` : ""})
                </span>
              )}
            </p>
            {event.team && (
              <p className="text-xs text-muted-foreground">{event.team}</p>
            )}
            {event.description && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {event.description}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function GameDetailPage() {
  const params = useParams();
  const gameId = Number(params.id);

  const [game, setGame] = useState<GameDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNaN(gameId)) {
      setError("Invalid game ID.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const detail = await getGameDetail(gameId);
        if (cancelled) return;
        if (!detail) {
          setError("Game not found.");
        } else {
          setGame(detail);
        }
      } catch {
        if (!cancelled) setError("Failed to load game details.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [gameId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading game details...
        </span>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="space-y-4">
        <Link
          href="/dashboard/games"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Games
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error ?? "Game not found."}
        </div>
      </div>
    );
  }

  const chartData = buildTeamStatsChart(game.team_stats);
  const { home: homePlayers, away: awayPlayers } = groupPlayersByTeam(
    game.player_stats,
    game
  );

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/dashboard/games"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Games
      </Link>

      {/* Header: team names + score */}
      <div className="rounded-xl border bg-card p-6">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center sm:gap-8">
          <div className="text-center sm:text-right sm:flex-1">
            <p className="text-lg font-bold text-primary-900">
              {game.home_team ?? "Home"}
            </p>
            <p className="text-xs text-muted-foreground">Home</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-extrabold text-primary-900">
              {game.home_score ?? 0} – {game.away_score ?? 0}
            </p>
          </div>
          <div className="text-center sm:text-left sm:flex-1">
            <p className="text-lg font-bold text-primary-900">
              {game.away_team ?? "Away"}
            </p>
            <p className="text-xs text-muted-foreground">Away</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            {formatDate(game.date)}
          </span>
          {game.venue && (
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {game.venue}
            </span>
          )}
          {game.attendance != null && (
            <span className="inline-flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              {game.attendance.toLocaleString()} attendance
            </span>
          )}
        </div>
      </div>

      {/* Team stats comparison chart */}
      {chartData.length > 0 && (
        <div className="rounded-xl border bg-card p-6">
          <h3 className="text-lg font-semibold text-primary-900 mb-4">
            Team Stats Comparison
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                <YAxis
                  dataKey="stat"
                  type="category"
                  tick={{ fontSize: 12 }}
                  width={100}
                />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="home"
                  name={game.home_team ?? "Home"}
                  fill="#1a365d"
                  radius={[0, 4, 4, 0]}
                />
                <Bar
                  dataKey="away"
                  name={game.away_team ?? "Away"}
                  fill="#0d9488"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Player stats tables */}
      {(homePlayers.length > 0 || awayPlayers.length > 0) && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-primary-900">
            Player Stats
          </h3>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <PlayerStatsTable
              players={homePlayers}
              teamName={game.home_team}
            />
            <PlayerStatsTable
              players={awayPlayers}
              teamName={game.away_team}
            />
          </div>
        </div>
      )}

      {/* Events timeline */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary-900" />
          <h3 className="text-lg font-semibold text-primary-900">
            Match Events
          </h3>
        </div>
        <EventsTimeline events={game.events} />
      </div>
    </div>
  );
}
