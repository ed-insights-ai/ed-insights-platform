interface DeltaBadgeProps {
  value: number;
  unit?: string;
  baseline?: string;
  showIcon?: boolean;
}

export function DeltaBadge({
  value,
  unit = "",
  baseline,
  showIcon = true,
}: DeltaBadgeProps) {
  const isPositive = value > 0;
  const isNegative = value < 0;

  const className = isPositive
    ? "delta-positive"
    : isNegative
      ? "delta-negative"
      : "delta-neutral";

  const icon = isPositive ? "▲" : isNegative ? "▼" : "—";

  const formatted = isPositive
    ? `+${value}`
    : value === 0
      ? `±${value}`
      : `${value}`;

  return (
    <span className={className} title={baseline}>
      <span className="tabular-nums">
        {formatted}
        {unit}
      </span>
      {showIcon && <span>{icon}</span>}
    </span>
  );
}
