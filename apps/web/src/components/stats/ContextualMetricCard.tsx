import { cn } from "@/lib/utils";
import { DeltaBadge } from "./DeltaBadge";
import { InlineSparkline } from "./InlineSparkline";

interface ContextualMetricCardProps {
  label: string;
  value: string | number;
  delta?: number;
  deltaUnit?: string;
  baseline?: string;
  sparklineData?: number[];
  className?: string;
}

export function ContextualMetricCard({
  label,
  value,
  delta,
  deltaUnit,
  baseline,
  sparklineData,
  className,
}: ContextualMetricCardProps) {
  return (
    <div className={cn("bento-card p-5", className)}>
      <p className="stat-label">{label}</p>
      <p className="stat-value mt-1">{value}</p>
      {delta !== undefined && (
        <div className="mt-1">
          <DeltaBadge value={delta} unit={deltaUnit} baseline={baseline} />
        </div>
      )}
      {baseline && <p className="mt-1 text-xs text-slate-400">{baseline}</p>}
      {sparklineData && sparklineData.length > 0 && (
        <InlineSparkline data={sparklineData} className="mt-2" />
      )}
    </div>
  );
}
