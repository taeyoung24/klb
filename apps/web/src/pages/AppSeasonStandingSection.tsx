import { useEffect, useState } from 'react'
import { FaCircle } from 'react-icons/fa'
import { getClubs, type Club } from '../api/clubs'
import { getMatches, type Match } from '../api/matches'
import { getStandings, type DailyClubStanding } from '../api/standings'
import { getSystemInfo } from '../api/system'
import MatchSeries from '../components/MatchSeries/MatchSeries'
import TeamLogo from '../components/TeamLogo/TeamLogo'
import './AppSeasonStandingSection.css'

const LEAGUES = [
  { code: 'AL' as const, id: 1, name: '아젤리아' },
  { code: 'CL' as const, id: 2, name: '카멜리아' },
  { code: 'GL' as const, id: 3, name: '젠티아나' },
  { code: 'ML' as const, id: 4, name: '매그놀리아' },
];

const getSimDayFromDate = (date: Date, year: number): number => {
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const baseDate = new Date(year, 0, 1);
  const diffTime = target.getTime() - baseDate.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  return diffDays + 1;
};

const formatPct = (pct: number) => {
  if (pct === 1) return "1.000";
  if (pct === 0) return ".000";
  const formatted = pct.toFixed(3);
  return formatted.startsWith("0") ? formatted.substring(1) : formatted;
};

const formatGb = (gb: number) => {
  if (gb === 0) return "-";
  const val = gb / 10;
  return val % 1 === 0 ? val.toString() : val.toFixed(1);
};

const formatStreak = (streak: number) => {
  if (streak === 0) return "-";
  if (streak > 0) return `${streak}승`;
  return `${Math.abs(streak)}패`;
};

interface AppSeasonStandingSectionProps {
  matchDate: Date;
  seasonYear: number | null;
  isSeasonYearLoaded: boolean;
}

export default function AppSeasonStandingSection({
  matchDate,
  seasonYear,
  isSeasonYearLoaded,
}: AppSeasonStandingSectionProps) {
  const [activeLeague, setActiveLeague] = useState<'AL' | 'CL' | 'GL' | 'ML'>('AL')
  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [allStandings, setAllStandings] = useState<Record<'AL' | 'CL' | 'GL' | 'ML', DailyClubStanding[]>>({
    AL: [],
    CL: [],
    GL: [],
    ML: [],
  });
  const [isStandingsLoaded, setIsStandingsLoaded] = useState(false);

  const [selectedStep, setSelectedStep] = useState<number>(1);
  const [seedMap, setSeedMap] = useState<Record<number, string>>({});
  const [eliteMatches, setEliteMatches] = useState<Match[]>([]);
  const [knockoutMatches, setKnockoutMatches] = useState<Match[]>([]);
  const [hostLeagueName, setHostLeagueName] = useState<string | null>(null);
  const [hostLeagueId, setHostLeagueId] = useState<number>(1);
  const [eliteStandings, setEliteStandings] = useState<DailyClubStanding[]>([]);

  useEffect(() => {
    getClubs()
      .then(list => {
        const map: Record<number, Club> = {};
        list.forEach(c => {
          map[c.id] = c;
        });
        setClubsMap(map);
      })
      .catch(e => {
        console.error("Failed to fetch clubs", e);
      });
  }, []);

  useEffect(() => {
    getSystemInfo()
      .then(info => {
        if (info.host_league_name) {
          setHostLeagueName(info.host_league_name);
        }
        if (info.host_league_id) {
          setHostLeagueId(info.host_league_id);
        }
      })
      .catch(e => {
        console.error("Failed to fetch host league region", e);
      });
  }, []);

  useEffect(() => {
    const rawSimDay = getSimDayFromDate(matchDate, seasonYear || 2026);
    const regSimDay = Math.min(rawSimDay, 228);
    setIsStandingsLoaded(false);

    Promise.all(
      LEAGUES.map(league => getStandings(league.id, regSimDay, false))
    )
      .then(([alData, clData, glData, mlData]) => {
        setAllStandings({
          AL: alData,
          CL: clData,
          GL: glData,
          ML: mlData,
        });
        setIsStandingsLoaded(true);
      })
      .catch(e => {
        console.error("Failed to fetch all standings", e);
        setAllStandings({
          AL: [],
          CL: [],
          GL: [],
          ML: [],
        });
        setIsStandingsLoaded(true);
      });
  }, [matchDate, seasonYear]);

  useEffect(() => {
    const simDay = getSimDayFromDate(matchDate, seasonYear || 2026);
    if (simDay >= 229) {
      getStandings(hostLeagueId, simDay, true)
        .then(data => setEliteStandings(data))
        .catch(e => {
          console.error("Failed to fetch elite standings snapshot", e);
          setEliteStandings([]);
        });
    }
  }, [matchDate, seasonYear, hostLeagueId]);

  useEffect(() => {
    const finalSimDay = 228;
    Promise.all(
      LEAGUES.map(league => getStandings(league.id, finalSimDay))
    )
      .then(results => {
        const map: Record<number, string> = {};
        const leagueCodes = ['AL', 'CL', 'GL', 'ML'];
        results.forEach((standings, idx) => {
          const code = leagueCodes[idx];
          standings.forEach(row => {
            if (row.rank <= 4) {
              map[row.club_id] = `${code}#${row.rank}`;
            }
          });
        });
        setSeedMap(map);
      })
      .catch(e => console.error("Failed to load final standings for seeds", e));

    getMatches({ status: 'COMPLETED' })
      .then(matches => {
        // limit_extra_innings가 false인 경우 연장 무제한인 녹아웃(토너먼트) 경기
        const postMatches = matches.filter(m => m.sim_day >= 229);
        const ko = postMatches.filter(m => m.limit_extra_innings === false);
        const elite = postMatches.filter(m => m.limit_extra_innings !== false);

        setEliteMatches(elite);
        setKnockoutMatches(ko);
      })
      .catch(e => console.error("Failed to load completed post-season matches", e));
  }, [seasonYear, matchDate]);

  const isSectionLoaded = isSeasonYearLoaded && isStandingsLoaded && Object.keys(clubsMap).length > 0;

  const simDay = getSimDayFromDate(matchDate, seasonYear || 2026);
  const isOpening = simDay >= 62;
  const isSecondHalf = simDay >= 146;
  const isPostSeason = simDay >= 229;
  const isKnockout = simDay >= 229 && (knockoutMatches.length > 0 || simDay >= 275);

  let currentStep = 1;
  if (simDay < 146) {
    currentStep = 1;
  } else if (simDay >= 146 && simDay <= 228) {
    currentStep = 3;
  } else if (simDay >= 229 && simDay <= 283) {
    currentStep = 4;
  } else {
    currentStep = 5;
  }

  // 현재 날짜 단계가 바뀌면 자동으로 선택된 단계를 활성화
  useEffect(() => {
    setSelectedStep(currentStep);
  }, [currentStep]);

  interface EliteStandingRow {
    club_id: number;
    wins: number;
    losses: number;
    draws: number;
    games_played: number;
    win_rate: number;
    games_back: number;
    rank: number;
    streak: number;
  }

  // 4단계 크라운 정예리그 순위표 동적 집계 로직
  const getEliteStandings = (): EliteStandingRow[] => {
    const clubIds = Object.keys(seedMap).map(Number);
    if (clubIds.length === 0) return [];

    const stats: Record<number, Omit<EliteStandingRow, 'rank' | 'games_back'>> = {};
    clubIds.forEach(cid => {
      stats[cid] = {
        club_id: cid,
        wins: 0,
        losses: 0,
        draws: 0,
        games_played: 0,
        win_rate: 0,
        streak: 0,
      };
    });

    eliteMatches.forEach(m => {
      const h = m.home_club_id;
      const a = m.away_club_id;
      if (stats[h] && stats[a] && m.status === 'COMPLETED') {
        stats[h].games_played += 1;
        stats[a].games_played += 1;
        const h_score = m.home_score ?? 0;
        const a_score = m.away_score ?? 0;

        if (h_score > a_score) {
          stats[h].wins += 1;
          stats[a].losses += 1;
        } else if (h_score < a_score) {
          stats[a].wins += 1;
          stats[h].losses += 1;
        } else {
          stats[h].draws += 1;
          stats[a].draws += 1;
        }
      }
    });

    clubIds.forEach(cid => {
      const row = stats[cid];
      const win_loss = row.wins + row.losses;
      row.win_rate = win_loss > 0 ? row.wins / win_loss : 0;
    });

    // 각 구단별 streak(연속 기록) 동적 계산
    clubIds.forEach(cid => {
      const clubMatches = eliteMatches
        .filter(m => m.status === 'COMPLETED' && (m.home_club_id === cid || m.away_club_id === cid))
        .sort((a, b) => b.sim_day - a.sim_day);

      let streak = 0;
      if (clubMatches.length > 0) {
        const firstMatch = clubMatches[0];
        const f_h = firstMatch.home_club_id;
        const f_h_score = firstMatch.home_score ?? 0;
        const f_a_score = firstMatch.away_score ?? 0;

        let isFirstWin = false;
        let isFirstLoss = false;

        if (f_h_score > f_a_score) {
          if (f_h === cid) isFirstWin = true;
          else isFirstLoss = true;
        } else if (f_h_score < f_a_score) {
          if (f_h !== cid) isFirstWin = true;
          else isFirstLoss = true;
        }

        if (isFirstWin) {
          streak = 1;
          for (let k = 1; k < clubMatches.length; k++) {
            const m = clubMatches[k];
            const h = m.home_club_id;
            const h_s = m.home_score ?? 0;
            const a_s = m.away_score ?? 0;
            const isWin = (h_s > a_s && h === cid) || (h_s < a_s && h !== cid);
            if (isWin) streak += 1;
            else break;
          }
        } else if (isFirstLoss) {
          streak = -1;
          for (let k = 1; k < clubMatches.length; k++) {
            const m = clubMatches[k];
            const h = m.home_club_id;
            const h_s = m.home_score ?? 0;
            const a_s = m.away_score ?? 0;
            const isLoss = (h_s < a_s && h === cid) || (h_s > a_s && h !== cid);
            if (isLoss) streak -= 1;
            else break;
          }
        }
      }
      stats[cid].streak = streak;
    });

    const list = Object.values(stats).sort((a, b) => {
      if (b.win_rate !== a.win_rate) return b.win_rate - a.win_rate;
      if (b.wins !== a.wins) return b.wins - a.wins;
      return a.club_id - b.club_id;
    });

    if (list.length === 0) return [];
    const leader = list[0];

    return list.map((item) => {
      const rank = list.findIndex(x => x.win_rate === item.win_rate && x.wins === item.wins) + 1;
      const games_back = (((leader.wins - item.wins) + (item.losses - leader.losses)) / 2) * 10;
      return { ...item, rank, games_back };
    });
  };

  // 5단계 토너먼트 대진 결과 집계 로직
  const getKnockoutResults = () => {
    if (!isKnockout) {
      return {
        q1: { round: 'ROUND_OF_8', id: 'q1', home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
        q2: { round: 'ROUND_OF_8', id: 'q2', home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
        q3: { round: 'ROUND_OF_8', id: 'q3', home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
        q4: { round: 'ROUND_OF_8', id: 'q4', home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
        s1: { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
        s2: { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
        f: { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null }
      };
    }

    const eliteStandings = getEliteStandings();
    const top8 = eliteStandings.slice(0, 8).map(r => r.club_id);
    const clubsList = Object.keys(clubsMap).map(Number).slice(0, 8);
    const t8 = top8.length === 8 ? top8 : clubsList;

    // 실제 knockoutMatches에서 8강 1차전 경기 4개를 순서대로 추출하여 대진 구단 매핑
    const minSimDay = knockoutMatches.length > 0 ? Math.min(...knockoutMatches.map(m => m.sim_day)) : 0;
    const q1stRoundMatches = knockoutMatches.filter(m => m.sim_day === minSimDay);

    const matchups = [
      { round: 'ROUND_OF_8', id: 'q1', home: q1stRoundMatches[0]?.home_club_id ?? t8[0], away: q1stRoundMatches[0]?.away_club_id ?? t8[7] },
      { round: 'ROUND_OF_8', id: 'q2', home: q1stRoundMatches[1]?.home_club_id ?? t8[3], away: q1stRoundMatches[1]?.away_club_id ?? t8[4] },
      { round: 'ROUND_OF_8', id: 'q3', home: q1stRoundMatches[2]?.home_club_id ?? t8[1], away: q1stRoundMatches[2]?.away_club_id ?? t8[6] },
      { round: 'ROUND_OF_8', id: 'q4', home: q1stRoundMatches[3]?.home_club_id ?? t8[2], away: q1stRoundMatches[3]?.away_club_id ?? t8[5] },
    ];

    // 1. 8강 각 대진의 구단 세트
    const q1_set = new Set([matchups[0].home, matchups[0].away]);
    const q2_set = new Set([matchups[1].home, matchups[1].away]);
    const q3_set = new Set([matchups[2].home, matchups[2].away]);
    const q4_set = new Set([matchups[3].home, matchups[3].away]);

    const getWins = (c1: number, c2: number) => {
      let c1_wins = 1; // 8강 상위시드 1승 선치
      let c2_wins = 0;
      knockoutMatches.forEach(m => {
        const h = m.home_club_id;
        const a = m.away_club_id;
        if (m.status === 'COMPLETED' && ((h === c1 && a === c2) || (h === c2 && a === c1))) {
          const winner = (m.home_score ?? 0) > (m.away_score ?? 0) ? h : a;
          if (winner === c1) c1_wins += 1;
          else c2_wins += 1;
        }
      });
      return { c1_wins, c2_wins };
    };

    const q1_res = getWins(matchups[0].home, matchups[0].away);
    const q1_winner = q1_res.c1_wins >= 2 ? matchups[0].home : (q1_res.c2_wins >= 2 ? matchups[0].away : null);

    const q2_res = getWins(matchups[1].home, matchups[1].away);
    const q2_winner = q2_res.c1_wins >= 2 ? matchups[1].home : (q2_res.c2_wins >= 2 ? matchups[1].away : null);

    const q3_res = getWins(matchups[2].home, matchups[2].away);
    const q3_winner = q3_res.c1_wins >= 2 ? matchups[2].home : (q3_res.c2_wins >= 2 ? matchups[2].away : null);

    const q4_res = getWins(matchups[3].home, matchups[3].away);
    const q4_winner = q4_res.c1_wins >= 2 ? matchups[3].home : (q4_res.c2_wins >= 2 ? matchups[3].away : null);

    const getHigherSeed = (c1: number | null, c2: number | null) => {
      if (!c1 || !c2) return { home: c1, away: c2 };
      const idx1 = t8.indexOf(c1);
      const idx2 = t8.indexOf(c2);
      return idx1 < idx2 ? { home: c1, away: c2 } : { home: c2, away: c1 };
    };

    // 2. 준결승 1경기(s1): q1 대진 구단 vs q2 대진 구단 간 경기 탐지
    let s1_home: number | null = getHigherSeed(q1_winner, q2_winner).home;
    let s1_away: number | null = getHigherSeed(q1_winner, q2_winner).away;

    if (!s1_home || !s1_away) {
      const matchS1 = knockoutMatches.find(m => 
        (q1_set.has(m.home_club_id) && q2_set.has(m.away_club_id)) ||
        (q2_set.has(m.home_club_id) && q1_set.has(m.away_club_id))
      );
      if (matchS1) {
        const higher = getHigherSeed(matchS1.home_club_id, matchS1.away_club_id);
        s1_home = higher.home;
        s1_away = higher.away;
      }
    }
    const s1_teams = { home: s1_home, away: s1_away };

    // 3. 준결승 2경기(s2): q3 대진 구단 vs q4 대진 구단 간 경기 탐지
    let s2_home: number | null = getHigherSeed(q3_winner, q4_winner).home;
    let s2_away: number | null = getHigherSeed(q3_winner, q4_winner).away;

    if (!s2_home || !s2_away) {
      const matchS2 = knockoutMatches.find(m => 
        (q3_set.has(m.home_club_id) && q4_set.has(m.away_club_id)) ||
        (q4_set.has(m.home_club_id) && q3_set.has(m.away_club_id))
      );
      if (matchS2) {
        const higher = getHigherSeed(matchS2.home_club_id, matchS2.away_club_id);
        s2_home = higher.home;
        s2_away = higher.away;
      }
    }
    const s2_teams = { home: s2_home, away: s2_away };

    const getWinsBo5 = (c1: number | null, c2: number | null) => {
      if (!c1 || !c2) return { c1_wins: 0, c2_wins: 0 };
      let c1_wins = 0, c2_wins = 0;
      knockoutMatches.forEach(m => {
        const h = m.home_club_id;
        const a = m.away_club_id;
        if (m.status === 'COMPLETED' && ((h === c1 && a === c2) || (h === c2 && a === c1))) {
          const winner = (m.home_score ?? 0) > (m.away_score ?? 0) ? h : a;
          if (winner === c1) c1_wins += 1;
          else c2_wins += 1;
        }
      });
      return { c1_wins, c2_wins };
    };

    const s1_res = getWinsBo5(s1_teams.home, s1_teams.away);
    const s1_winner = s1_res.c1_wins === 3 ? s1_teams.home : (s1_res.c2_wins === 3 ? s1_teams.away : null);

    const s2_res = getWinsBo5(s2_teams.home, s2_teams.away);
    const s2_winner = s2_res.c1_wins === 3 ? s2_teams.home : (s2_res.c2_wins === 3 ? s2_teams.away : null);

    // 4. 결승전(f): s1 참가 구단 vs s2 참가 구단 간 경기 탐지
    const s1_set = new Set([s1_teams.home, s1_teams.away].filter(Boolean) as number[]);
    const s2_set = new Set([s2_teams.home, s2_teams.away].filter(Boolean) as number[]);

    let f_home: number | null = getHigherSeed(s1_winner, s2_winner).home;
    let f_away: number | null = getHigherSeed(s1_winner, s2_winner).away;

    if (!f_home || !f_away) {
      const matchF = knockoutMatches.find(m => 
        (s1_set.has(m.home_club_id) && s2_set.has(m.away_club_id)) ||
        (s2_set.has(m.home_club_id) && s1_set.has(m.away_club_id))
      );
      if (matchF) {
        const higher = getHigherSeed(matchF.home_club_id, matchF.away_club_id);
        f_home = higher.home;
        f_away = higher.away;
      }
    }
    const f_teams = { home: f_home, away: f_away };

    const getWinsBo7 = (c1: number | null, c2: number | null) => {
      if (!c1 || !c2) return { c1_wins: 0, c2_wins: 0 };
      let c1_wins = 0, c2_wins = 0;
      knockoutMatches.forEach(m => {
        const h = m.home_club_id;
        const a = m.away_club_id;
        if (m.status === 'COMPLETED' && ((h === c1 && a === c2) || (h === c2 && a === c1))) {
          const winner = (m.home_score ?? 0) > (m.away_score ?? 0) ? h : a;
          if (winner === c1) c1_wins += 1;
          else c2_wins += 1;
        }
      });
      return { c1_wins, c2_wins };
    };

    const f_res = getWinsBo7(f_teams.home, f_teams.away);
    const f_winner = f_res.c1_wins === 4 ? f_teams.home : (f_res.c2_wins === 4 ? f_teams.away : null);

    return {
      q1: { ...matchups[0], wins: q1_res, winner: q1_winner },
      q2: { ...matchups[1], wins: q2_res, winner: q2_winner },
      q3: { ...matchups[2], wins: q3_res, winner: q3_winner },
      q4: { ...matchups[3], wins: q4_res, winner: q4_winner },
      s1: { ...s1_teams, wins: s1_res, winner: s1_winner },
      s2: { ...s2_teams, wins: s2_res, winner: s2_winner },
      f: { ...f_teams, wins: f_res, winner: f_winner }
    };
  };

  const renderBracket = () => {
    const data = getKnockoutResults();

    const getSeriesScores = (c1: number | null, c2: number | null, isBo3Advantage = false) => {
      if (!c1 || !c2) return { upperScores: [], lowerScores: [], matchIds: [] };
      const upperScores: number[] = [];
      const lowerScores: number[] = [];
      const matchIds: (number | null)[] = [];

      if (isBo3Advantage) {
        upperScores.push(1);
        lowerScores.push(0);
        matchIds.push(null);
      }

      const matches = knockoutMatches
        .filter(m => m.status === 'COMPLETED' && ((m.home_club_id === c1 && m.away_club_id === c2) || (m.home_club_id === c2 && m.away_club_id === c1)))
        .sort((a, b) => a.sim_day - b.sim_day);

      matches.forEach(m => {
        const isC1Home = m.home_club_id === c1;
        const c1Score = isC1Home ? (m.home_score ?? 0) : (m.away_score ?? 0);
        const c2Score = isC1Home ? (m.away_score ?? 0) : (m.home_score ?? 0);
        upperScores.push(c1Score);
        lowerScores.push(c2Score);
        matchIds.push(m.id);
      });

      return { upperScores, lowerScores, matchIds };
    };

    const renderNode = (title: string, homeId: number | null, awayId: number | null, isBo3Advantage = false, seriesLimit?: number) => {
      const homeClub = homeId ? clubsMap[homeId] : null;
      const awayClub = awayId ? clubsMap[awayId] : null;

      const homeName = homeClub ? (homeClub.abbr_name || homeClub.name_ko) : 'TBD';
      const awayName = awayClub ? (awayClub.abbr_name || awayClub.name_ko) : 'TBD';

      const homeSeed = homeId ? (seedMap[homeId] ? seedMap[homeId] : '') : '';
      const awaySeed = awayId ? (seedMap[awayId] ? seedMap[awayId] : '') : '';

      const homeCode = homeClub?.team_code;
      const awayCode = awayClub?.team_code;

      const { upperScores, lowerScores, matchIds } = getSeriesScores(homeId, awayId, isBo3Advantage);

      return (
        <MatchSeries
          stageTitle={title}
          seriesLimit={seriesLimit}
          upperSeedTitle={homeSeed}
          upperTeamName={homeName}
          upperTeamCode={homeCode}
          upperScoreSeries={upperScores}
          lowerSeedTitle={awaySeed}
          lowerTeamName={awayName}
          lowerTeamCode={awayCode}
          lowerScoreSeries={lowerScores}
          matchIds={matchIds}
        />
      );
    };

    return (
      <div className="bracket-view">
        <div className="bracket-col">
          <div className="bracket-col__header">8강전 (Bo3, 1승선취)</div>
          <div className="bracket-col__nodes">
            {renderNode("8강 1경기", data.q1.home, data.q1.away, true, 3)}
            {renderNode("8강 2경기", data.q2.home, data.q2.away, true, 3)}
            {renderNode("8강 3경기", data.q3.home, data.q3.away, true, 3)}
            {renderNode("8강 4경기", data.q4.home, data.q4.away, true, 3)}
          </div>
        </div>

        <div className="bracket-col">
          <div className="bracket-col__header">준결승전 (Bo5)</div>
          <div className="bracket-col__nodes">
            {renderNode("준결승 1경기", data.s1.home, data.s1.away, false, 5)}
            {renderNode("준결승 2경기", data.s2.home, data.s2.away, false, 5)}
          </div>
        </div>

        <div className="bracket-col">
          <div className="bracket-col__header">결승전 (Bo7)</div>
          <div className="bracket-col__nodes bracket-col__nodes--center">
            {renderNode("KROWN SERIES", data.f.home, data.f.away, false, 7)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <section className="section section--black section--first">
      <div className="section__container">
        {/* 시즌 진행 현황 5단계 스텝 바 */}
        <div className={`progress-status ${isSectionLoaded ? 'loaded' : 'loading'}`}>
          <div className="progress-status__season-title">KLB {seasonYear}</div>
          <div className="progress-status__steps">
            <div className={`progress-status__step progress-status__step--${selectedStep === 1 ? 'active' : 'inactive'} ${currentStep === 1 ? 'progress-status__step--current' : ''}`} onClick={() => setSelectedStep(1)}>
              <span className="progress-status__step-num">1</span>
              <span className="progress-status__step-text">
                정규리그 전반
                {currentStep === 1 && <FaCircle className="progress-status__current-dot" />}
              </span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 2 ? 'active' : 'inactive'} ${currentStep === 2 ? 'progress-status__step--current' : ''}`} onClick={() => setSelectedStep(2)}>
              <span className="progress-status__step-num">2</span>
              <span className="progress-status__step-text">
                인터리그
                {currentStep === 2 && <FaCircle className="progress-status__current-dot" />}
              </span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 3 ? 'active' : 'inactive'} ${currentStep === 3 ? 'progress-status__step--current' : ''}`} onClick={() => setSelectedStep(3)}>
              <span className="progress-status__step-num">3</span>
              <span className="progress-status__step-text">
                정규리그 후반
                {currentStep === 3 && <FaCircle className="progress-status__current-dot" />}
              </span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 4 ? 'active' : 'inactive'} ${currentStep === 4 ? 'progress-status__step--current' : ''}`} onClick={() => setSelectedStep(4)}>
              <span className="progress-status__step-num">4</span>
              <span className="progress-status__step-text">
                포스트 리그
                {currentStep === 4 && <FaCircle className="progress-status__current-dot" />}
              </span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 5 ? 'active' : 'inactive'} ${currentStep === 5 ? 'progress-status__step--current' : ''}`} onClick={() => setSelectedStep(5)}>
              <span className="progress-status__step-num">5</span>
              <span className="progress-status__step-text">
                포스트 파이널
                {currentStep === 5 && <FaCircle className="progress-status__current-dot" />}
              </span>
            </div>
          </div>
        </div>

        {/* 선택된 시즌 단계(selectedStep)에 따른 분기 렌더링 */}
        {selectedStep === 5 ? (
          <div className={`standings ${isSectionLoaded ? 'loaded' : 'loading'}`}>
            {renderBracket()}
          </div>
        ) : selectedStep === 4 ? (
          <div className={`standings ${isSectionLoaded ? 'loaded' : 'loading'}`}>
            <div className="standings__header">
              <h3 className="standings__title">
                {matchDate.getMonth() + 1}.{matchDate.getDate()} 크라운 정예리그
              </h3>
              <div className="standings__tabs">
                <button className="standings__tab standings__tab--active">
                  KROWN ELITE{hostLeagueName ? `: ${hostLeagueName}` : ''}
                </button>
              </div>
            </div>

            <div className="standings__table-wrapper">
              <table className="standings__table">
                <thead>
                  <tr>
                    <th className="standings__rank-col">순위</th>
                    <th className="standings__team-col">구단</th>
                    <th>경기</th>
                    <th>승</th>
                    <th>무</th>
                    <th>패</th>
                    <th>승률</th>
                    <th>게임차</th>
                    <th>연속</th>
                  </tr>
                </thead>
                <tbody>
                  {!isPostSeason ? (
                    Array.from({ length: 16 }).map((_, idx) => (
                      <tr key={`post-placeholder-${idx}`}>
                        <td className={`standings__rank ${idx < 8 ? 'standings__rank--playoff' : ''}`}>{idx + 1}</td>
                        <td className="standings__team-name">
                          <div className="standings__team-cell">
                            <TeamLogo teamName="?" size={20} />
                            <span className="standings__team-text" style={{ color: "rgba(255,255,255,0.4)" }}>TBD</span>
                          </div>
                        </td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td className="standings__pct">-</td>
                        <td>-</td>
                        <td>-</td>
                      </tr>
                    ))
                  ) : (
                    (eliteStandings.length > 0 ? eliteStandings : getEliteStandings()).map((row, idx) => {
                      const club = clubsMap[row.club_id];
                      const clubDisplayName = club ? (club.abbr_name || (club.hometown_ko ? `${club.hometown_ko} ${club.name_ko}` : club.name_ko)) : '로딩중...';
                      const teamCode = club ? club.team_code : '';
                      const seedText = seedMap[row.club_id] ? ` (${seedMap[row.club_id]})` : '';

                      return (
                        <tr key={`${row.club_id}-${idx}`}>
                          <td className={`standings__rank ${row.rank <= 8 ? 'standings__rank--playoff' : ''}`}>{row.rank}</td>
                          <td className="standings__team-name">
                            <div className="standings__team-cell">
                              <TeamLogo teamCode={teamCode} teamName={clubDisplayName} size={20} />
                              <span className="standings__team-text">
                                {clubDisplayName}
                                <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginLeft: '6px' }}>{seedText}</span>
                              </span>
                            </div>
                          </td>
                          <td>{row.games_played}</td>
                          <td>{row.wins}</td>
                          <td>{row.draws}</td>
                          <td>{row.losses}</td>
                          <td className="standings__pct">{formatPct(row.win_rate)}</td>
                          <td>{formatGb(row.games_back)}</td>
                          <td>{formatStreak(row.streak)}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : selectedStep === 2 ? (
          <div className={`standings ${isSectionLoaded ? 'loaded' : 'loading'}`}>
            <div className="standings__header">
              <h3 className="standings__title">KLB 인터리그</h3>
            </div>
            <div style={{ padding: '80px 16px', textAlign: 'center', color: 'rgba(255,255,255,0.35)', fontFamily: 'var(--sans)', fontSize: 'var(--fs-sm)' }}>
              현재 진행되거나 예정된 인터리그 일정이 존재하지 않습니다.
            </div>
          </div>
        ) : (
          <div className={`standings ${isSectionLoaded ? 'loaded' : 'loading'}`}>
            <div className="standings__header">
              <h3 className="standings__title">
                {matchDate.getMonth() + 1}.{matchDate.getDate()} {LEAGUES.find(l => l.code === activeLeague)?.name}
              </h3>
              <div className="standings__tabs">
                {LEAGUES.map((league) => (
                  <button
                    key={league.code}
                    className={`standings__tab ${activeLeague === league.code ? 'standings__tab--active' : ''}`}
                    onClick={() => setActiveLeague(league.code)}
                  >
                    {league.code}
                  </button>
                ))}
              </div>
            </div>

            <div className="standings__table-wrapper">
              <table className="standings__table">
                <thead>
                  <tr>
                    <th className="standings__rank-col">순위</th>
                    <th className="standings__team-col">구단</th>
                    <th>경기</th>
                    <th>승</th>
                    <th>무</th>
                    <th>패</th>
                    <th>승률</th>
                    <th>게임차</th>
                    <th>연속</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedStep === 3 && !isSecondHalf ? (
                    Array.from({ length: 10 }).map((_, idx) => (
                      <tr key={`secondhalf-placeholder-${idx}`}>
                        <td className="standings__rank">{idx + 1}</td>
                        <td className="standings__team-name">
                          <div className="standings__team-cell">
                            <TeamLogo teamName="?" size={20} />
                            <span className="standings__team-text" style={{ color: "rgba(255,255,255,0.4)" }}>TBD</span>
                          </div>
                        </td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td className="standings__pct">-</td>
                        <td>-</td>
                        <td>-</td>
                      </tr>
                    ))
                  ) : (() => {
                    const standingsList = allStandings[activeLeague];
                    const isZeroGames = !isOpening || standingsList.every(row => row.games_played === 0);

                    return standingsList.map((row, idx) => {
                      const club = clubsMap[row.club_id];
                      const clubDisplayName = club ? (club.abbr_name || (club.hometown_ko ? `${club.hometown_ko} ${club.name_ko}` : club.name_ko)) : '로딩중...';
                      const teamCode = club ? club.team_code : '';

                      const isTied = standingsList.filter(item => item.rank === row.rank).length > 1;
                      const displayRank = isZeroGames ? "-" : (isTied ? `T${row.rank}` : row.rank);

                      return (
                        <tr key={`${row.club_id}-${idx}`}>
                          <td className={`standings__rank ${!isZeroGames && row.rank <= 4 ? 'standings__rank--playoff' : ''}`}>{displayRank}</td>
                          <td className="standings__team-name">
                            <div className="standings__team-cell">
                              <TeamLogo teamCode={teamCode} teamName={clubDisplayName} size={20} />
                              <span className="standings__team-text">{clubDisplayName}</span>
                            </div>
                          </td>
                          <td>{isZeroGames ? "-" : row.games_played}</td>
                          <td>{isZeroGames ? "-" : row.wins}</td>
                          <td>{isZeroGames ? "-" : row.draws}</td>
                          <td>{isZeroGames ? "-" : row.losses}</td>
                          <td className="standings__pct">{isZeroGames ? "-" : formatPct(row.win_rate)}</td>
                          <td>{isZeroGames ? "-" : formatGb(row.games_back)}</td>
                          <td>{isZeroGames ? "-" : formatStreak(row.streak)}</td>
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
