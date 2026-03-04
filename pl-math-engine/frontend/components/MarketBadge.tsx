"use client";

interface MarketBadgeProps {
  label: string;
  confidence: number;
  variant?: "goals" | "btts" | "corners";
}

export default function MarketBadge({
  label,
  confidence,
  variant = "goals",
}: MarketBadgeProps) {
  const pct = Math.round(confidence * 100);

  let bgColor: string;
  if (confidence >= 0.65) {
    bgColor =
      variant === "goals"
        ? "bg-green-600"
        : variant === "btts"
        ? "bg-blue-600"
        : "bg-amber-600";
  } else if (confidence >= 0.55) {
    bgColor =
      variant === "goals"
        ? "bg-green-500"
        : variant === "btts"
        ? "bg-blue-500"
        : "bg-amber-500";
  } else {
    bgColor = "bg-gray-500";
  }

  return (
    <span
      className={`${bgColor} text-white text-xs font-semibold px-2.5 py-1 rounded-full`}
    >
      {label} ({pct}%)
    </span>
  );
}
