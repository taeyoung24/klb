export interface LeagueColorTheme {
  primary: string;
  secondary: string;
}

export const AWAY_TEAM_COLOR: LeagueColorTheme = {
  primary: '#888888',
  secondary: '#aaaaaa',
};

export const LEAGUE_COLORS: Record<string, LeagueColorTheme> = {
  // 매그놀리아 리그 (ML)
  ML: {
    primary: '#FFFFFF',
    secondary: '#FFE83B',
  },
  // 카멜리아 리그 (CL)
  CL: {
    primary: '#D22828',
    secondary: '#EBC988',
  },
  // 젠티아나 리그 (GL)
  GL: {
    primary: '#5C71FB',
    secondary: '#795CFB',
  },
  // 아젤리아 리그 (AL)
  AL: {
    primary: '#F8369A',
    secondary: '#FFFFFF',
  },
};

export const getLeagueColor = (leagueCode: string): LeagueColorTheme => {
  return LEAGUE_COLORS[leagueCode.toUpperCase()] || {
    primary: '#cccccc',
    secondary: '#ffffff',
  };
};
