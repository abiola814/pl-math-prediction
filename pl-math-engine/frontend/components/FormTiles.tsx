"use client";

import { TeamFixtureResult } from "@/lib/types";

const resultColors: Record<string, string> = {
  W: "bg-green-500 text-white",
  D: "bg-gray-400 text-white",
  L: "bg-red-500 text-white",
};

export default function FormTiles({ results }: { results: TeamFixtureResult[] }) {
  if (results.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 sm:gap-2">
      {results.map((r, i) => (
        <div
          key={i}
          className={`rounded-lg px-2 sm:px-3 py-1.5 sm:py-2 text-center min-w-[48px] sm:min-w-[60px] ${resultColors[r.result]}`}
          title={`${r.is_home ? "H" : "A"} vs ${r.opponent}: ${r.goals_for}-${r.goals_against}`}
        >
          <div className="text-xs font-bold">{r.result}</div>
          <div className="text-[10px] opacity-90 truncate max-w-[44px] sm:max-w-[56px]">
            {r.opponent.split(" ").pop()}
          </div>
          <div className="text-xs font-medium">
            {r.goals_for}-{r.goals_against}
          </div>
        </div>
      ))}
    </div>
  );
}
