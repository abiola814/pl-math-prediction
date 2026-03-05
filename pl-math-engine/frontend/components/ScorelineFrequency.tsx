"use client";

import { ScorelineFrequencyItem } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";

const outcomeColors: Record<string, string> = {
  W: "#22c55e",
  D: "#eab308",
  L: "#ef4444",
};

interface Props {
  data: ScorelineFrequencyItem[];
  teamName: string;
}

export default function ScorelineFrequency({ data, teamName }: Props) {
  if (!data || data.length === 0) return null;

  const chartData = data.map((d) => ({
    scoreline: d.scoreline,
    team: d.team_pct,
    avg: d.avg_pct,
    outcome: d.outcome,
  }));

  return (
    <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-1">
        Scoreline Frequency
      </h3>
      <p className="text-xs text-gray-500 mb-3 sm:mb-4">
        Most common scorelines from {teamName}&apos;s perspective
      </p>
      <div className="h-48 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barGap={1}>
            <XAxis
              dataKey="scoreline"
              tick={{ fontSize: 10 }}
              angle={-45}
              textAnchor="end"
              height={50}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              label={{
                value: "%",
                angle: -90,
                position: "insideLeft",
                fontSize: 11,
              }}
            />
            <Tooltip
              formatter={(value) => `${value}%`}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar
              dataKey="avg"
              name="League Avg"
              fill="#d1d5db"
              radius={[2, 2, 0, 0]}
            />
            <Bar dataKey="team" name={teamName} radius={[2, 2, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={outcomeColors[entry.outcome] || "#9ca3af"}
                  fillOpacity={0.75}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex gap-4 mt-3 justify-center text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-green-500 inline-block" />
          Win
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-yellow-500 inline-block" />
          Draw
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-red-500 inline-block" />
          Loss
        </span>
      </div>
    </div>
  );
}
