"use client";

import { useGender } from "@/context/GenderContext";
import { cn } from "@/lib/utils";

export function GenderSwitch() {
  const { gender, setGender } = useGender();

  return (
    <div className="flex rounded-lg bg-surface-muted p-0.5">
      <button
        onClick={() => setGender("men")}
        className={cn(
          "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
          gender === "men"
            ? "bg-data-primary text-white shadow-sm"
            : "text-slate-600 hover:text-slate-900"
        )}
      >
        <span
          className={cn(
            "inline-block h-1.5 w-1.5 rounded-full",
            gender === "men" ? "bg-white/80" : "bg-slate-400"
          )}
        />
        Men&apos;s
      </button>
      <button
        onClick={() => setGender("women")}
        className={cn(
          "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
          gender === "women"
            ? "bg-purple-600 text-white shadow-sm"
            : "text-slate-600 hover:text-slate-900"
        )}
      >
        <span
          className={cn(
            "inline-block h-1.5 w-1.5 rounded-full",
            gender === "women" ? "bg-white/80" : "bg-slate-400"
          )}
        />
        Women&apos;s
      </button>
    </div>
  );
}
