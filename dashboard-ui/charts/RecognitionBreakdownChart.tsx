"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = ["#f59e0b", "#2563eb", "#10b981", "#94a3b8"];

export interface BreakdownPoint {
  label: string;
  count: number;
}

interface RecognitionBreakdownChartProps {
  data: BreakdownPoint[];
  height?: number;
}

export function RecognitionBreakdownChart({
  data,
  height = 240,
}: RecognitionBreakdownChartProps) {
  if (data.length === 0 || data.every((d) => d.count === 0)) {
    return (
      <p className="py-8 text-center text-sm text-slate-500">
        No recognitions in the last 24h
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="label"
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={2}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            borderRadius: 8,
            border: "1px solid #e2e8f0",
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
