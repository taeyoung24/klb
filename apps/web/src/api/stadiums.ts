import client from './client';
import type { Region } from './regions';

export interface FenceProfileItem {
  angle: number;
  dist: number;
  height: number;
}

export interface Stadium {
  id: number;
  name: string;
  name_ko: string;
  is_dome: boolean;
  capacity: number;
  turf_type: string;
  altitude: number;
  fence_profile: FenceProfileItem[];
  curvature: number;
  region_id?: number;
  region?: Region | null;
}

export const getStadiums = async (): Promise<Stadium[]> => {
  const response = await client.get<Stadium[]>('/stadiums');
  return response.data;
};

export const getStadiumById = async (id: number): Promise<Stadium> => {
  const response = await client.get<Stadium>(`/stadiums/${id}`);
  return response.data;
};
