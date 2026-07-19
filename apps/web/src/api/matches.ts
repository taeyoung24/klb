import client from './client';

export interface Match {
  id: number;
  away_club_id: number;
  home_club_id: number;
  sim_day: number;
  status: string; // 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELED'
  home_score?: number | null;
  away_score?: number | null;
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
