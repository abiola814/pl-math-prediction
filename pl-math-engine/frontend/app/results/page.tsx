"use client";

import { useEffect, useState } from "react";
import { ResultWithPrediction } from "@/lib/types";
import { getResults } from "@/lib/api";

function MarketBadge({
  label,
  confidence,
  correct,
}: {
  label: string;
  confidence: number;
  correct: boolean | null;
}) {
  const bg =
    correct === true
      ? "bg-green-100 text-green-800"
      : correct === false
        ? "bg-red-100 text-red-800"
        : "bg-gray-100 text-gray-600";

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${bg}`}
    >
      {label} ({Math.round(confidence * 100)}%)
    </span>
  );
}

export default function ResultsPage() {
  const [results, setResults] = useState<ResultWithPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getResults(50);
        setResults(data);
      } catch (e) {
        setError("Failed to load results. Make sure the backend is running.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-20 text-gray-500">
        Loading results...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20 text-red-500">{error}</div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-20">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Match Results
        </h1>
        <p className="text-gray-500">
          No completed matches found. Results will appear here after matches are
          played.
        </p>
      </div>
    );
  }

  // Compute summary stats
  const withPredictions = results.filter((r) => r.predicted_home_goals !== null);
  const allMarkets = withPredictions.flatMap((r) => r.markets || []);
  const evaluatedMarkets = allMarkets.filter((m) => m.correct !== null);
  const correctMarkets = evaluatedMarkets.filter((m) => m.correct === true);
  const marketHitRate = evaluatedMarkets.length > 0
    ? Math.round((correctMarkets.length / evaluatedMarkets.length) * 100)
    : 0;

  return (
    <div>
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1 sm:mb-2">Match Results</h1>
      <p className="text-gray-500 text-sm sm:text-base mb-4 sm:mb-6">
        Recent completed matches with market pick performance
      </p>

      {/* Summary */}
      {withPredictions.length > 0 && (
        <div className="mb-4 sm:mb-6">
          <div className="bg-white rounded-xl shadow-md p-4 sm:p-6 text-center max-w-xs mx-auto">
            <p className="text-2xl sm:text-3xl font-bold text-blue-600">
              {marketHitRate}%
            </p>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">Market Hit Rate</p>
            <p className="text-[10px] text-gray-400 mt-1">
              {correctMarkets.length}/{evaluatedMarkets.length} picks correct
            </p>
          </div>
        </div>
      )}

      {/* Results table */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs sm:text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-left">Date</th>
                <th className="px-3 py-3 text-left hidden sm:table-cell">MD</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-left">Match</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-center">Score</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-left">Markets</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {results.map((r) => (
                <tr key={r.fixture_api_id} className="hover:bg-gray-50">
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3 text-gray-500 text-xs">
                    {new Date(r.date).toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "short",
                    })}
                  </td>
                  <td className="px-3 py-3 text-gray-400 hidden sm:table-cell">
                    {r.matchday || "-"}
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3">
                    <span className="font-medium">{r.home_team}</span>
                    <span className="text-gray-400 mx-0.5 sm:mx-1">vs</span>
                    <span className="font-medium">{r.away_team}</span>
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3 text-center font-bold text-gray-900">
                    {r.actual_home_goals}-{r.actual_away_goals}
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3">
                    {r.markets && r.markets.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {r.markets.map((m, i) => (
                          <MarketBadge key={i} label={m.label} confidence={m.confidence} correct={m.correct} />
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400 text-xs">-</span>
                    )}
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
