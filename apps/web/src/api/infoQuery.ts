import client from './client';
import type { Region } from './regions';
import type { HighSchool } from './highSchools';

export interface PlayerListItem {
  id: number;
  name: string;
  club_id: number;
  uniform_number: string;
  position: string;
  potential?: number;
  height?: number;
  weight?: number;
  region_id?: number;
  region?: Region | null;
  high_school_id?: number;
  high_school?: HighSchool | null;
}

export interface PlayerBattingRecord {
  season: string;
  avg: string;
  games: number;
  ab: number;
  hits: number;
  homeruns: number;
  rbi: number;
  so: number;
  obp: string;
  ops: string;
}

export type PlayerSeasonRecord = PlayerBattingRecord;

export interface PlayerPitchingRecord {
  season: string;
  era: string;
  games: number;
  innings: string;
  wins: number;
  losses: number;
  saves: number;
  holds: number;
  so: number;
  hits: number;
  homeruns: number;
  runs: number;
  bb: number;
  hbp: number;
  whip: string;
}

export interface PlayerDetailInfo {
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
  potential?: number;
  current_energy?: number;
  max_energy?: number;
  height?: number;
  weight?: number;
  birthday?: string;
  personality?: number[];
  roster_status?: string;
  region_id?: number;
  region?: Region | null;
  high_school_id?: number;
  high_school?: HighSchool | null;
  records?: PlayerBattingRecord[];
  batting_records?: PlayerBattingRecord[];
  pitching_records?: PlayerPitchingRecord[];
}

export type PlayerInfo = PlayerListItem;

export interface InfoQueryPlayersParams {
  club_id?: number;
  position?: string;
  name?: string;
  page?: number;
  limit?: number;
}

export interface InfoQueryPlayersResponse {
  items: PlayerListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export type Player = PlayerListItem;

export const fetchInfoQueryPlayers = async (
  params: InfoQueryPlayersParams = {}
): Promise<InfoQueryPlayersResponse> => {
  const response = await client.get<InfoQueryPlayersResponse>('/info-query/players', { params });
  return response.data;
};

export const fetchInfoQueryPlayerDetail = async (
  playerId: number
): Promise<PlayerDetailInfo> => {
  const response = await client.get<PlayerDetailInfo>(`/info-query/players/${playerId}`);
  return response.data;
};

export const getClubPlayers = async (clubId: number): Promise<PlayerListItem[]> => {
  const response = await client.get<InfoQueryPlayersResponse>('/info-query/players', {
    params: { club_id: clubId, limit: 100 },
  });
  return response.data.items;
};
