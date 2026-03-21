"use client";

import { useState } from "react";
import { Prediction } from "@/lib/types";
import MarketBadge from "./MarketBadge";
import CornerPrediction from "./CornerPrediction";
import CardPrediction from "./CardPrediction";

interface PredictionCardProps {
  prediction: Prediction;
}

function ConfidenceDots({ level }: { level: number }) {
  return (
    <span className="inline-flex gap-0.5">
      {[...Array(10)].map((_, i) => (
        <span
          key={i}
          className={`w-1.5 h-1.5 rounded-full ${
            i < level ? "bg-purple-600" : "bg-gray-200"
          }`}
        />
      ))}
    </span>
  );
}

export default function PredictionCard({ prediction }: PredictionCardProps) {
  const [showAI, setShowAI] = useState(false);
  const { market, corners, cards, llm_verdict } = prediction;

  const matchDate = new Date(prediction.date);
  const dateStr = matchDate.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="bg-white rounded-xl shadow-md p-5 hover:shadow-lg transition-shadow">
      {/* Date */}
      <p className="text-xs text-gray-500 mb-3 text-center">{dateStr}</p>

      {/* Teams */}
      <div className="text-center mb-4">
        <p className="font-semibold text-gray-900 text-sm">
          {prediction.home_team}
        </p>
        <p className="text-gray-400 text-xs my-0.5">vs</p>
        <p className="font-semibold text-gray-900 text-sm">
          {prediction.away_team}
        </p>
      </div>

      {/* Stats Market Badges */}
      <div className="flex flex-wrap gap-2 justify-center mb-3">
        <MarketBadge
          label={market.recommended_market}
          confidence={market.recommended_confidence}
          variant="goals"
        />
        <MarketBadge
          label={market.btts_recommendation}
          confidence={market.btts_confidence}
          variant="btts"
        />
      </div>

      {/* Home/Away Team Market Badges */}
      <div className="flex flex-wrap gap-2 justify-center mb-3">
        <MarketBadge
          label={market.home_recommended}
          confidence={market.home_recommended_confidence}
          variant="goals"
        />
        <MarketBadge
          label={market.away_recommended}
          confidence={market.away_recommended_confidence}
          variant="goals"
        />
      </div>

      {/* Goal Probabilities */}
      <div className="grid grid-cols-3 gap-2 text-xs text-center text-gray-600 mb-2">
        <div>
          <p className="font-medium">O1.5</p>
          <p>{Math.round(market.over_15 * 100)}%</p>
        </div>
        <div>
          <p className="font-medium">O2.5</p>
          <p>{Math.round(market.over_25 * 100)}%</p>
        </div>
        <div>
          <p className="font-medium">BTTS</p>
          <p>{Math.round(market.btts_yes * 100)}%</p>
        </div>
      </div>

      {/* Home/Away Team Goal Probabilities */}
      <div className="grid grid-cols-2 gap-3 text-xs text-center text-gray-600 mb-3">
        <div className="bg-gray-50 rounded p-1.5">
          <p className="font-medium text-gray-700 mb-1">{prediction.home_team}</p>
          <div className="flex justify-around">
            <div>
              <p className="font-medium">O0.5</p>
              <p>{Math.round(market.home_over_05 * 100)}%</p>
            </div>
            <div>
              <p className="font-medium">O1.5</p>
              <p>{Math.round(market.home_over_15 * 100)}%</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-50 rounded p-1.5">
          <p className="font-medium text-gray-700 mb-1">{prediction.away_team}</p>
          <div className="flex justify-around">
            <div>
              <p className="font-medium">O0.5</p>
              <p>{Math.round(market.away_over_05 * 100)}%</p>
            </div>
            <div>
              <p className="font-medium">O1.5</p>
              <p>{Math.round(market.away_over_15 * 100)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Corner Prediction */}
      <CornerPrediction corners={corners} />

      {/* Card Prediction */}
      <CardPrediction cards={cards} />

      {/* AI Market Verdict */}
      {llm_verdict && llm_verdict.summary && (
        <div className="mt-3">
          <button
            onClick={() => setShowAI(!showAI)}
            className="w-full bg-purple-50 hover:bg-purple-100 rounded-lg px-3 py-2 text-xs text-purple-800 text-left transition-colors"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold">AI Market Analyst</span>
              <span className="text-purple-400">{showAI ? "Hide" : "Show"}</span>
            </div>
            <p className="mt-1 text-purple-700">{llm_verdict.summary}</p>
          </button>

          {showAI && (
            <div className="mt-2 bg-purple-50 rounded-lg px-3 py-3 space-y-2 text-xs">
              {/* AI Goals Pick */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-semibold text-purple-900">
                    {llm_verdict.match_goals_pick}
                  </span>
                  <p className="text-purple-600 mt-0.5">
                    {llm_verdict.match_goals_reasoning}
                  </p>
                </div>
                <ConfidenceDots level={llm_verdict.match_goals_confidence} />
              </div>

              {/* AI Home/Away Goals */}
              <div className="border-t border-purple-200 pt-2 grid grid-cols-2 gap-2">
                <div>
                  <p className="font-semibold text-purple-900">
                    {llm_verdict.home_goals_pick}
                  </p>
                  <p className="text-purple-600">{llm_verdict.home_goals_reasoning}</p>
                </div>
                <div>
                  <p className="font-semibold text-purple-900">
                    {llm_verdict.away_goals_pick}
                  </p>
                  <p className="text-purple-600">{llm_verdict.away_goals_reasoning}</p>
                </div>
              </div>

              {/* AI BTTS */}
              <div className="border-t border-purple-200 pt-2 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-purple-900">
                    {llm_verdict.btts_pick}
                  </span>
                  <p className="text-purple-600 mt-0.5">
                    {llm_verdict.btts_reasoning}
                  </p>
                </div>
                <ConfidenceDots level={llm_verdict.btts_confidence} />
              </div>

              {/* AI Corners */}
              <div className="border-t border-purple-200 pt-2 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-purple-900">
                    {llm_verdict.corners_pick}
                  </span>
                  <p className="text-purple-600 mt-0.5">
                    {llm_verdict.corners_reasoning}
                  </p>
                </div>
                <ConfidenceDots level={llm_verdict.corners_confidence} />
              </div>

              {/* AI Cards */}
              <div className="border-t border-purple-200 pt-2 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-purple-900">
                    {llm_verdict.cards_pick}
                  </span>
                  <p className="text-purple-600 mt-0.5">
                    {llm_verdict.cards_reasoning}
                  </p>
                </div>
                <ConfidenceDots level={llm_verdict.cards_confidence} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
