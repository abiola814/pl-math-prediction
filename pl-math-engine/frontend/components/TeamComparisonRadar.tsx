"use client";

import { TeamComparisonData } from "@/lib/types";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface Props {
  data: TeamComparisonData;
}

export default function TeamComparisonRadar({ data }: Props) {
  if (!data || data.attributes.length === 0) return null;

  const chartData = data.attributes.map((attr) => ({
    attribute: attr.name,
    team: attr.team_value,
    avg: attr.avg_value,
  }));

  return (
    <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-1">
        Team Comparison
      </h3>
      <p className="text-xs text-gray-500 mb-3 sm:mb-4">
        {data.team_name} vs league average (0-100 scale)
      </p>
      <div className="h-64 sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
            <PolarGrid strokeDasharray="3 3" />
            <PolarAngleAxis
              dataKey="attribute"
              tick={{ fontSize: 10, fill: "#4b5563" }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fontSize: 9 }}
              tickCount={5}
            />
            <Tooltip
              formatter={(value) => `${value}`}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Radar
              name="League Avg"
              dataKey="avg"
              stroke="#9ca3af"
              fill="#9ca3af"
              fillOpacity={0.15}
              strokeWidth={1.5}
            />
            <Radar
              name={data.team_name}
              dataKey="team"
              stroke="#7c3aed"
              fill="#7c3aed"
              fillOpacity={0.25}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
