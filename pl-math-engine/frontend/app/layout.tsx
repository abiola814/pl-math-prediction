"use client";

import "./globals.css";
import Logo from "@/components/Logo";
import { useState } from "react";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <html lang="en">
      <head>
        <title>PremPredict</title>
        <meta
          name="description"
          content="AI-powered Premier League predictions — scores, over/under, BTTS, corners, and cards"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <nav className="bg-purple-900 text-white px-4 sm:px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <a href="/" className="flex items-center gap-2 sm:gap-2.5 group">
              <Logo size={32} />
              <div className="leading-tight">
                <span className="text-base sm:text-lg font-bold tracking-tight group-hover:text-purple-300 transition-colors">
                  PremPredict
                </span>
                <span className="hidden sm:block text-[10px] text-purple-400 font-medium -mt-0.5">
                  AI Match Intelligence
                </span>
              </div>
            </a>

            {/* Desktop nav */}
            <div className="hidden sm:flex gap-5 text-sm">
              <a href="/" className="hover:text-purple-300 transition-colors">
                Standings
              </a>
              <a
                href="/predictions"
                className="hover:text-purple-300 transition-colors"
              >
                Predictions
              </a>
              <a
                href="/game-of-the-week"
                className="hover:text-purple-300 transition-colors"
              >
                Game of the Week
              </a>
              <a
                href="/results"
                className="hover:text-purple-300 transition-colors"
              >
                Results
              </a>
              <a
                href="/accuracy"
                className="hover:text-purple-300 transition-colors"
              >
                Accuracy
              </a>
            </div>

            {/* Mobile hamburger */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="sm:hidden p-1.5 rounded-md hover:bg-purple-800 transition-colors"
              aria-label="Toggle menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                {menuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>
          </div>

          {/* Mobile dropdown */}
          {menuOpen && (
            <div className="sm:hidden mt-2 pt-2 border-t border-purple-800 flex flex-col gap-2 text-sm">
              <a
                href="/"
                className="py-2 px-2 rounded hover:bg-purple-800 transition-colors"
              >
                Standings
              </a>
              <a
                href="/predictions"
                className="py-2 px-2 rounded hover:bg-purple-800 transition-colors"
              >
                Predictions
              </a>
              <a
                href="/game-of-the-week"
                className="py-2 px-2 rounded hover:bg-purple-800 transition-colors"
              >
                Game of the Week
              </a>
              <a
                href="/results"
                className="py-2 px-2 rounded hover:bg-purple-800 transition-colors"
              >
                Results
              </a>
              <a
                href="/accuracy"
                className="py-2 px-2 rounded hover:bg-purple-800 transition-colors"
              >
                Accuracy
              </a>
            </div>
          )}
        </nav>
        <main className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
