export interface Scoreline {
  home_goals: number;
  away_goals: number;
  total_goals: number;
  result: "H" | "D" | "A";
}

export interface Market {
  over_05: number;
  over_15: number;
  over_25: number;
  over_35: number;
  home_over_05: number;
  home_over_15: number;
  home_over_25: number;
  away_over_05: number;
  away_over_15: number;
  away_over_25: number;
  btts_yes: number;
  btts_no: number;
  recommended_market: string;
  recommended_confidence: number;
  btts_recommendation: string;
  btts_confidence: number;
  home_recommended: string;
  home_recommended_confidence: number;
  away_recommended: string;
  away_recommended_confidence: number;
}

export interface Corners {
  predicted_total: number;
  home_corners: number;
  away_corners: number;
  over_85: number;
  over_95: number;
  over_105: number;
  over_115: number;
  recommended_line: number;
  recommended_pick: string;
  confidence: number;
}

export interface Cards {
  predicted_total: number;
  home_cards: number;
  away_cards: number;
  over_25: number;
  over_35: number;
  over_45: number;
  over_55: number;
  recommended_line: number;
  recommended_pick: string;
  confidence: number;
}

export interface LLMVerdict {
  match_goals_pick: string;
  match_goals_confidence: number;
  match_goals_reasoning: string;
  home_goals_pick: string;
  home_goals_reasoning: string;
  away_goals_pick: string;
  away_goals_reasoning: string;
  btts_pick: string;
  btts_confidence: number;
  btts_reasoning: string;
  corners_pick: string;
  corners_confidence: number;
  corners_reasoning: string;
  cards_pick: string;
  cards_confidence: number;
  cards_reasoning: string;
  summary: string;
}

export interface Prediction {
  fixture_id: number;
  home_team: string;
  away_team: string;
  home_team_id: number;
  away_team_id: number;
  date: string;
  predicted_score: Scoreline;
  score_probability: number;
  top_scorelines: [string, number][];
  market: Market;
  corners: Corners;
  cards: Cards;
  llm_verdict: LLMVerdict | null;
  llm_insight: string | null;
  llm_adjustment_applied: boolean;
}

export interface AccuracyData {
  total_predictions: number;
  exact_score_accuracy: number | null;
  result_accuracy: number | null;
  over_under_accuracy: number | null;
  btts_accuracy: number | null;
  corner_line_accuracy: number | null;
  card_line_accuracy: number | null;
  message: string | null;
}

// ── Dashboard Types ──────────────────────────────────────────

export interface StandingOverview {
  position: number;
  team_name: string;
  team_api_id: number;
  logo_url: string | null;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  home_won: number;
  home_drawn: number;
  home_lost: number;
  away_won: number;
  away_drawn: number;
  away_lost: number;
  rating: number;
  form: number;
  home_advantage: number;
}

export interface TeamFixtureResult {
  date: string;
  opponent: string;
  is_home: boolean;
  goals_for: number;
  goals_against: number;
  result: "W" | "D" | "L";
  matchday: number | null;
}

export interface InjuryItem {
  player_name: string;
  player_position: string | null;
  reason: string | null;
}

export interface GoalsAnalysis {
  avg_scored: number;
  avg_conceded: number;
  avg_scored_home: number;
  avg_scored_away: number;
  avg_conceded_home: number;
  avg_conceded_away: number;
  clean_sheets: number;
  failed_to_score: number;
  total_matches: number;
}

export interface FixtureResponse {
  api_id: number;
  home_team: string;
  away_team: string;
  home_team_id: number;
  away_team_id: number;
  date: string;
  status: string;
  home_goals: number | null;
  away_goals: number | null;
  matchday: number | null;
  season: number;
}

export interface MiniTableRow {
  position: number;
  team_name: string;
  logo_url: string | null;
  goal_difference: number;
  points: number;
  is_current: boolean;
}

export interface OpponentInfo {
  name: string;
  position: number;
  form: number;
  rating: number;
}

export interface TeamDashboard {
  team_name: string;
  team_api_id: number;
  logo_url: string | null;
  position: number;
  points: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  rating: number;
  form: number;
  home_advantage: number;
  recent_form: TeamFixtureResult[];
  season_fixtures: TeamFixtureResult[];
  injuries: InjuryItem[];
  goals_analysis: GoalsAnalysis;
  next_fixture: FixtureResponse | null;
  next_opponent_info: OpponentInfo | null;
  h2h_vs_next: TeamFixtureResult[];
  mini_table: MiniTableRow[];
}

export interface FormHistoryPoint {
  matchday: number;
  form: number;
  cumulative_points: number;
  goals_scored: number;
  goals_conceded: number;
  cumulative_goals_for: number;
  cumulative_goals_against: number;
}

export interface ResultWithPrediction {
  fixture_api_id: number;
  home_team: string;
  away_team: string;
  date: string;
  matchday: number | null;
  actual_home_goals: number;
  actual_away_goals: number;
  predicted_home_goals: number | null;
  predicted_away_goals: number | null;
  predicted_result: string | null;
  actual_result: string;
  score_correct: boolean;
  result_correct: boolean;
  recommended_market: string | null;
  market_correct: boolean | null;
}

// ── Analysis Types ──────────────────────────────────────────

export interface TeamMatchdaySnapshot {
  matchday: number;
  form: number;
  cumulative_points: number;
  position: number;
}

export interface AllTeamsTimeSeries {
  teams: Record<string, TeamMatchdaySnapshot[]>;
}

export interface GoalFrequency {
  goals: number[];
  team_scored_pct: number[];
  team_conceded_pct: number[];
  avg_scored_pct: number[];
  avg_conceded_pct: number[];
}

export interface ScorelineFrequencyItem {
  scoreline: string;
  team_pct: number;
  avg_pct: number;
  outcome: "W" | "D" | "L";
}

export interface SpiderAttribute {
  name: string;
  team_value: number;
  avg_value: number;
}

export interface TeamComparisonData {
  team_name: string;
  attributes: SpiderAttribute[];
}
