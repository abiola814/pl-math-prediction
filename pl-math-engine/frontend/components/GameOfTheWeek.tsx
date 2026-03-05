"use client";

import { useEffect, useState } from "react";
import { GameOfTheWeek as GameOfTheWeekType } from "@/lib/types";
import { getGameOfTheWeek } from "@/lib/api";

export default function GameOfTheWeek() {
  const [data, setData] = useState<GameOfTheWeekType | null>(null);
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const dismissed = sessionStorage.getItem("gotw_dismissed");
    if (dismissed) {
      setLoading(false);
      return;
    }

    async function load() {
      try {
        const result = await getGameOfTheWeek();
        if (result && result.games.length > 0) {
          setData(result);
          setTimeout(() => setVisible(true), 400);
        }
      } catch {
        // don't break the app for a popup
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function dismiss() {
    setVisible(false);
    sessionStorage.setItem("gotw_dismissed", "1");
    setTimeout(() => setData(null), 300);
  }

  if (loading || !data) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        visible ? "opacity-100" : "opacity-0 pointer-events-none"
      }`}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={dismiss} />

      {/* Card */}
      <div
        className={`relative bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto transform transition-all duration-300 ${
          visible ? "scale-100 translate-y-0" : "scale-95 translate-y-4"
        }`}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-700 to-purple-900 text-white px-5 py-4 sticky top-0 z-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] font-bold text-purple-300 uppercase tracking-widest">
                Game of the Week
              </p>
              <p className="text-lg font-bold mt-0.5">
                Best Picks — {data.total_games} Games
              </p>
            </div>
            <button
              onClick={dismiss}
              className="text-purple-300 hover:text-white transition-colors p-1"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Accuracy summary if there are finished games */}
          {data.finished_games > 0 && (
            <div className="mt-2 flex items-center gap-3 text-sm">
              <span className="bg-purple-600 px-2.5 py-0.5 rounded-full text-xs font-bold">
                {data.accuracy}% Hit Rate
              </span>
              <span className="text-purple-300 text-xs">
                {data.correct_picks}/{data.finished_games} correct
              </span>
            </div>
          )}
        </div>

        {/* Games List */}
        <div className="px-4 py-3 space-y-2">
          {data.games.map((g) => {
            const dateStr = new Date(g.date).toLocaleDateString("en-GB", {
              day: "numeric",
              month: "short",
              hour: "2-digit",
              minute: "2-digit",
            });

            return (
              <div
                key={g.fixture_api_id}
                className={`rounded-xl p-3 border ${
                  g.is_finished
                    ? g.pick_correct
                      ? "border-green-200 bg-green-50"
                      : "border-red-200 bg-red-50"
                    : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  {/* Teams + Score */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 text-sm">
                      <span className="font-semibold text-gray-900 truncate">{g.home_team}</span>
                      <span className="text-gray-400 text-xs">vs</span>
                      <span className="font-semibold text-gray-900 truncate">{g.away_team}</span>
                    </div>
                    <p className="text-[10px] text-gray-400 mt-0.5">{dateStr}</p>
                  </div>

                  {/* Predicted score */}
                  <div className="text-center px-2">
                    <p className="text-xs text-gray-400">Pred</p>
                    <p className="font-bold text-purple-900 text-sm">
                      {g.predicted_home_goals}-{g.predicted_away_goals}
                    </p>
                  </div>

                  {/* Actual score if finished */}
                  {g.is_finished && g.actual_home_goals !== null && (
                    <div className="text-center px-2">
                      <p className="text-xs text-gray-400">Actual</p>
                      <p className="font-bold text-gray-900 text-sm">
                        {g.actual_home_goals}-{g.actual_away_goals}
                      </p>
                    </div>
                  )}
                </div>

                {/* Best pick */}
                <div className="mt-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      {g.best_pick_label}
                    </span>
                    <span className="text-xs font-bold text-purple-700">
                      {Math.round(g.best_pick_confidence * 100)}%
                    </span>
                  </div>

                  {/* Result badge */}
                  {g.is_finished && (
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${
                        g.pick_correct
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {g.pick_correct ? "Hit" : "Miss"}
                    </span>
                  )}

                  {!g.is_finished && (
                    <span className="text-xs text-gray-400">Pending</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-5 pb-4 pt-2">
          <a
            href="/predictions"
            className="block w-full bg-purple-700 hover:bg-purple-800 text-white text-center py-2.5 rounded-lg text-sm font-medium transition-colors"
          >
            View All Predictions
          </a>
        </div>
      </div>
    </div>
  );
}
