import client from './client';
import type { Stadium } from './stadiums';

export interface Match {
  id: number;
  away_club_id: number;
  home_club_id: number;
  stadium_id?: number | null;
  sim_day: number;
  status: string; // 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELED'
  limit_extra_innings?: boolean;
  home_score?: number | null;
  away_score?: number | null;
  stadium?: Stadium | null;
}

export interface GetMatchesParams {
  league_id?: number;
  club_id?: number;
  sim_day?: number;
  status?: string;
}

export const getMatches = async (params: GetMatchesParams = {}): Promise<Match[]> => {
  const response = await client.get<Match[]>('/matches', { params });
  return response.data;
};
