"use client";

import { useEffect, useState } from "react";
import { AccuracyData } from "@/lib/types";
import { getAccuracy } from "@/lib/api";

function AccuracyStat({
  label,
  value,
  color,
}: {
  label: string;
  value: number | null;
  color: string;
}) {
  if (value === null || value === undefined) return null;

  return (
    <div className="bg-white rounded-xl shadow-md p-6 text-center">
      <p className="text-sm text-gray-500 mb-2">{label}</p>
      <p className={`text-4xl font-bold ${color}`}>{value}%</p>
    </div>
  );
}

export default function AccuracyPage() {
  const [accuracy, setAccuracy] = useState<AccuracyData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getAccuracy();
        setAccuracy(data);
      } catch {
        // No data yet
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-20 text-gray-500">
        Loading accuracy data...
      </div>
    );
  }

  if (!accuracy || accuracy.total_predictions === 0) {
    return (
      <div className="text-center py-20">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Prediction Accuracy
        </h1>
        <p className="text-gray-500">
          No completed predictions yet. Accuracy tracking will begin once
          matches finish and results are compared against predictions.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Prediction Accuracy
      </h1>
      <p className="text-gray-500 mb-8">
        Based on {accuracy.total_predictions} completed predictions
      </p>

      {/* Game of the Week — Best Pick accuracy */}
      {accuracy.best_pick_accuracy !== null && accuracy.best_pick_accuracy !== undefined && (
        <div className="bg-gradient-to-r from-purple-700 to-purple-900 rounded-xl shadow-lg p-6 text-center mb-8">
          <p className="text-sm text-purple-300 mb-1">Game of the Week — Best Pick</p>
          <p className="text-5xl font-bold text-white">{accuracy.best_pick_accuracy}%</p>
          <p className="text-xs text-purple-300 mt-2">
            Highest-confidence pick per match hit rate
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <AccuracyStat
          label="Exact Score"
          value={accuracy.exact_score_accuracy}
          color="text-purple-700"
        />
        <AccuracyStat
          label="Correct Result (H/D/A)"
          value={accuracy.result_accuracy}
          color="text-green-700"
        />
        <AccuracyStat
          label="Over/Under"
          value={accuracy.over_under_accuracy}
          color="text-blue-700"
        />
        <AccuracyStat
          label="BTTS"
          value={accuracy.btts_accuracy}
          color="text-amber-700"
        />
        <AccuracyStat
          label="Corner Line"
          value={accuracy.corner_line_accuracy}
          color="text-orange-700"
        />
        <AccuracyStat
          label="Card Line"
          value={accuracy.card_line_accuracy}
          color="text-red-700"
        />
      </div>

      <div className="mt-10 bg-white rounded-xl shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          How Accuracy Is Calculated
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <p className="font-medium text-gray-800">Best Pick (Game of the Week)</p>
            <p>
              For each match, the system selects the single highest-confidence
              market pick (goals O/U, BTTS, home/away goals, corners, or
              cards) and checks if it was correct.
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">Exact Score</p>
            <p>
              Predicted scoreline matches the actual result exactly (e.g.,
              predicted 2-1, actual 2-1).{" "}
              <span className="font-medium text-purple-700">
                ~10% is typical — even the best models rarely exceed this.
              </span>{" "}
              The real value is in correct result and market picks.
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">Correct Result</p>
            <p>
              Predicted the right outcome: Home win, Draw, or Away win
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">Over/Under</p>
            <p>
              The recommended over/under goals line was correct
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">BTTS</p>
            <p>
              Both Teams To Score prediction was correct
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">Corner Line</p>
            <p>
              The recommended corner over/under line was correct
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">Card Line</p>
            <p>
              The recommended yellow card over/under line was correct
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
