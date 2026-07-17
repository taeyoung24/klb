import client from './client';

export interface SystemInfo {
  season_year: number;
  current_sim_day: number;
  current_date: string;
}

export const getSeasonYear = async (): Promise<number> => {
  const response = await client.get('/system/season-year');
  return response.data;
};

export const getSystemInfo = async (): Promise<SystemInfo> => {
  const response = await client.get<SystemInfo>('/system/info');
  return response.data;
};
