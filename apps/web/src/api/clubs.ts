import client from './client';
import type { Stadium } from './stadiums';

export interface Club {
  id: number;
  name: string;
  name_ko: string;
  hometown: string;
  hometown_ko: string;
  team_code: string;
  abbr_name: string;
  stadium_name: string;
  stadium_name_ko: string;
  league_id: number;
  home_stadium_id?: number | null;
  home_stadium?: Stadium | null;
}

export const getClubs = async (leagueId?: number): Promise<Club[]> => {
  const response = await client.get<Club[]>('/clubs', {
    params: leagueId ? { league_id: leagueId } : {},
  });
  return response.data;
};
