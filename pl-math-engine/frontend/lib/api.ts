import {
  Prediction,
  AccuracyData,
  StandingOverview,
  TeamDashboard,
  FormHistoryPoint,
  ResultWithPrediction,
  AllTeamsTimeSeries,
  GoalFrequency,
  ScorelineFrequencyItem,
  TeamComparisonData,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getUpcomingPredictions(): Promise<Prediction[]> {
  return fetchAPI<Prediction[]>("/predictions/upcoming");
}

export async function getAccuracy(): Promise<AccuracyData> {
  return fetchAPI<AccuracyData>("/predictions/accuracy");
}

export async function getLastRefreshed(): Promise<string | null> {
  const data = await fetchAPI<{ last_refreshed: string | null }>("/predictions/last-refreshed");
  return data.last_refreshed;
}

export async function getStandingsOverview(): Promise<StandingOverview[]> {
  return fetchAPI<StandingOverview[]>("/standings/overview");
}

export async function getTeamDashboard(teamName: string): Promise<TeamDashboard> {
  return fetchAPI<TeamDashboard>(`/teams/${encodeURIComponent(teamName)}/dashboard`);
}

export async function getTeamFormHistory(teamName: string): Promise<FormHistoryPoint[]> {
  return fetchAPI<FormHistoryPoint[]>(`/teams/${encodeURIComponent(teamName)}/form-history`);
}

export async function getResults(limit: number = 20): Promise<ResultWithPrediction[]> {
  return fetchAPI<ResultWithPrediction[]>(`/results/?limit=${limit}`);
}

export async function getAllTeamsTimeSeries(): Promise<AllTeamsTimeSeries> {
  return fetchAPI<AllTeamsTimeSeries>("/teams/analysis/time-series");
}

export async function getGoalFrequency(teamName: string): Promise<GoalFrequency> {
  return fetchAPI<GoalFrequency>(`/teams/${encodeURIComponent(teamName)}/goal-frequency`);
}

export async function getScorelineFrequency(teamName: string): Promise<ScorelineFrequencyItem[]> {
  return fetchAPI<ScorelineFrequencyItem[]>(`/teams/${encodeURIComponent(teamName)}/scoreline-frequency`);
}

export async function getTeamComparison(teamName: string): Promise<TeamComparisonData> {
  return fetchAPI<TeamComparisonData>(`/teams/${encodeURIComponent(teamName)}/comparison`);
}
