"use client";

import { useEffect, useState } from "react";
import { Prediction } from "@/lib/types";
import { getUpcomingPredictions, refreshPredictions } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";

export default function Home() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadPredictions() {
    try {
      setLoading(true);
      setError(null);
      const data = await getUpcomingPredictions();
      setPredictions(data);
    } catch (e) {
      setError(
        "Failed to load predictions. Make sure the backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    try {
      setRefreshing(true);
      setError(null);
      await refreshPredictions();
      await loadPredictions();
    } catch (e) {
      setError("Failed to refresh. Check your API key and backend logs.");
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadPredictions();
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Upcoming Predictions
          </h1>
          <p className="text-gray-500 mt-1">
            Premier League match predictions with AI-powered analysis
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {refreshing ? "Refreshing..." : "Refresh Data"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-20 text-gray-500">
          Loading predictions...
        </div>
      ) : predictions.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-500 text-lg">No upcoming predictions.</p>
          <p className="text-gray-400 text-sm mt-2">
            Click &quot;Refresh Data&quot; to fetch fixtures from API-Football
            and generate predictions.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {predictions.map((pred) => (
            <PredictionCard key={pred.fixture_id} prediction={pred} />
          ))}
        </div>
      )}
    </div>
  );
}
