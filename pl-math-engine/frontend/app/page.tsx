"use client";

import { useEffect, useState } from "react";
import { StandingOverview } from "@/lib/types";
import { getStandingsOverview } from "@/lib/api";

function getPositionStyle(pos: number): string {
  if (pos <= 4) return "border-l-4 border-green-500 bg-green-50/50";
  if (pos <= 6) return "border-l-4 border-cyan-500 bg-cyan-50/50";
  if (pos >= 18) return "border-l-4 border-red-500 bg-red-50/50";
  return "border-l-4 border-transparent";
}

function RatingBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70
      ? "bg-green-500"
      : pct >= 40
        ? "bg-amber-500"
        : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden" title={`${label}: ${pct}%`}>
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-8">{pct}%</span>
    </div>
  );
}

export default function Home() {
  const [standings, setStandings] = useState<StandingOverview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getStandingsOverview();
        setStandings(data);
      } catch (e) {
        setError("Failed to load standings. Make sure the backend is running.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-20 text-gray-500">
        Loading standings...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20 text-red-500">{error}</div>
    );
  }

  if (standings.length === 0) {
    return (
      <div className="text-center py-20">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Premier League Standings
        </h1>
        <p className="text-gray-500">
          No standings data available. Try refreshing predictions first.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1 sm:mb-2">
        Premier League Standings
      </h1>
      <p className="text-gray-500 text-sm sm:text-base mb-4 sm:mb-6">
        Current season standings with team ratings and form
      </p>

      {/* Tip */}
      <div className="bg-purple-50 border border-purple-200 text-purple-800 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg mb-4 sm:mb-6 text-xs sm:text-sm">
        Tap any team to view their full dashboard with analysis — form, position history, goals distribution, scoreline frequency, and team comparison.
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 sm:gap-4 mb-3 sm:mb-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-green-500 rounded-sm" /> Champions League
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-cyan-500 rounded-sm" /> Europa League
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-red-500 rounded-sm" /> Relegation
        </span>
      </div>

      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs sm:text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-left w-8">#</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-left">Team</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-center">P</th>
                <th className="px-3 py-3 text-center hidden sm:table-cell">W</th>
                <th className="px-3 py-3 text-center hidden sm:table-cell">D</th>
                <th className="px-3 py-3 text-center hidden sm:table-cell">L</th>
                <th className="px-3 py-3 text-center hidden md:table-cell">GF</th>
                <th className="px-3 py-3 text-center hidden md:table-cell">GA</th>
                <th className="px-3 py-3 text-center hidden md:table-cell">GD</th>
                <th className="px-3 py-3 text-center font-bold">Pts</th>
                <th className="px-3 py-3 text-center hidden lg:table-cell">Rating</th>
                <th className="px-3 py-3 text-center hidden lg:table-cell">Form</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {standings.map((team) => (
                <tr
                  key={team.team_api_id}
                  className={`hover:bg-gray-50 transition-colors ${getPositionStyle(team.position)}`}
                >
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3 text-gray-500 font-medium">
                    {team.position}
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3">
                    <a
                      href={`/team/${encodeURIComponent(team.team_name)}`}
                      className="flex items-center gap-1.5 sm:gap-2 hover:text-purple-700 font-medium"
                    >
                      {team.logo_url && (
                        <img
                          src={team.logo_url}
                          alt={team.team_name}
                          className="w-5 h-5 sm:w-6 sm:h-6 object-contain flex-shrink-0"
                        />
                      )}
                      <span className="hidden sm:inline">{team.team_name}</span>
                      <span className="sm:hidden truncate max-w-[100px]">{team.team_name}</span>
                    </a>
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3 text-center">{team.played}</td>
                  <td className="px-3 py-3 text-center hidden sm:table-cell">{team.won}</td>
                  <td className="px-3 py-3 text-center hidden sm:table-cell">{team.drawn}</td>
                  <td className="px-3 py-3 text-center hidden sm:table-cell">{team.lost}</td>
                  <td className="px-3 py-3 text-center hidden md:table-cell">{team.goals_for}</td>
                  <td className="px-3 py-3 text-center hidden md:table-cell">{team.goals_against}</td>
                  <td className="px-3 py-3 text-center hidden md:table-cell font-medium">
                    <span className={team.goal_difference > 0 ? "text-green-600" : team.goal_difference < 0 ? "text-red-600" : "text-gray-500"}>
                      {team.goal_difference > 0 ? "+" : ""}{team.goal_difference}
                    </span>
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3 text-center font-bold text-gray-900">
                    {team.points}
                  </td>
                  <td className="px-3 py-3 hidden lg:table-cell">
                    <RatingBar value={team.rating} label="Rating" />
                  </td>
                  <td className="px-3 py-3 hidden lg:table-cell">
                    <RatingBar value={team.form} label="Form" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
