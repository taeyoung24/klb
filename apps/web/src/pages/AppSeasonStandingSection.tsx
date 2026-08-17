import { useEffect, useState } from 'react'
import { getCalendarEvents, type CalendarEvent } from '../api/calendar'
import { getMatches, getMatchPlaceholders, type Match, type MatchPlaceholder } from '../api/matches'
import { getStandings, getLatestStandings, type DailyClubStanding } from '../api/standings'
import MatchSeries from '../components/MatchSeries/MatchSeries'
import TeamLogo from '../components/TeamLogo/TeamLogo'
import { useSystemContext } from '../context/SystemContext'
import './AppSeasonStandingSection.css'

const LEAGUES = [
  { code: 'AL' as const, id: 1, name: '아젤리아' },
  { code: 'CL' as const, id: 2, name: '카멜리아' },
  { code: 'GL' as const, id: 3, name: '젠티아나' },
  { code: 'ML' as const, id: 4, name: '매그놀리아' },
];

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
  const { clubsMap, hostLeagueName, hostLeagueId } = useSystemContext();

  const [activeLeague, setActiveLeague] = useState<'AL' | 'CL' | 'GL' | 'ML'>(() => {
    const saved = localStorage.getItem('klb_standing_active_league');
    if (saved && ['AL', 'CL', 'GL', 'ML'].includes(saved)) {
      return saved as 'AL' | 'CL' | 'GL' | 'ML';
    }
    return 'AL';
  });
  const [allStandings, setAllStandings] = useState<Record<'AL' | 'CL' | 'GL' | 'ML', DailyClubStanding[]>>({
    AL: [],
    CL: [],
    GL: [],
    ML: [],
  });
  const [isStandingsLoaded, setIsStandingsLoaded] = useState(false);

  const [selectedStep, setSelectedStep] = useState<number>(() => {
    const saved = localStorage.getItem('klb_standing_selected_step');
    if (saved) {
      const num = Number(saved);
      if (num >= 1 && num <= 5) return num;
    }
    return 1;
  });
  const [seedMap, setSeedMap] = useState<Record<number, string>>({});
  const [knockoutMatches, setKnockoutMatches] = useState<Match[]>([]);
  const [placeholders, setPlaceholders] = useState<MatchPlaceholder[]>([]);
  const [eliteStandings, setEliteStandings] = useState<DailyClubStanding[]>([]);
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [isEventsLoaded, setIsEventsLoaded] = useState(false);

  // 1. Fetch Calendar Events first
  useEffect(() => {
    setIsEventsLoaded(false);
    getCalendarEvents(seasonYear || undefined)
      .then(events => {
        setCalendarEvents(events);
        setIsEventsLoaded(true);
      })
      .catch(e => {
        console.error("Failed to load calendar events", e);
        setCalendarEvents([]);
        setIsEventsLoaded(true);
      });
  }, [seasonYear]);

  // Extract Milestone Events dynamically (No Fallback Strings)
  const openingEv = calendarEvents.find(e => e.label.includes('정규시즌 개막') || e.label.includes('개막'));
  const secondHalfEv = calendarEvents.find(e => e.label.includes('RS 후반기') || e.label.includes('후반기'));
  const eliteEv = calendarEvents.find(e =>
    e.event_type === 'ELITE_LEAGUE' ||
    e.label.includes('PS 개막') ||
    e.label.includes('EL 1일차') ||
    e.label.includes('크라운 정예리그') ||
    e.label.includes('정예리그')
  );
  const knockoutEv = calendarEvents.find(e =>
    e.label.includes('PS 8강') ||
    e.label.includes('8강 1차전') ||
    e.label.includes('포스트시즌 8강')
  );

  const matchDateStr = `${matchDate.getFullYear()}-${String(matchDate.getMonth() + 1).padStart(2, '0')}-${String(matchDate.getDate()).padStart(2, '0')}`;

  // 2. Fetch Regular Season Standings
  useEffect(() => {
    setIsStandingsLoaded(false);

    const isPostseasonDate = eliteEv ? matchDateStr >= eliteEv.date : false;

    if (isPostseasonDate) {
      // 포스트시즌 기간에는 정규시즌 최종 스탠딩을 한 번에 조회
      getLatestStandings({ year: seasonYear || undefined, isPostseason: false })
        .then(allData => {
          setAllStandings({
            AL: allData.filter(r => r.league_id === 1),
            CL: allData.filter(r => r.league_id === 2),
            GL: allData.filter(r => r.league_id === 3),
            ML: allData.filter(r => r.league_id === 4),
          });
          setIsStandingsLoaded(true);
        })
        .catch(e => {
          console.error("Failed to fetch latest regular season standings", e);
          setIsStandingsLoaded(true);
        });
    } else {
      // 정규시즌 중 특정 날짜 조회
      Promise.all(
        LEAGUES.map(league => getStandings(league.id, undefined, false, matchDateStr))
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
    }
  }, [matchDate, seasonYear, matchDateStr, eliteEv]);

  // 3. Fetch Elite Standings snapshot dynamically when in postseason
  useEffect(() => {
    const isPostseasonDate = eliteEv ? matchDateStr >= eliteEv.date : false;
    if (isPostseasonDate) {
      getStandings(hostLeagueId, undefined, true, matchDateStr)
        .then(data => {
          if (data && data.length > 0) {
            setEliteStandings(data);
          } else {
            getLatestStandings({ year: seasonYear || undefined, isPostseason: true })
              .then(latest => setEliteStandings(latest))
              .catch(() => setEliteStandings([]));
          }
        })
        .catch(() => {
          getLatestStandings({ year: seasonYear || undefined, isPostseason: true })
            .then(latest => setEliteStandings(latest))
            .catch(() => setEliteStandings([]));
        });
    }
  }, [matchDateStr, seasonYear, hostLeagueId, eliteEv]);

  // 4. Fetch Post-season Matches, Placeholders, and Seed Map dynamically
  useEffect(() => {
    if (!isEventsLoaded) return;

    // 정규시즌 최종 순위 스냅샷으로부터 1~4위 시드 맵을 단 1회 쿼리로 생성
    getLatestStandings({ year: seasonYear || undefined, isPostseason: false })
      .then(results => {
        const map: Record<number, string> = {};
        const leagueMapById: Record<number, string> = { 1: 'AL', 2: 'CL', 3: 'GL', 4: 'ML' };
        results.forEach(row => {
          if (row.rank <= 4) {
            const code = leagueMapById[row.league_id] || 'AL';
            map[row.club_id] = `${code}#${row.rank}`;
          }
        });
        setSeedMap(map);
      })
      .catch(e => console.error("Failed to load final standings for seeds", e));

    getMatchPlaceholders(seasonYear || undefined)
      .then(data => setPlaceholders(data))
      .catch(e => console.error("Failed to load match placeholders", e));

    getMatches({ year: seasonYear || 2026 })
      .then(matches => {
        const ko = matches.filter(m => m.stage === 'KNOCKOUT');
        setKnockoutMatches(ko);
      })
      .catch(e => console.error("Failed to load post-season matches", e));
  }, [seasonYear, isEventsLoaded]);

  const isSectionLoaded = isSeasonYearLoaded && isStandingsLoaded && isEventsLoaded && Object.keys(clubsMap).length > 0;

  const isOpening = openingEv ? matchDateStr >= openingEv.date : true;
  const isSecondHalf = secondHalfEv ? matchDateStr >= secondHalfEv.date : false;
  const isPostSeason = eliteEv ? matchDateStr >= eliteEv.date : false;
  const isKnockout = knockoutEv
    ? matchDateStr >= knockoutEv.date
    : knockoutMatches.length > 0 && knockoutMatches.some(m => m.status === 'COMPLETED');

  let currentStep = 1;
  if (!isSecondHalf) {
    currentStep = 1;
  } else if (!isPostSeason) {
    currentStep = 3;
  } else if (!isKnockout) {
    currentStep = 4;
  } else {
    currentStep = 5;
  }

  const handleSelectStep = (step: number) => {
    setSelectedStep(step);
    localStorage.setItem('klb_standing_selected_step', String(step));
  };

  const handleSelectLeague = (leagueCode: 'AL' | 'CL' | 'GL' | 'ML') => {
    setActiveLeague(leagueCode);
    localStorage.setItem('klb_standing_active_league', leagueCode);
  };

  // 저장된 사용자 선택이 없을 때만 현재 날짜 단계(currentStep)로 초기화
  useEffect(() => {
    const saved = localStorage.getItem('klb_standing_selected_step');
    if (!saved) {
      setSelectedStep(currentStep);
    }
  }, [currentStep]);

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

    const top8 = eliteStandings.slice(0, 8).map(r => r.club_id);
    const clubsList = Object.keys(clubsMap).map(Number).slice(0, 8);
    const t8 = top8.length === 8 ? top8 : clubsList;

    // 시리즈 승수 집계 헬퍼
    const getWinsCount = (c1: number | null, c2: number | null, isBo3Advantage = false) => {
      if (!c1 || !c2) return { c1_wins: isBo3Advantage ? 1 : 0, c2_wins: 0 };
      let c1_wins = isBo3Advantage ? 1 : 0;
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

    // placeholders DB 데이터를 이용한 정확한 트레이싱 및 대진 바인딩
    const qList = placeholders.filter(p => p.round === 'ROUND_OF_8').sort((a, b) => a.id - b.id);
    const sList = placeholders.filter(p => p.round === 'SEMI_FINAL').sort((a, b) => a.id - b.id);
    const fList = placeholders.filter(p => p.round === 'FINAL');

    // 8강전 (q1~q4)
    const q_nodes = qList.map((p, idx) => {
      const home = p.home_club_id ?? t8[idx] ?? null;
      const away = p.away_club_id ?? t8[7 - idx] ?? null;
      const wins = getWinsCount(home, away, true);
      const winner = wins.c1_wins >= 2 ? home : (wins.c2_wins >= 2 ? away : null);
      return { id: `q${idx + 1}`, home, away, wins, winner, pId: p.id };
    });

    const qMap = new Map(q_nodes.map(n => [n.pId, n]));

    // 4강/준결승전 (s1, s2)
    const s_nodes = sList.map((p, idx) => {
      const homeParent = p.home_parent_id ? qMap.get(p.home_parent_id) : null;
      const awayParent = p.away_parent_id ? qMap.get(p.away_parent_id) : null;

      const home = p.home_club_id ?? homeParent?.winner ?? null;
      const away = p.away_club_id ?? awayParent?.winner ?? null;

      const wins = getWinsCount(home, away, false);
      const winner = wins.c1_wins >= 3 ? home : (wins.c2_wins >= 3 ? away : null);
      return { id: `s${idx + 1}`, home, away, wins, winner, pId: p.id };
    });

    const sMap = new Map(s_nodes.map(n => [n.pId, n]));

    // 결승전 (f)
    const fP = fList[0];
    const fHomeParent = fP?.home_parent_id ? sMap.get(fP.home_parent_id) : null;
    const fAwayParent = fP?.away_parent_id ? sMap.get(fP.away_parent_id) : null;

    const fHome = fP?.home_club_id ?? fHomeParent?.winner ?? null;
    const fAway = fP?.away_club_id ?? fAwayParent?.winner ?? null;

    const fWins = getWinsCount(fHome, fAway, false);
    const fWinner = fWins.c1_wins >= 4 ? fHome : (fWins.c2_wins >= 4 ? fAway : null);

    return {
      q1: q_nodes[0] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      q2: q_nodes[1] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      q3: q_nodes[2] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      q4: q_nodes[3] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      s1: s_nodes[0] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      s2: s_nodes[1] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      f: { home: fHome, away: fAway, wins: fWins, winner: fWinner }
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
      <div className={`section__container ${isSectionLoaded ? 'section__container--loaded' : 'section__container--loading'}`}>
        {/* 시즌 진행 현황 5단계 스텝 바 */}
        <div className={`progress-status ${isSectionLoaded ? 'loaded' : 'loading'}`}>
          <div className="progress-status__season-title">KLB {seasonYear}</div>
          <div className="progress-status__steps">
            <div className={`progress-status__step progress-status__step--${selectedStep === 1 ? 'active' : 'inactive'} ${currentStep === 1 ? 'progress-status__step--current' : ''}`} onClick={() => handleSelectStep(1)}>
              <span className="progress-status__step-num">1</span>
              <span className="progress-status__step-text">정규리그 전반</span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 2 ? 'active' : 'inactive'} ${currentStep === 2 ? 'progress-status__step--current' : ''}`} onClick={() => handleSelectStep(2)}>
              <span className="progress-status__step-num">2</span>
              <span className="progress-status__step-text">인터리그</span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 3 ? 'active' : 'inactive'} ${currentStep === 3 ? 'progress-status__step--current' : ''}`} onClick={() => handleSelectStep(3)}>
              <span className="progress-status__step-num">3</span>
              <span className="progress-status__step-text">정규리그 후반</span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 4 ? 'active' : 'inactive'} ${currentStep === 4 ? 'progress-status__step--current' : ''}`} onClick={() => handleSelectStep(4)}>
              <span className="progress-status__step-num">4</span>
              <span className="progress-status__step-text">포스트 리그</span>
            </div>
            <div className="progress-status__connector"></div>
            <div className={`progress-status__step progress-status__step--${selectedStep === 5 ? 'active' : 'inactive'} ${currentStep === 5 ? 'progress-status__step--current' : ''}`} onClick={() => handleSelectStep(5)}>
              <span className="progress-status__step-num">5</span>
              <span className="progress-status__step-text">포스트 파이널</span>
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
                    eliteStandings.map((row, idx) => {
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
                    onClick={() => handleSelectLeague(league.code)}
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
                    const isZeroGames = !isOpening || (standingsList.length > 0 && standingsList.every(row => row.games_played === 0));

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
