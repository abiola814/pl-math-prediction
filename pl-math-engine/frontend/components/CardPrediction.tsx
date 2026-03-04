"use client";

import { Cards } from "@/lib/types";

interface CardPredictionProps {
  cards: Cards;
}

export default function CardPrediction({ cards }: CardPredictionProps) {
  const pct = Math.round(cards.confidence * 100);

  return (
    <div className="mt-3 bg-red-50 rounded-lg px-3 py-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="text-red-800 font-medium">Yellow Cards</span>
        <span className="text-red-900 font-bold">
          {cards.predicted_total.toFixed(1)} total
        </span>
      </div>
      <div className="flex items-center justify-between mt-1 text-xs text-red-700">
        <span>
          H: {cards.home_cards.toFixed(1)} | A: {cards.away_cards.toFixed(1)}
        </span>
        <span className="bg-red-600 text-white px-2 py-0.5 rounded-full">
          {cards.recommended_pick} ({pct}%)
        </span>
      </div>
    </div>
  );
}
