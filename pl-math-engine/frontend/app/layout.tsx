import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PL Math Engine",
  description: "Premier League match predictions with AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <nav className="bg-purple-900 text-white px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <a href="/" className="text-xl font-bold">
              PL Math Engine
            </a>
            <div className="flex gap-6 text-sm">
              <a href="/" className="hover:text-purple-300">
                Predictions
              </a>
              <a href="/accuracy" className="hover:text-purple-300">
                Accuracy
              </a>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
