"use client";

import { useEffect, useState } from "react";
import { GameOfTheWeek as GameOfTheWeekType } from "@/lib/types";
import { getGameOfTheWeek } from "@/lib/api";

export default function GameOfTheWeekPage() {
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

  if (loading) {
    return (
      <div>
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Game of the Week
          </h1>
          <p className="text-gray-500 text-sm sm:text-base mt-1">
            Our highest-confidence picks this gameweek
          </p>
        </div>
        <div className="space-y-4 animate-pulse">
          <div className="h-32 bg-gradient-to-r from-purple-100 to-purple-50 rounded-xl" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-36 bg-gray-100 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div>
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Game of the Week
          </h1>
          <p className="text-gray-500 text-sm sm:text-base mt-1">
            Our highest-confidence picks this gameweek
          </p>
        </div>
        <div className="text-center py-20">
          <p className="text-gray-500 text-lg">No picks available this week.</p>
          <p className="text-gray-400 text-sm mt-2">
            Check back closer to the next matchday.
          </p>
        </div>
      </div>
    );
  }

  const pendingGames = data.games.filter((g) => !g.is_finished);
  const finishedGames = data.games.filter((g) => g.is_finished);
  const hitCount = finishedGames.filter((g) => g.pick_correct).length;
  const missCount = finishedGames.length - hitCount;

  // Sort pending by confidence (highest first)
  const sortedPending = [...pendingGames].sort(
    (a, b) => b.best_pick_confidence - a.best_pick_confidence
  );

  const topPick = sortedPending.length > 0 ? sortedPending[0] : null;

  return (
    <div>
      {/* Page header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          Game of the Week
        </h1>
        <p className="text-gray-500 text-sm sm:text-base mt-1">
          Our highest-confidence picks this gameweek
        </p>
      </div>

      {/* Stats banner */}
      <div className="bg-gradient-to-r from-purple-700 via-purple-800 to-purple-900 rounded-xl px-5 sm:px-8 py-5 sm:py-6 mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          {/* Left: headline + pills */}
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <svg className="w-5 h-5 text-purple-300" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span className="text-white text-xl sm:text-2xl font-bold">
                {data.total_games} Picks
              </span>
            </div>

            {/* Stat pills */}
            <div className="flex flex-wrap items-center gap-2 mt-3">
              {data.finished_games > 0 && (
                <>
                  <span className="inline-flex items-center gap-1.5 bg-green-500/20 text-green-300 text-xs font-medium px-2.5 py-1 rounded-full">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {hitCount} Hit{hitCount !== 1 ? "s" : ""}
                  </span>
                  <span className="inline-flex items-center gap-1.5 bg-red-500/20 text-red-300 text-xs font-medium px-2.5 py-1 rounded-full">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    {missCount} Miss{missCount !== 1 ? "es" : ""}
                  </span>
                </>
              )}
              {pendingGames.length > 0 && (
                <span className="inline-flex items-center gap-1.5 bg-white/10 text-purple-200 text-xs font-medium px-2.5 py-1 rounded-full">
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                  </svg>
                  {pendingGames.length} Pending
                </span>
              )}
            </div>
          </div>

          {/* Right: accuracy ring */}
          {data.accuracy !== null && (
            <div className="relative flex-shrink-0 self-center">
              <svg className="w-24 h-24 sm:w-28 sm:h-28" viewBox="0 0 100 100">
                <circle
                  cx="50" cy="50" r="42"
                  fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="8"
                />
                <circle
                  cx="50" cy="50" r="42"
                  fill="none"
                  stroke={data.accuracy >= 60 ? "#4ade80" : data.accuracy >= 40 ? "#fbbf24" : "#f87171"}
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${(data.accuracy / 100) * 263.9} 263.9`}
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-white text-2xl sm:text-3xl font-black leading-none">
                  {data.accuracy}%
                </span>
                <span className="text-purple-300 text-[10px] uppercase tracking-wider mt-0.5">
                  hit rate
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Insight text */}
        <div className="mt-4 pt-3 border-t border-white/10">
          <p className="text-purple-200 text-sm leading-relaxed">
            {data.accuracy !== null && data.accuracy >= 70
              ? "Excellent form this week — our model is firing on all cylinders. High-confidence picks deserve extra attention."
              : data.accuracy !== null && data.accuracy >= 50
                ? "Solid week so far. The model is tracking well — prioritise picks with 65%+ confidence for best results."
                : data.accuracy !== null
                  ? "A tricky set of fixtures this week. Stick to only the highest-confidence selections."
                  : pendingGames.length > 0
                    ? `All ${pendingGames.length} picks are still pending. Top confidence: ${Math.round(Math.max(...pendingGames.map((g) => g.best_pick_confidence)) * 100)}%.`
                    : "All picks have been settled for this gameweek."}
          </p>
        </div>
      </div>

      {/* Top Pick spotlight */}
      {topPick && (
        <div className="bg-white rounded-xl shadow-md border border-purple-100 overflow-hidden mb-6 sm:mb-8">
          <div className="bg-purple-50 px-5 py-2.5 border-b border-purple-100">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span className="text-xs font-bold text-purple-700 uppercase tracking-widest">
                Top Pick of the Week
              </span>
            </div>
          </div>
          <div className="px-5 py-4 sm:py-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p className="text-xl sm:text-2xl font-bold text-gray-900">
                  {topPick.home_team} vs {topPick.away_team}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {new Date(topPick.date).toLocaleDateString("en-GB", {
                    weekday: "long",
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-bold bg-purple-700 text-white">
                  {topPick.best_pick_label}
                </span>
                <div className="text-right">
                  <p className="text-2xl font-black text-purple-700">
                    {Math.round(topPick.best_pick_confidence * 100)}%
                  </p>
                  <p className="text-[10px] text-gray-400 uppercase tracking-wider">
                    confidence
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upcoming Picks */}
      {sortedPending.length > 0 && (
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold text-gray-900">Upcoming Picks</h2>
            <span className="h-px flex-1 bg-gray-200" />
            <span className="text-xs text-gray-400 font-medium">
              {sortedPending.length} match{sortedPending.length !== 1 ? "es" : ""}
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedPending.map((g, idx) => (
              <PendingCard key={g.fixture_api_id} game={g} rank={idx + 1} />
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {finishedGames.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold text-gray-900">Results</h2>
            <span className="h-px flex-1 bg-gray-200" />
            <span className="text-xs text-gray-400 font-medium">
              {hitCount}/{finishedGames.length} correct
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {finishedGames.map((g) => (
              <FinishedCard key={g.fixture_api_id} game={g} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Pending game card ── */
function PendingCard({
  game: g,
  rank,
}: {
  game: GameOfTheWeekType["games"][number];
  rank: number;
}) {
  const dateStr = new Date(g.date).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  const confPct = Math.round(g.best_pick_confidence * 100);
  const barColor =
    confPct >= 70
      ? "bg-green-500"
      : confPct >= 55
        ? "bg-amber-500"
        : "bg-gray-400";
  const confTextColor =
    confPct >= 70
      ? "text-green-600"
      : confPct >= 55
        ? "text-amber-600"
        : "text-gray-500";

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-4 border border-gray-100">
      {/* Rank badge */}
      <div className="flex items-center justify-between mb-3">
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold">
          {rank}
        </span>
        <span className="text-[10px] text-gray-400">{dateStr}</span>
      </div>

      {/* Teams */}
      <div className="mb-3">
        <p className="font-semibold text-gray-900 text-sm truncate">
          {g.home_team}
        </p>
        <p className="font-semibold text-gray-900 text-sm truncate mt-0.5">
          {g.away_team}
        </p>
      </div>

      {/* Pick + confidence */}
      <div className="pt-3 border-t border-gray-100">
        <div className="flex items-center justify-between mb-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold bg-purple-100 text-purple-800">
            {g.best_pick_label}
          </span>
          <span className={`text-sm font-bold ${confTextColor}`}>
            {confPct}%
          </span>
        </div>
        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${confPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

/* ── Finished game card ── */
function FinishedCard({
  game: g,
}: {
  game: GameOfTheWeekType["games"][number];
}) {
  const isHit = g.pick_correct;

  return (
    <div
      className={`rounded-xl shadow-md p-4 border ${
        isHit
          ? "border-green-200 bg-gradient-to-br from-green-50 to-white"
          : "border-red-200 bg-gradient-to-br from-red-50 to-white"
      }`}
    >
      {/* Result badge */}
      <div className="flex items-center justify-between mb-3">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${
            isHit ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
          }`}
        >
          {isHit ? (
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          )}
          {isHit ? "Hit" : "Miss"}
        </span>
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-purple-100 text-purple-800">
          {g.best_pick_label}
        </span>
      </div>

      {/* Teams + FT score */}
      <div className="space-y-1 mb-3">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-gray-900 text-sm truncate flex-1">
            {g.home_team}
          </span>
          <span className="font-bold text-gray-900 text-sm w-4 text-center ml-2">
            {g.actual_home_goals}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-semibold text-gray-900 text-sm truncate flex-1">
            {g.away_team}
          </span>
          <span className="font-bold text-gray-900 text-sm w-4 text-center ml-2">
            {g.actual_away_goals}
          </span>
        </div>
      </div>

      {/* Confidence */}
      <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
        <span className="text-[11px] text-gray-500">Confidence</span>
        <span className="text-xs font-bold text-purple-600">
          {Math.round(g.best_pick_confidence * 100)}%
        </span>
      </div>
    </div>
  );
}
