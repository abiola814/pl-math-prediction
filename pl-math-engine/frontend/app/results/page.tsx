"use client";

import { useEffect, useState } from "react";
import { ResultWithPrediction } from "@/lib/types";
import { getResults } from "@/lib/api";

function AccuracyBadge({
  scoreCorrect,
  resultCorrect,
}: {
  scoreCorrect: boolean;
  resultCorrect: boolean;
}) {
  if (scoreCorrect) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        Exact
      </span>
    );
  }
  if (resultCorrect) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
        Result
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
      Wrong
    </span>
  );
}

const resultLabels: Record<string, string> = {
  H: "Home",
  D: "Draw",
  A: "Away",
};

const resultBadgeColors: Record<string, string> = {
  H: "bg-blue-100 text-blue-800",
  D: "bg-gray-100 text-gray-700",
  A: "bg-orange-100 text-orange-800",
};

function ResultBadge({
  predicted,
  actual,
}: {
  predicted: string | null;
  actual: string;
}) {
  if (!predicted) return <span className="text-gray-400 text-xs">-</span>;

  const isCorrect = predicted === actual;
  const border = isCorrect ? "ring-2 ring-green-400" : "ring-2 ring-red-300";

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${resultBadgeColors[predicted] || "bg-gray-100 text-gray-600"} ${border}`}
    >
      {resultLabels[predicted] || predicted}
    </span>
  );
}

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
  const exactCount = withPredictions.filter((r) => r.score_correct).length;
  const resultCount = withPredictions.filter((r) => r.result_correct).length;

  // Count all market picks that have been evaluated (correct !== null)
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
        Recent completed matches with prediction comparison
      </p>

      {/* Summary */}
      {withPredictions.length > 0 && (
        <div className="mb-4 sm:mb-6">
          <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-3">
            <div className="bg-white rounded-xl shadow-md p-2.5 sm:p-4 text-center">
              <p className="text-lg sm:text-2xl font-bold text-purple-600">
                {Math.round((exactCount / withPredictions.length) * 100)}%
              </p>
              <p className="text-[10px] sm:text-xs text-gray-500">Exact Score</p>
              <p className="text-[10px] text-gray-400 mt-1 hidden sm:block">~10% is typical</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-2.5 sm:p-4 text-center">
              <p className="text-lg sm:text-2xl font-bold text-amber-600">
                {Math.round((resultCount / withPredictions.length) * 100)}%
              </p>
              <p className="text-[10px] sm:text-xs text-gray-500">Correct Result</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-2.5 sm:p-4 text-center">
              <p className="text-lg sm:text-2xl font-bold text-blue-600">
                {marketHitRate}%
              </p>
              <p className="text-[10px] sm:text-xs text-gray-500">Market Hit</p>
              <p className="text-[10px] text-gray-400 mt-1 hidden sm:block">
                {correctMarkets.length}/{evaluatedMarkets.length} picks
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-400 text-center">
            Exact score prediction is the hardest metric — even the best models achieve ~10% accuracy.
            The real value is in correct result (H/D/A) and over/under market picks.
          </p>
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
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-center">Actual</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-center hidden sm:table-cell">Predicted</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-center">Result</th>
                <th className="px-1.5 sm:px-3 py-2 sm:py-3 text-center hidden sm:table-cell">Accuracy</th>
                <th className="px-3 py-3 text-left hidden md:table-cell">Markets</th>
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
                  <td className="px-3 py-3 text-center text-gray-500 hidden sm:table-cell">
                    {r.predicted_home_goals !== null
                      ? `${r.predicted_home_goals}-${r.predicted_away_goals}`
                      : "-"}
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3 text-center">
                    <ResultBadge
                      predicted={r.predicted_result}
                      actual={r.actual_result}
                    />
                  </td>
                  <td className="px-1.5 sm:px-3 py-2 sm:py-3 text-center hidden sm:table-cell">
                    {r.predicted_home_goals !== null ? (
                      <AccuracyBadge
                        scoreCorrect={r.score_correct}
                        resultCorrect={r.result_correct}
                      />
                    ) : (
                      <span className="text-gray-400 text-xs">No prediction</span>
                    )}
                  </td>
                  <td className="px-3 py-3 hidden md:table-cell">
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
