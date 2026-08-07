import client from './client';

export interface Player {
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
  height?: number;
  weight?: number;
}

export interface GetPlayersParams {
  club_id?: number;
}

export const getPlayers = async (params: GetPlayersParams = {}): Promise<Player[]> => {
  const response = await client.get<Player[]>('/players', { params });
  return response.data;
};
