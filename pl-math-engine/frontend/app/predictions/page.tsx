"use client";

import { useEffect, useState } from "react";
import { Prediction } from "@/lib/types";
import { getUpcomingPredictions, getLastRefreshed } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const [data, refreshedAt] = await Promise.all([
          getUpcomingPredictions(),
          getLastRefreshed(),
        ]);
        setPredictions(data);
        setLastRefreshed(refreshedAt);
      } catch (e) {
        setError(
          "Failed to load predictions. Make sure the backend is running on port 8000."
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const formattedDate = lastRefreshed
    ? new Date(lastRefreshed).toLocaleString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div>
      <div className="mb-4 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          Upcoming Predictions
        </h1>
        <p className="text-gray-500 text-sm sm:text-base mt-1">
          AI-powered Premier League match predictions
        </p>
        {formattedDate && (
          <p className="text-gray-400 text-xs mt-1">
            Last updated: {formattedDate}
          </p>
        )}
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
            Predictions are generated automatically. Check back soon.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {predictions.map((pred) => (
            <PredictionCard key={pred.fixture_id} prediction={pred} />
          ))}
        </div>
      )}
    </div>
  );
}
