"use client";

import { Corners } from "@/lib/types";

interface CornerPredictionProps {
  corners: Corners;
}

export default function CornerPrediction({ corners }: CornerPredictionProps) {
  const pct = Math.round(corners.confidence * 100);

  return (
    <div className="mt-3 bg-amber-50 rounded-lg px-3 py-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="text-amber-800 font-medium">Corners</span>
        <span className="text-amber-900 font-bold">
          {corners.predicted_total.toFixed(1)} total
        </span>
      </div>
      <div className="flex items-center justify-between mt-1 text-xs text-amber-700">
        <span>
          H: {corners.home_corners.toFixed(1)} | A:{" "}
          {corners.away_corners.toFixed(1)}
        </span>
        <span className="bg-amber-600 text-white px-2 py-0.5 rounded-full">
          {corners.recommended_pick} ({pct}%)
        </span>
      </div>
    </div>
  );
}
