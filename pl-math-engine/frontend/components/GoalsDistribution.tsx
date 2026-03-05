"use client";

import { GoalFrequency } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface Props {
  data: GoalFrequency;
  teamName: string;
}

export default function GoalsDistribution({ data, teamName }: Props) {
  if (!data || data.goals.length === 0) return null;

  const scoredData = data.goals.map((g, i) => ({
    goals: g === 5 ? "5+" : String(g),
    team: data.team_scored_pct[i],
    avg: data.avg_scored_pct[i],
  }));

  const concededData = data.goals.map((g, i) => ({
    goals: g === 5 ? "5+" : String(g),
    team: data.team_conceded_pct[i],
    avg: data.avg_conceded_pct[i],
  }));

  return (
    <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">
        Goals Per Game Distribution
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* Goals Scored */}
        <div>
          <p className="text-sm font-medium text-gray-600 mb-2 text-center">
            Goals Scored
          </p>
          <div className="h-40 sm:h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoredData} barGap={2}>
                <XAxis
                  dataKey="goals"
                  tick={{ fontSize: 11 }}
                  label={{
                    value: "Goals",
                    position: "insideBottom",
                    offset: -5,
                    fontSize: 11,
                  }}
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
                <Bar
                  dataKey="team"
                  name={teamName}
                  fill="#22c55e"
                  fillOpacity={0.7}
                  radius={[2, 2, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Goals Conceded */}
        <div>
          <p className="text-sm font-medium text-gray-600 mb-2 text-center">
            Goals Conceded
          </p>
          <div className="h-40 sm:h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={concededData} barGap={2}>
                <XAxis
                  dataKey="goals"
                  tick={{ fontSize: 11 }}
                  label={{
                    value: "Goals",
                    position: "insideBottom",
                    offset: -5,
                    fontSize: 11,
                  }}
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
                <Bar
                  dataKey="team"
                  name={teamName}
                  fill="#ef4444"
                  fillOpacity={0.7}
                  radius={[2, 2, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
