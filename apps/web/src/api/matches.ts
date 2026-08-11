import client from './client';
import type { Stadium } from './stadiums';

export type MatchStage = 'REGULAR' | 'TIEBREAKER' | 'INTERLEAGUE' | 'ELITE' | 'KNOCKOUT';
export type MatchStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELED';

export interface Match {
  id: number;
  away_club_id: number;
  home_club_id: number;
  stadium_id?: number | null;
  sim_day: number;
  status: MatchStatus | string;
  stage?: MatchStage | string;
  limit_extra_innings?: boolean;
  home_score?: number | null;
  away_score?: number | null;
  winning_pitcher_id?: number | null;
  losing_pitcher_id?: number | null;
  save_pitcher_id?: number | null;
  stadium?: Stadium | null;
}

export interface GetMatchesParams {
  league_id?: number;
  club_id?: number;
  sim_day?: number;
  start_date?: string;
  end_date?: string;
  date?: string;
  year?: number;
  status?: MatchStatus | string;
  stage?: MatchStage | string;
}

export interface IngameScoreboard {
  current_inning: number;
  is_top: boolean;
  balls: number;
  strikes: number;
  outs: number;
  away_innings: number[];
  away_r: number;
  away_h: number;
  away_e: number;
  away_b: number;
  home_innings: number[];
  home_r: number;
  home_h: number;
  home_e: number;
  home_b: number;
}

export interface IngameInstructionLog {
  simulation_version?: string;
  logged_events: Record<string, any>[];
}

export interface MatchDetailData extends Match {
  match_log?: IngameInstructionLog | null;
  match_log_json?: IngameInstructionLog | string | null;
}

export interface MatchPlaceholder {
  id: number;
  round: string; // 'ROUND_OF_8' | 'SEMI_FINAL' | 'FINAL'
  sim_day: number;
  limit_extra_innings: boolean;
  home_club_id?: number | null;
  away_club_id?: number | null;
  home_parent_id?: number | null;
  away_parent_id?: number | null;
  actual_match_id?: number | null;
}

export const getMatches = async (params: GetMatchesParams = {}): Promise<Match[]> => {
  const response = await client.get<Match[]>('/matches', { params });
  return response.data;
};

export const getMatchPlaceholders = async (year?: number): Promise<MatchPlaceholder[]> => {
  const response = await client.get<MatchPlaceholder[]>('/matches/placeholders', {
    params: year ? { year } : undefined,
  });
  return response.data;
};

export const getMatch = async (matchId: number): Promise<MatchDetailData> => {
  const response = await client.get<MatchDetailData>(`/matches/${matchId}`);
  return response.data;
};

export interface MatchLineupItem {
  id?: number;
  match_id: number;
  club_id: number;
  player_id: number;
  position: string;
  batting_order?: number | null;
  is_starter: boolean;
}

export interface MatchLineupResponse {
  away_lineup: MatchLineupItem[];
  home_lineup: MatchLineupItem[];
}

export const getMatchScoreboard = async (matchId: number): Promise<IngameScoreboard> => {
  const response = await client.get<IngameScoreboard>(`/matches/${matchId}/scoreboard`);
  return response.data;
};

export const getMatchLineup = async (matchId: number): Promise<MatchLineupResponse> => {
  const response = await client.get<MatchLineupResponse>(`/matches/${matchId}/lineup`);
  return response.data;
};

export interface MetricItemData {
  label: string;
  away: string;
  home: string;
  away_win: boolean;
}

export interface HeadToHeadDetailData {
  away_wins: number;
  home_wins: number;
  draws: number;
  recent_results?: string;
}

export interface PitcherProfileData {
  name: string;
  hand: string;
  era: string;
  record: string;
}

export interface PitcherComparisonData {
  away_pitcher: PitcherProfileData;
  home_pitcher: PitcherProfileData;
  metrics: MetricItemData[];
}

export interface MatchAnalysisData {
  away_team_record?: string;
  home_team_record?: string;
  head_to_head_detail: HeadToHeadDetailData;
  metrics: MetricItemData[];
  pitcher_comparison: PitcherComparisonData;
}

export const getMatchAnalysis = async (matchId: number): Promise<MatchAnalysisData> => {
  const response = await client.get<MatchAnalysisData>(`/matches/${matchId}/analysis`);
  return response.data;
};


