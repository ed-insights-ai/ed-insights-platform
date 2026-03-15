"use client";

import { useCallback, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type SortingState,
  type ColumnDef,
} from "@tanstack/react-table";
import { ArrowUpDown, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { SchoolSeasonSelector } from "@/components/SchoolSeasonSelector";
import { getPlayerLeaderboard } from "@/lib/api";
import type { PlayerLeaderboard } from "@/lib/api";

const SORT_FIELD_MAP: Record<string, string> = {
  total_goals: "goals",
  total_assists: "assists",
  total_shots: "shots",
  total_minutes: "minutes",
};

const PAGE_SIZE = 20;

const columns: ColumnDef<PlayerLeaderboard>[] = [
  {
    id: "rank",
    header: "#",
    cell: ({ row, table }) => {
      const offset =
        (table.options.meta as { offset: number } | undefined)?.offset ?? 0;
      return offset + row.index + 1;
    },
    enableSorting: false,
  },
  {
    accessorKey: "player_name",
    header: "Player",
    enableSorting: false,
  },
  {
    accessorKey: "games_played",
    header: "GP",
    enableSorting: false,
  },
  {
    accessorKey: "total_goals",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-primary-900 dark:hover:text-white"
        onClick={() => column.toggleSorting(column.getIsSorted() !== "desc")}
      >
        Goals <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
  },
  {
    accessorKey: "total_assists",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-primary-900 dark:hover:text-white"
        onClick={() => column.toggleSorting(column.getIsSorted() !== "desc")}
      >
        Assists <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
  },
  {
    accessorKey: "total_shots",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-primary-900 dark:hover:text-white"
        onClick={() => column.toggleSorting(column.getIsSorted() !== "desc")}
      >
        Shots <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
  },
  {
    accessorKey: "total_shots_on_goal",
    header: "SOG",
    enableSorting: false,
  },
  {
    accessorKey: "total_minutes",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-primary-900 dark:hover:text-white"
        onClick={() => column.toggleSorting(column.getIsSorted() !== "desc")}
      >
        Minutes <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
  },
];

export default function PlayersPage() {
  const [data, setData] = useState<PlayerLeaderboard[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [school, setSchool] = useState("");
  const [season, setSeason] = useState(2025);
  const [sorting, setSorting] = useState<SortingState>([
    { id: "total_goals", desc: true },
  ]);

  const fetchData = useCallback(
    async (abbr: string, yr: number, sort: SortingState, off: number) => {
      setLoading(true);
      setError(null);
      try {
        const sortField =
          sort.length > 0 ? SORT_FIELD_MAP[sort[0].id] ?? "goals" : "goals";
        const res = await getPlayerLeaderboard(
          abbr,
          yr,
          sortField,
          PAGE_SIZE,
          off
        );
        setData(res.items);
        setTotal(res.total);
      } catch {
        setError("Failed to load player data.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleSelectionChange = useCallback(
    (abbr: string, yr: number, _schoolName: string) => {
      setSchool(abbr);
      setSeason(yr);
      setOffset(0);
      fetchData(abbr, yr, sorting, 0);
    },
    [fetchData, sorting]
  );

  const handleSortingChange = (updater: SortingState | ((old: SortingState) => SortingState)) => {
    const newSorting = typeof updater === "function" ? updater(sorting) : updater;
    setSorting(newSorting);
    setOffset(0);
    if (school) fetchData(school, season, newSorting, 0);
  };

  const handlePageChange = (newOffset: number) => {
    setOffset(newOffset);
    if (school) fetchData(school, season, sorting, newOffset);
  };

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: handleSortingChange,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    meta: { offset },
  });

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-primary-900">
            Player Leaderboard
          </h2>
          <p className="text-muted-foreground">
            Individual athlete statistics ranked by performance
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
          <span className="ml-3 text-muted-foreground">Loading players...</span>
        </div>
      ) : data.length === 0 && school ? (
        <div className="rounded-xl border bg-card p-12 text-center">
          <p className="text-muted-foreground">
            No player data available for this selection.
          </p>
        </div>
      ) : data.length > 0 ? (
        <div className="rounded-xl border bg-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr
                    key={headerGroup.id}
                    className="border-b bg-gray-50 dark:bg-gray-800/50"
                  >
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="px-4 py-3 text-primary-900 dark:text-gray-200"
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3">
              <span className="text-sm text-muted-foreground">
                Showing {offset + 1}&ndash;{Math.min(offset + PAGE_SIZE, total)}{" "}
                of {total} players
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(offset - PAGE_SIZE)}
                  disabled={offset === 0}
                  className="rounded-lg border px-3 py-1.5 text-sm font-medium disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-muted-foreground">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => handlePageChange(offset + PAGE_SIZE)}
                  disabled={offset + PAGE_SIZE >= total}
                  className="rounded-lg border px-3 py-1.5 text-sm font-medium disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
