"use client";

import { LineChart, Line } from "recharts";

interface InlineSparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

export function InlineSparkline({
  data,
  width = 40,
  height = 16,
  color = "#0D9488",
  className,
}: InlineSparklineProps) {
  const chartData = data.map((v) => ({ v }));

  return (
    <div className={className}>
      <LineChart width={width} height={height} data={chartData}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </div>
  );
}
