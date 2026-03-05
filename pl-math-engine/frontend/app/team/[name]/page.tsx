"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  TeamDashboard,
  FormHistoryPoint,
  AllTeamsTimeSeries,
  GoalFrequency,
  ScorelineFrequencyItem,
  TeamComparisonData,
} from "@/lib/types";
import {
  getTeamDashboard,
  getTeamFormHistory,
  getAllTeamsTimeSeries,
  getGoalFrequency,
  getScorelineFrequency,
  getTeamComparison,
} from "@/lib/api";
import FormTiles from "@/components/FormTiles";
import GoalsAnalysis from "@/components/GoalsAnalysis";
import FormChart from "@/components/FormChart";
import GoalsChart from "@/components/GoalsChart";
import AllTeamsFormChart from "@/components/AllTeamsFormChart";
import GoalsDistribution from "@/components/GoalsDistribution";
import ScorelineFrequency from "@/components/ScorelineFrequency";
import TeamComparisonRadar from "@/components/TeamComparisonRadar";

const resultColors: Record<string, string> = {
  W: "text-green-600",
  D: "text-gray-500",
  L: "text-red-600",
};

const resultBgColors: Record<string, string> = {
  W: "bg-green-100",
  D: "bg-gray-100",
  L: "bg-red-100",
};

type TabKey = "overview" | "analysis" | "fixtures";

const tabs: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "analysis", label: "Analysis" },
  { key: "fixtures", label: "Fixtures" },
];

function ordinal(n: number): string {
  if (n === 1) return "st";
  if (n === 2) return "nd";
  if (n === 3) return "rd";
  return "th";
}

export default function TeamDashboardPage() {
  const params = useParams();
  const teamName = decodeURIComponent(params.name as string);

  const [dashboard, setDashboard] = useState<TeamDashboard | null>(null);
  const [formHistory, setFormHistory] = useState<FormHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  // Analysis data — loaded lazily when Analysis tab is activated
  const [timeSeries, setTimeSeries] = useState<AllTeamsTimeSeries | null>(null);
  const [goalFreq, setGoalFreq] = useState<GoalFrequency | null>(null);
  const [scorelines, setScorelines] = useState<ScorelineFrequencyItem[] | null>(null);
  const [comparison, setComparison] = useState<TeamComparisonData | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [dashData, formData] = await Promise.all([
          getTeamDashboard(teamName),
          getTeamFormHistory(teamName),
        ]);
        setDashboard(dashData);
        setFormHistory(formData);
      } catch (e) {
        setError(`Failed to load data for ${teamName}`);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [teamName]);

  // Lazy-load analysis data when tab becomes active
  useEffect(() => {
    if (activeTab !== "analysis" || timeSeries) return;
    async function loadAnalysis() {
      setAnalysisLoading(true);
      try {
        const [ts, gf, sl, cmp] = await Promise.all([
          getAllTeamsTimeSeries(),
          getGoalFrequency(teamName),
          getScorelineFrequency(teamName),
          getTeamComparison(teamName),
        ]);
        setTimeSeries(ts);
        setGoalFreq(gf);
        setScorelines(sl);
        setComparison(cmp);
      } catch {
        // Analysis data is optional — silently degrade
      } finally {
        setAnalysisLoading(false);
      }
    }
    loadAnalysis();
  }, [activeTab, teamName, timeSeries]);

  if (loading) {
    return (
      <div className="text-center py-20 text-gray-500">
        Loading {teamName}...
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="text-center py-20 text-red-500">
        {error || "Team not found"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <a
        href="/"
        className="text-sm text-purple-600 hover:text-purple-800"
      >
        &larr; Back to Standings
      </a>

      {/* ═══ TOP ROW: Position Circle + Mini Table + Form ═══ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Position Circle */}
        <div className="bg-white rounded-xl shadow-md p-4 sm:p-6 flex flex-col items-center justify-center">
          <div className="relative">
            <svg viewBox="0 0 200 200" className="w-32 h-32 sm:w-44 sm:h-44">
              <circle cx="100" cy="100" r="95" fill="#7c3aed" opacity="0.1" />
              <circle cx="100" cy="100" r="75" fill="#7c3aed" opacity="0.2" />
              <circle cx="100" cy="100" r="55" fill="#7c3aed" opacity="0.35" />
              <text
                x="100"
                y="108"
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="64"
                fontWeight="900"
                fill="#7c3aed"
              >
                {dashboard.position}
              </text>
            </svg>
          </div>
          <div className="flex items-center gap-2 mt-2">
            {dashboard.logo_url && (
              <img
                src={dashboard.logo_url}
                alt={dashboard.team_name}
                className="w-6 h-6 sm:w-8 sm:h-8 object-contain"
              />
            )}
            <h1 className="text-lg sm:text-xl font-bold text-gray-900">
              {dashboard.team_name}
            </h1>
          </div>
          <div className="flex gap-3 sm:gap-4 mt-2 text-xs sm:text-sm text-gray-500">
            <span><strong className="text-gray-700">{dashboard.points}</strong> pts</span>
            <span><strong className="text-gray-700">{dashboard.goal_difference > 0 ? "+" : ""}{dashboard.goal_difference}</strong> GD</span>
            <span><strong className="text-gray-700">{dashboard.won}</strong>W <strong className="text-gray-700">{dashboard.drawn}</strong>D <strong className="text-gray-700">{dashboard.lost}</strong>L</span>
          </div>
        </div>

        {/* Mini League Table */}
        <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
          <h3 className="text-sm font-semibold text-gray-600 uppercase mb-3">
            League Table
          </h3>
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-400 uppercase">
              <tr>
                <th className="text-left py-1 w-6">#</th>
                <th className="text-left py-1">Team</th>
                <th className="text-center py-1">GD</th>
                <th className="text-right py-1">Pts</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.mini_table.map((row) => (
                <tr
                  key={row.team_name}
                  className={`${
                    row.is_current
                      ? "bg-purple-100 font-bold text-purple-900"
                      : "text-gray-700"
                  }`}
                >
                  <td className="py-1.5 text-gray-400 text-xs">{row.position}</td>
                  <td className="py-1.5">
                    <a
                      href={`/team/${encodeURIComponent(row.team_name)}`}
                      className="flex items-center gap-1.5 hover:text-purple-700"
                    >
                      {row.logo_url && (
                        <img
                          src={row.logo_url}
                          alt=""
                          className="w-4 h-4 object-contain"
                        />
                      )}
                      <span className="truncate text-xs">
                        {row.team_name}
                      </span>
                    </a>
                  </td>
                  <td className="py-1.5 text-center text-xs">
                    <span className={row.goal_difference > 0 ? "text-green-600" : row.goal_difference < 0 ? "text-red-600" : ""}>
                      {row.goal_difference > 0 ? "+" : ""}{row.goal_difference}
                    </span>
                  </td>
                  <td className="py-1.5 text-right font-semibold text-xs">
                    {row.points}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Metrics + Form */}
        <div className="bg-white rounded-xl shadow-md p-4 sm:p-6 space-y-4 md:col-span-2 lg:col-span-1">
          <h3 className="text-sm font-semibold text-gray-600 uppercase mb-1">
            Team Metrics
          </h3>
          <div className="grid grid-cols-3 gap-2 sm:gap-3">
            <div className="text-center p-2 sm:p-3 bg-purple-50 rounded-lg">
              <p className="text-xl sm:text-2xl font-bold text-purple-700">
                {Math.round(dashboard.rating * 100)}%
              </p>
              <p className="text-[10px] sm:text-xs text-gray-500">Rating</p>
            </div>
            <div className="text-center p-2 sm:p-3 bg-amber-50 rounded-lg">
              <p className="text-xl sm:text-2xl font-bold text-amber-700">
                {Math.round(dashboard.form * 100)}%
              </p>
              <p className="text-[10px] sm:text-xs text-gray-500">Form</p>
            </div>
            <div className="text-center p-2 sm:p-3 bg-blue-50 rounded-lg">
              <p className="text-xl sm:text-2xl font-bold text-blue-700">
                {dashboard.home_advantage > 0 ? "+" : ""}
                {Math.round(dashboard.home_advantage * 100)}%
              </p>
              <p className="text-[10px] sm:text-xs text-gray-500">Home Adv.</p>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">
              Recent Form
            </p>
            <FormTiles results={dashboard.recent_form} />
          </div>
        </div>
      </div>

      {/* ═══ TAB NAVIGATION ═══ */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4 sm:gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-2 sm:pb-3 text-xs sm:text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-purple-700 text-purple-700"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* ═══ OVERVIEW TAB ═══ */}
      {activeTab === "overview" && (
        <>
          {/* Next match + H2H */}
          {dashboard.next_fixture && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              {/* Next match card */}
              <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">
                  Next Game:{" "}
                  <span className="text-purple-700">
                    {dashboard.next_fixture.home_team === teamName
                      ? dashboard.next_fixture.away_team
                      : dashboard.next_fixture.home_team}
                  </span>
                  <span className="text-sm font-normal text-gray-500 ml-2">
                    ({dashboard.next_fixture.home_team === teamName ? "Home" : "Away"})
                  </span>
                </h3>

                <div className="flex items-center gap-4 sm:gap-6">
                  {dashboard.next_opponent_info && (
                    <div className="text-center flex-shrink-0">
                      <div className="relative inline-block">
                        <svg viewBox="0 0 120 120" className="w-16 h-16 sm:w-24 sm:h-24">
                          <circle cx="60" cy="60" r="55" fill="#f3f4f6" />
                          <circle cx="60" cy="60" r="42" fill="#e5e7eb" />
                          <text
                            x="60"
                            y="65"
                            textAnchor="middle"
                            dominantBaseline="middle"
                            fontSize="36"
                            fontWeight="900"
                            fill="#374151"
                          >
                            {dashboard.next_opponent_info.position}
                          </text>
                        </svg>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {dashboard.next_opponent_info.position}{ordinal(dashboard.next_opponent_info.position)} place
                      </p>
                      <p className="text-sm font-semibold text-green-600 mt-1">
                        Form: {Math.round(dashboard.next_opponent_info.form * 100)}%
                      </p>
                    </div>
                  )}

                  <div className="flex-1">
                    <p className="font-medium text-gray-900">
                      {dashboard.next_fixture.home_team} vs {dashboard.next_fixture.away_team}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(dashboard.next_fixture.date).toLocaleDateString(
                        "en-GB",
                        {
                          weekday: "long",
                          day: "numeric",
                          month: "long",
                          hour: "2-digit",
                          minute: "2-digit",
                        }
                      )}
                    </p>
                    {dashboard.next_fixture.matchday && (
                      <p className="text-xs text-gray-400 mt-1">
                        Matchday {dashboard.next_fixture.matchday}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* H2H */}
              <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3">
                  Head-to-Head
                  {dashboard.h2h_vs_next.length > 0 && (
                    <span className="text-sm font-normal text-gray-500 ml-2">
                      ({dashboard.h2h_vs_next.length} matches)
                    </span>
                  )}
                </h3>
                {dashboard.h2h_vs_next.length > 0 ? (
                  <div className="space-y-1.5">
                    {dashboard.h2h_vs_next.slice(-6).map((h, i) => (
                      <div
                        key={i}
                        className={`flex items-center justify-between px-3 py-2 rounded text-sm ${resultBgColors[h.result]}`}
                      >
                        <span className="text-gray-600">
                          <span className={`inline-block w-5 h-5 leading-5 rounded text-xs font-bold text-white text-center mr-2 ${
                            h.is_home ? "bg-green-500" : "bg-blue-500"
                          }`}>
                            {h.is_home ? "H" : "A"}
                          </span>
                          vs {h.opponent}
                        </span>
                        <span className={`font-semibold ${resultColors[h.result]}`}>
                          {h.goals_for}-{h.goals_against}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-sm">No head-to-head matches found</p>
                )}
              </div>
            </div>
          )}

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            <FormChart data={formHistory} />
            <GoalsChart data={formHistory} />
          </div>

          {/* Goals Analysis */}
          <GoalsAnalysis data={dashboard.goals_analysis} />

          {/* Injuries */}
          {dashboard.injuries.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3">
                Injuries
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                    <tr>
                      <th className="px-3 py-2 text-left">Player</th>
                      <th className="px-3 py-2 text-left">Position</th>
                      <th className="px-3 py-2 text-left">Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {dashboard.injuries.map((inj, i) => (
                      <tr key={i}>
                        <td className="px-3 py-2 font-medium">{inj.player_name}</td>
                        <td className="px-3 py-2 text-gray-500">
                          {inj.player_position || "-"}
                        </td>
                        <td className="px-3 py-2 text-gray-500">
                          {inj.reason || "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* ═══ ANALYSIS TAB ═══ */}
      {activeTab === "analysis" && (
        <>
          {analysisLoading ? (
            <div className="text-center py-16 text-gray-500">
              Loading analysis data...
            </div>
          ) : (
            <div className="space-y-6">
              {/* Form / Position / Points over time (all 20 teams) */}
              {timeSeries && (
                <>
                  <AllTeamsFormChart
                    data={timeSeries}
                    currentTeam={teamName}
                    mode="form"
                  />
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    <AllTeamsFormChart
                      data={timeSeries}
                      currentTeam={teamName}
                      mode="position"
                    />
                    <AllTeamsFormChart
                      data={timeSeries}
                      currentTeam={teamName}
                      mode="points"
                    />
                  </div>
                </>
              )}

              {/* Goals Distribution + Scoreline Frequency */}
              {goalFreq && (
                <GoalsDistribution data={goalFreq} teamName={teamName} />
              )}
              {scorelines && (
                <ScorelineFrequency data={scorelines} teamName={teamName} />
              )}

              {/* Spider/Radar Chart */}
              {comparison && <TeamComparisonRadar data={comparison} />}
            </div>
          )}
        </>
      )}

      {/* ═══ FIXTURES TAB ═══ */}
      {activeTab === "fixtures" && (
        <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3">
            Season Fixtures
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs sm:text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                <tr>
                  <th className="px-1.5 sm:px-3 py-2 text-left">MD</th>
                  <th className="px-1.5 sm:px-3 py-2 text-left">Date</th>
                  <th className="px-1.5 sm:px-3 py-2 text-center">H/A</th>
                  <th className="px-1.5 sm:px-3 py-2 text-left">Opponent</th>
                  <th className="px-1.5 sm:px-3 py-2 text-center">Score</th>
                  <th className="px-1.5 sm:px-3 py-2 text-center">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {dashboard.season_fixtures.map((fix, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-1.5 sm:px-3 py-2 text-gray-400">{fix.matchday || "-"}</td>
                    <td className="px-1.5 sm:px-3 py-2 text-gray-600">
                      {new Date(fix.date).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "short",
                      })}
                    </td>
                    <td className="px-1.5 sm:px-3 py-2 text-center">
                      <span
                        className={`text-xs px-1.5 sm:px-2 py-0.5 rounded ${
                          fix.is_home
                            ? "bg-green-100 text-green-700"
                            : "bg-blue-100 text-blue-700"
                        }`}
                      >
                        {fix.is_home ? "H" : "A"}
                      </span>
                    </td>
                    <td className="px-1.5 sm:px-3 py-2 font-medium">
                      <a
                        href={`/team/${encodeURIComponent(fix.opponent)}`}
                        className="hover:text-purple-700 truncate block max-w-[100px] sm:max-w-none"
                      >
                        {fix.opponent}
                      </a>
                    </td>
                    <td className="px-1.5 sm:px-3 py-2 text-center font-medium">
                      {fix.goals_for}-{fix.goals_against}
                    </td>
                    <td className="px-1.5 sm:px-3 py-2 text-center">
                      <span
                        className={`inline-block w-6 h-6 leading-6 rounded text-xs font-bold text-white ${
                          fix.result === "W"
                            ? "bg-green-500"
                            : fix.result === "D"
                              ? "bg-gray-400"
                              : "bg-red-500"
                        }`}
                      >
                        {fix.result}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
