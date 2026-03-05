import TeamDashboardClient from "./TeamDashboardClient";

export function generateStaticParams() {
  return [
    "Arsenal",
    "Aston Villa",
    "AFC Bournemouth",
    "Brentford",
    "Brighton & Hove Albion",
    "Chelsea",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Ipswich Town",
    "Leicester City",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Newcastle United",
    "Nottingham Forest",
    "Southampton",
    "Tottenham Hotspur",
    "West Ham United",
    "Wolverhampton Wanderers",
  ].map((name) => ({ name: encodeURIComponent(name) }));
}

export default function TeamPage() {
  return <TeamDashboardClient />;
}
