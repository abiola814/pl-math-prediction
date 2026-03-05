"use client";

import { FormHistoryPoint } from "@/lib/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function FormChart({ data }: { data: FormHistoryPoint[] }) {
  if (data.length === 0) return null;

  return (
    <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">
        Season Progress
      </h3>
      <div className="h-48 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis
              dataKey="matchday"
              tick={{ fontSize: 11 }}
              label={{ value: "Matchday", position: "insideBottom", offset: -5, fontSize: 11 }}
            />
            <YAxis
              yAxisId="points"
              tick={{ fontSize: 11 }}
              label={{ value: "Points", angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <YAxis
              yAxisId="form"
              orientation="right"
              domain={[0, 1]}
              tick={{ fontSize: 11 }}
              label={{ value: "Form", angle: 90, position: "insideRight", fontSize: 11 }}
            />
            <Tooltip
              formatter={(value) => {
                if (value === undefined || value === null) return value;
                const num = typeof value === "number" ? value : parseFloat(String(value));
                return num < 1.1 ? `${Math.round(num * 100)}%` : num;
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line
              yAxisId="points"
              type="monotone"
              dataKey="cumulative_points"
              name="Points"
              stroke="#7c3aed"
              strokeWidth={2}
              dot={false}
            />
            <Line
              yAxisId="form"
              type="monotone"
              dataKey="form"
              name="Form"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              strokeDasharray="5 5"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
