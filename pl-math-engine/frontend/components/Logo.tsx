export default function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer circle — football shape */}
      <circle cx="32" cy="32" r="30" fill="#7c3aed" />
      <circle cx="32" cy="32" r="27" fill="#6d28d9" />

      {/* Pentagon pattern — football stitching */}
      <path
        d="M32 12 L42 22 L38 34 L26 34 L22 22 Z"
        fill="#a78bfa"
        opacity="0.4"
      />
      <path
        d="M32 12 L42 22 L38 34 L26 34 L22 22 Z"
        fill="none"
        stroke="#c4b5fd"
        strokeWidth="1"
        opacity="0.6"
      />

      {/* Sigma symbol — mathematical prediction */}
      <text
        x="32"
        y="38"
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize="28"
        fontWeight="900"
        fill="white"
        fontFamily="serif"
      >
        &Sigma;
      </text>

      {/* Small data dots — representing prediction data points */}
      <circle cx="16" cy="44" r="2" fill="#a78bfa" opacity="0.7" />
      <circle cx="48" cy="44" r="2" fill="#a78bfa" opacity="0.7" />
      <circle cx="14" cy="28" r="1.5" fill="#a78bfa" opacity="0.5" />
      <circle cx="50" cy="28" r="1.5" fill="#a78bfa" opacity="0.5" />
    </svg>
  );
}
