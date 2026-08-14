import client from './client';

export interface DailyClubStanding {
  id: number;
  sim_day: number;
  league_id: number;
  club_id: number;
  is_postseason?: boolean;
  rank: number;
  win_rate: number;
  games_back: number;
  wins: number;
  draws: number;
  losses: number;
  games_played: number;
  streak: number;
  batting_average: number;
  era: number;
}

export const getStandings = async (
  leagueId: number,
  simDay?: number,
  isPostseason?: boolean,
  date?: string
): Promise<DailyClubStanding[]> => {
  const response = await client.get<DailyClubStanding[]>('/standings', {
    params: {
      league_id: leagueId,
      ...(simDay !== undefined ? { sim_day: simDay } : {}),
      ...(isPostseason !== undefined ? { is_postseason: isPostseason } : {}),
      ...(date ? { date } : {}),
    },
  });
  return response.data;
};

export const getLatestStandings = async (params?: {
  year?: number;
  leagueId?: number;
  isPostseason?: boolean;
}): Promise<DailyClubStanding[]> => {
  const response = await client.get<DailyClubStanding[]>('/standings/latest', {
    params: {
      ...(params?.year !== undefined ? { year: params.year } : {}),
      ...(params?.leagueId !== undefined ? { league_id: params.leagueId } : {}),
      ...(params?.isPostseason !== undefined ? { is_postseason: params.isPostseason } : {}),
    },
  });
  return response.data;
};

export const getStandingSeasons = async (): Promise<number[]> => {
  const response = await client.get<number[]>('/standings/seasons');
  return response.data;
};
