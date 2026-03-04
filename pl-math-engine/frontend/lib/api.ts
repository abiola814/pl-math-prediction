import { Prediction, AccuracyData } from "./types";

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

export async function refreshPredictions(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/predictions/refresh`, {
    method: "POST",
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}
