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
