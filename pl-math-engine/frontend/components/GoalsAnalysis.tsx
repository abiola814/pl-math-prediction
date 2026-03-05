"use client";

import { GoalsAnalysis as GoalsAnalysisType } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function GoalsAnalysis({ data }: { data: GoalsAnalysisType }) {
  const chartData = [
    {
      name: "Home",
      Scored: data.avg_scored_home,
      Conceded: data.avg_conceded_home,
    },
    {
      name: "Away",
      Scored: data.avg_scored_away,
      Conceded: data.avg_conceded_away,
    },
    {
      name: "Overall",
      Scored: data.avg_scored,
      Conceded: data.avg_conceded,
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">
        Goals Analysis
      </h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div className="text-center">
          <p className="text-xl sm:text-2xl font-bold text-green-600">{data.avg_scored}</p>
          <p className="text-xs text-gray-500">Avg Scored</p>
        </div>
        <div className="text-center">
          <p className="text-xl sm:text-2xl font-bold text-red-600">{data.avg_conceded}</p>
          <p className="text-xs text-gray-500">Avg Conceded</p>
        </div>
        <div className="text-center">
          <p className="text-xl sm:text-2xl font-bold text-blue-600">{data.clean_sheets}</p>
          <p className="text-xs text-gray-500">Clean Sheets</p>
        </div>
        <div className="text-center">
          <p className="text-xl sm:text-2xl font-bold text-amber-600">{data.failed_to_score}</p>
          <p className="text-xs text-gray-500">Failed to Score</p>
        </div>
      </div>

      <div className="h-40 sm:h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Scored" fill="#22c55e" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Conceded" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-gray-400 mt-2 text-center">
        Based on {data.total_matches} matches this season
      </p>
    </div>
  );
}
