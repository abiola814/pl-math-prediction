"use client";

import { useEffect, useState } from "react";
import { GameOfTheWeek as GameOfTheWeekType } from "@/lib/types";
import { getGameOfTheWeek } from "@/lib/api";

export default function GameOfTheWeek() {
  const [data, setData] = useState<GameOfTheWeekType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = await getGameOfTheWeek();
        if (result && result.games.length > 0) {
          setData(result);
        }
      } catch {
        // silently fail
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading || !data) return null;

  const pendingGames = data.games.filter((g) => !g.is_finished);
  const finishedGames = data.games.filter((g) => g.is_finished);
  const hitCount = finishedGames.filter((g) => g.pick_correct).length;
  const missCount = finishedGames.length - hitCount;

  return (
    <section className="mb-6 sm:mb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-700 to-purple-900 rounded-t-xl px-4 sm:px-5 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-purple-300 uppercase tracking-widest">
              Weekly Insight
            </p>
            <h2 className="text-base sm:text-lg font-bold text-white mt-0.5">
              Game of the Week — {data.total_games} Picks
            </h2>
          </div>
          {data.accuracy !== null && (
            <div className="flex flex-col items-end">
              <span className="text-2xl sm:text-3xl font-black text-white leading-none">
                {data.accuracy}%
              </span>
              <span className="text-[10px] text-purple-300 mt-0.5">
                hit rate
              </span>
            </div>
          )}
        </div>

        {/* Stats bar */}
        {data.finished_games > 0 && (
          <div className="mt-3 flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400" />
              <span className="text-xs text-purple-200">
                {hitCount} Hit{hitCount !== 1 ? "s" : ""}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-400" />
              <span className="text-xs text-purple-200">
                {missCount} Miss{missCount !== 1 ? "es" : ""}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-400" />
              <span className="text-xs text-purple-200">
                {pendingGames.length} Pending
              </span>
            </div>
            {/* Progress bar */}
            <div className="flex-1 h-1.5 bg-purple-800 rounded-full overflow-hidden ml-1">
              <div
                className="h-full bg-green-400 rounded-full transition-all"
                style={{
                  width: `${data.finished_games > 0 ? (hitCount / data.total_games) * 100 : 0}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Games grid */}
      <div className="bg-white border border-t-0 border-gray-200 rounded-b-xl shadow-md">
        {/* Finished results section */}
        {finishedGames.length > 0 && (
          <div className="px-3 sm:px-4 pt-3 pb-1">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
              Results
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {finishedGames.map((g) => (
                <GameCard key={g.fixture_api_id} game={g} />
              ))}
            </div>
          </div>
        )}

        {/* Upcoming picks section */}
        {pendingGames.length > 0 && (
          <div className="px-3 sm:px-4 pt-3 pb-1">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
              Upcoming Picks
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {pendingGames.map((g) => (
                <GameCard key={g.fixture_api_id} game={g} />
              ))}
            </div>
          </div>
        )}

        {/* Footer insight */}
        <div className="px-3 sm:px-4 py-3 border-t border-gray-100 mt-2">
          <p className="text-xs text-gray-500">
            {data.accuracy !== null && data.accuracy >= 70
              ? "Strong week — picks are performing well. Consider following the remaining selections."
              : data.accuracy !== null && data.accuracy >= 50
                ? "Solid accuracy this week. Check individual confidence levels before placing."
                : data.accuracy !== null
                  ? "Tougher week for picks. Focus on the highest-confidence selections."
                  : pendingGames.length > 0
                    ? `${pendingGames.length} pick${pendingGames.length > 1 ? "s" : ""} awaiting results. Best confidence: ${Math.round(Math.max(...pendingGames.map((g) => g.best_pick_confidence)) * 100)}%.`
                    : "All picks have been settled."}
          </p>
        </div>
      </div>
    </section>
  );
}

function GameCard({
  game: g,
}: {
  game: GameOfTheWeekType["games"][number];
}) {
  const dateStr = new Date(g.date).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={`rounded-lg p-2.5 border ${
        g.is_finished
          ? g.pick_correct
            ? "border-green-200 bg-green-50/70"
            : "border-red-200 bg-red-50/70"
          : "border-purple-100 bg-purple-50/40"
      }`}
    >
      {/* Teams row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 text-sm">
            <span className="font-semibold text-gray-900 truncate">
              {g.home_team}
            </span>
            <span className="text-gray-400 text-xs">vs</span>
            <span className="font-semibold text-gray-900 truncate">
              {g.away_team}
            </span>
          </div>
          <p className="text-[10px] text-gray-400 mt-0.5">{dateStr}</p>
        </div>

        {/* Scores */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="text-center">
            <p className="text-[10px] text-gray-400">Pred</p>
            <p className="font-bold text-purple-900 text-sm">
              {g.predicted_home_goals}-{g.predicted_away_goals}
            </p>
          </div>
          {g.is_finished && g.actual_home_goals !== null && (
            <div className="text-center">
              <p className="text-[10px] text-gray-400">FT</p>
              <p className="font-bold text-gray-900 text-sm">
                {g.actual_home_goals}-{g.actual_away_goals}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Pick row */}
      <div className="mt-1.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-100 text-purple-800">
            {g.best_pick_label}
          </span>
          <span className="text-xs font-bold text-purple-700">
            {Math.round(g.best_pick_confidence * 100)}%
          </span>
        </div>
        {g.is_finished ? (
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold ${
              g.pick_correct
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {g.pick_correct ? "Hit" : "Miss"}
          </span>
        ) : (
          <span className="text-[11px] text-gray-400 italic">Pending</span>
        )}
      </div>
    </div>
  );
}
