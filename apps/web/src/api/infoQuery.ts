import client from './client';
import type { Region } from './regions';
import type { HighSchool } from './highSchools';

export interface PlayerInfo {
  id: number;
  name: string;
  club_id: number;
  uniform_number: string;
  position: string;
  speed?: number;
  control?: number;
  power?: number;
  flexibility?: number;
  focus?: number;
  stamina?: number;
  height?: number;
  weight?: number;
  region_id?: number;
  region?: Region | null;
  high_school_id?: number;
  high_school?: HighSchool | null;
}

export interface InfoQueryPlayersParams {
  club_id?: number;
  position?: string;
  name?: string;
  page?: number;
  limit?: number;
}

export interface InfoQueryPlayersResponse {
  items: PlayerInfo[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export type Player = PlayerInfo;

export const fetchInfoQueryPlayers = async (
  params: InfoQueryPlayersParams = {}
): Promise<InfoQueryPlayersResponse> => {
  const response = await client.get<InfoQueryPlayersResponse>('/info-query/players', { params });
  return response.data;
};

export const getClubPlayers = async (clubId: number): Promise<PlayerInfo[]> => {
  const response = await client.get<InfoQueryPlayersResponse>('/info-query/players', {
    params: { club_id: clubId, limit: 100 },
  });
  return response.data.items;
};
