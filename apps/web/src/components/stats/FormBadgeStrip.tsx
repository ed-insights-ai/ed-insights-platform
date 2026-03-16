import Link from "next/link";
import { cn } from "@/lib/utils";

interface FormResult {
  result: "W" | "L" | "D";
  gameId?: number;
}

interface FormBadgeStripProps {
  results: FormResult[];
  maxDisplay?: number;
  size?: "sm" | "md";
}

const colorMap = {
  W: "bg-emerald-500 text-white",
  L: "bg-rose-500 text-white",
  D: "bg-amber-500 text-white",
} as const;

const sizeMap = {
  sm: "w-6 h-6",
  md: "w-7 h-7",
} as const;

export function FormBadgeStrip({
  results,
  maxDisplay = 5,
  size = "md",
}: FormBadgeStripProps) {
  const visible = results.slice(-maxDisplay);

  return (
    <div className="flex gap-1">
      {visible.map((r, i) => {
        const badgeClass = cn(
          "rounded-md font-bold text-xs flex items-center justify-center",
          colorMap[r.result],
          sizeMap[size],
        );

        if (r.gameId) {
          return (
            <Link
              key={i}
              href={`/dashboard/games/${r.gameId}`}
              className={badgeClass}
            >
              {r.result}
            </Link>
          );
        }

        return (
          <span key={i} className={badgeClass}>
            {r.result}
          </span>
        );
      })}
    </div>
  );
}
