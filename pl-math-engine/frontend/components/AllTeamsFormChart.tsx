"use client";

import { AllTeamsTimeSeries } from "@/lib/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: AllTeamsTimeSeries;
  currentTeam: string;
  mode: "form" | "position" | "points";
}

const TEAM_COLOR = "#7c3aed";
const OTHER_COLOR = "#d1d5db";

export default function AllTeamsFormChart({ data, currentTeam, mode }: Props) {
  const teamNames = Object.keys(data.teams);
  if (teamNames.length === 0) return null;

  // Build chart data: one entry per matchday with each team as a key
  const allMatchdays = new Set<number>();
  for (const snaps of Object.values(data.teams)) {
    for (const s of snaps) allMatchdays.add(s.matchday);
  }

  const sortedMatchdays = Array.from(allMatchdays).sort((a, b) => a - b);

  const chartData = sortedMatchdays.map((md) => {
    const point: Record<string, number> = { matchday: md };
    for (const [tn, snaps] of Object.entries(data.teams)) {
      const snap = snaps.find((s) => s.matchday === md);
      if (snap) {
        const key = tn.replace(/\s+/g, "_");
        if (mode === "form") point[key] = Math.round(snap.form * 100);
        else if (mode === "position") point[key] = snap.position;
        else point[key] = snap.cumulative_points;
      }
    }
    return point;
  });

  const labels = { form: "Form %", position: "Position", points: "Points" };
  const titles = {
    form: "Form Over Time",
    position: "Position Over Time",
    points: "Points Over Time",
  };

  const yDomain =
    mode === "position" ? [20, 1] : mode === "form" ? [0, 100] : undefined;

  return (
    <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">
        {titles[mode]}
      </h3>
      <div className="h-52 sm:h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <XAxis
              dataKey="matchday"
              tick={{ fontSize: 11 }}
              label={{
                value: "Matchday",
                position: "insideBottom",
                offset: -5,
                fontSize: 11,
              }}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              domain={yDomain}
              reversed={mode === "position"}
              label={{
                value: labels[mode],
                angle: -90,
                position: "insideLeft",
                fontSize: 11,
              }}
            />
            <Tooltip
              content={({ payload, label }) => {
                if (!payload || payload.length === 0) return null;
                // Find current team's entry
                const currentKey = currentTeam.replace(/\s+/g, "_");
                const currentEntry = payload.find(
                  (p) => p.dataKey === currentKey
                );
                if (!currentEntry) return null;
                const suffix =
                  mode === "form"
                    ? "%"
                    : mode === "position"
                      ? ordinal(Number(currentEntry.value))
                      : "";
                return (
                  <div className="bg-white shadow-lg rounded-lg px-3 py-2 border text-sm">
                    <p className="font-medium">Matchday {label}</p>
                    <p className="text-purple-700">
                      {currentTeam}: {currentEntry.value}
                      {suffix}
                    </p>
                  </div>
                );
              }}
            />
            {mode === "position" && (
              <>
                {/* CL zone */}
                <defs>
                  <linearGradient id="clZone" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity={0.1} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
              </>
            )}
            {/* Other teams — render first so current team is on top */}
            {teamNames
              .filter((tn) => tn !== currentTeam)
              .map((tn) => (
                <Line
                  key={tn}
                  type="monotone"
                  dataKey={tn.replace(/\s+/g, "_")}
                  stroke={OTHER_COLOR}
                  strokeWidth={1}
                  dot={false}
                  activeDot={false}
                  isAnimationActive={false}
                />
              ))}
            {/* Current team — rendered last */}
            <Line
              type="monotone"
              dataKey={currentTeam.replace(/\s+/g, "_")}
              stroke={TEAM_COLOR}
              strokeWidth={3}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ordinal(n: number): string {
  if (n === 1) return "st";
  if (n === 2) return "nd";
  if (n === 3) return "rd";
  return "th";
}
