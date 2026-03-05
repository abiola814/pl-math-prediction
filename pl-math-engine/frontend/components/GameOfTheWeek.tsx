"use client";

import { useEffect, useState } from "react";
import { GameOfTheWeek as GameOfTheWeekType } from "@/lib/types";
import { getGameOfTheWeek } from "@/lib/api";

export default function GameOfTheWeek() {
  const [game, setGame] = useState<GameOfTheWeekType | null>(null);
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
        const data = await getGameOfTheWeek();
        if (data) {
          setGame(data);
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
    setTimeout(() => setGame(null), 300);
  }

  if (loading || !game) return null;

  const matchDate = new Date(game.date);
  const dateStr = matchDate.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

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
        className={`relative bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto transform transition-all duration-300 ${
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
              <p className="text-lg font-bold mt-0.5">Top Pick This Week</p>
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
        </div>

        <div className="px-5 py-4 space-y-4">
          {/* Date & Matchday */}
          <p className="text-xs text-gray-500 text-center">
            {dateStr}
            {game.matchday && <span className="ml-2 text-gray-400">Matchday {game.matchday}</span>}
          </p>

          {/* Teams and Predicted Score */}
          <div className="flex items-center justify-between">
            <div className="flex-1 text-right">
              <p className="font-bold text-gray-900 text-sm">{game.home_team}</p>
            </div>
            <div className="mx-4 flex items-center gap-2">
              <span className="text-3xl font-bold text-purple-900">
                {game.predicted_home_goals}
              </span>
              <span className="text-gray-400 text-lg">-</span>
              <span className="text-3xl font-bold text-purple-900">
                {game.predicted_away_goals}
              </span>
            </div>
            <div className="flex-1 text-left">
              <p className="font-bold text-gray-900 text-sm">{game.away_team}</p>
            </div>
          </div>

          <p className="text-center text-xs text-gray-500">
            Score probability: {Math.round(game.score_probability * 100)}%
          </p>

          {/* Best Pick Highlight */}
          <div className="bg-purple-50 rounded-xl p-4 text-center">
            <p className="text-[10px] text-purple-500 font-bold uppercase tracking-widest mb-1">
              Best Pick
            </p>
            <p className="text-lg font-bold text-purple-900">{game.best_pick_label}</p>
            <div className="mt-2 flex items-center justify-center gap-2">
              <div className="bg-purple-200 rounded-full h-2 w-28 overflow-hidden">
                <div
                  className="bg-purple-600 h-full rounded-full"
                  style={{ width: `${Math.round(game.best_pick_confidence * 100)}%` }}
                />
              </div>
              <span className="text-sm font-bold text-purple-700">
                {Math.round(game.best_pick_confidence * 100)}%
              </span>
            </div>
          </div>

          {/* Top 3 Market Picks */}
          <div>
            <p className="text-xs font-semibold text-gray-700 mb-2">Top Market Picks</p>
            <div className="space-y-1.5">
              {game.top_markets.map((m, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                  <span className="text-sm font-medium text-gray-800">{m.label}</span>
                  <span className="text-sm font-bold text-purple-700">
                    {Math.round(m.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* BTTS + Corners + Cards row */}
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-gray-50 rounded-lg p-2">
              <p className="font-semibold text-gray-700">{game.btts_recommendation}</p>
              <p className="text-purple-600 font-bold">{Math.round(game.btts_confidence * 100)}%</p>
            </div>
            {game.corner_pick && (
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="font-semibold text-gray-700">{game.corner_pick}</p>
                <p className="text-purple-600 font-bold">{Math.round((game.corner_confidence || 0) * 100)}%</p>
              </div>
            )}
            {game.card_pick && (
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="font-semibold text-gray-700">{game.card_pick}</p>
                <p className="text-purple-600 font-bold">{Math.round((game.card_confidence || 0) * 100)}%</p>
              </div>
            )}
          </div>

          {/* Result Section (if match is finished) */}
          {game.is_finished && game.actual_home_goals !== null && (
            <div className="border-t border-gray-200 pt-4">
              <p className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 text-center">
                Final Result
              </p>
              <div className="flex items-center justify-center gap-3 mb-3">
                <span className="text-2xl font-bold text-gray-900">
                  {game.actual_home_goals}
                </span>
                <span className="text-gray-400">-</span>
                <span className="text-2xl font-bold text-gray-900">
                  {game.actual_away_goals}
                </span>
              </div>

              <div className="flex justify-center gap-2 mb-3">
                {game.score_correct && (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-green-100 text-green-800">
                    Exact Score Hit!
                  </span>
                )}
                {game.result_correct && !game.score_correct && (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                    Result Correct
                  </span>
                )}
                {game.result_correct === false && (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800">
                    Result Wrong
                  </span>
                )}
              </div>

              {/* Market results */}
              {game.markets_correct && game.markets_correct.length > 0 && (
                <div className="space-y-1">
                  {game.markets_correct.map((m, i) => (
                    <div key={i} className="flex items-center justify-between text-xs px-2 py-1.5 rounded-lg bg-gray-50">
                      <span className="text-gray-700">{m.label}</span>
                      {m.correct === true && (
                        <span className="font-bold text-green-600">Hit</span>
                      )}
                      {m.correct === false && (
                        <span className="font-bold text-red-500">Miss</span>
                      )}
                      {m.correct === null && (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
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
