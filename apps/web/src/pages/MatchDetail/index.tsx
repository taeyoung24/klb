import { useEffect, useState } from 'react';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { getClubs, type Club } from '../../api/clubs';
import {
  getMatch,
  getMatchAnalysis,
  getMatches,
  getMatchLineup,
  getMatchPlaceholders,
  getMatchScoreboard,
  type IngameScoreboard,
  type Match,
  type MatchAnalysisData,
  type MatchDetailData,
  type MatchLineupItem,
  type MatchLineupResponse,
  type MatchPlaceholder,
} from '../../api/matches';
import { getPlayers, type Player } from '../../api/players';
import { getSystemInfo } from '../../api/system';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';
import TeamLogo from '../../components/TeamLogo/TeamLogo';
import { simDayToDate } from '../../utils/date';
import './index.css';

import AnalysisTab from './AnalysisTab';
import BoxscoreTab from './BoxscoreTab';
import BroadcastTab from './BroadcastTab';
import LineupTab from './LineupTab';
import NewsTab from './NewsTab';

const POSITION_CODE_MAP: Record<string, string> = {
  PITCHER: 'P',
  CATCHER: 'C',
  FIRST_BASE: '1B',
  SECOND_BASE: '2B',
  THIRD_BASE: '3B',
  SHORT_STOP: 'SS',
  LEFT_FIELD: 'LF',
  CENTER_FIELD: 'CF',
  RIGHT_FIELD: 'RF',
  DESIGNATED_HITTER: 'DH',
};

const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];

const LEAGUE_INFO: Record<number, { name: string; code: string }> = {
  1: { name: '아젤리아', code: 'AL' },
  2: { name: '카멜리아', code: 'CL' },
  3: { name: '젠티아나', code: 'GL' },
  4: { name: '매그놀리아', code: 'ML' },
};

const getMatchTitle = (
  match: Match | null,
  homeClub: Club | null,
  seasonYear: number | null,
  placeholders: MatchPlaceholder[] = []
): string => {
  if (!match) return `${seasonYear || 2026} KLB 정규리그`;

  const isKnockout = match.stage === 'KNOCKOUT';
  const isElite = match.stage === 'ELITE';

  // 1. 녹아웃 토너먼트 경기 (8강전 / 준결승전 / 결승전)
  if (isKnockout) {
    const ph = placeholders.find(p => p.actual_match_id === match.id);
    if (ph) {
      if (ph.round === 'ROUND_OF_8') return `${seasonYear} 포스트시즌 8강전`;
      if (ph.round === 'SEMI_FINAL') return `${seasonYear} 포스트시즌 준결승전`;
      if (ph.round === 'FINAL') return `${seasonYear} 포스트시즌 결승전 (KROWN SERIES)`;
    }

    const knockoutPlaceholders = placeholders.filter(p => p.limit_extra_innings === false);
    const minKoDay = knockoutPlaceholders.length > 0 ? Math.min(...knockoutPlaceholders.map(p => p.sim_day)) : 261;

    if (match.sim_day >= minKoDay + 8) {
      return `${seasonYear} KROWN SERIES`;
    } else if (match.sim_day >= minKoDay + 3) {
      return `${seasonYear} 포스트시즌 준결승전`;
    } else {
      return `${seasonYear} 포스트시즌 8강전`;
    }
  }

  // 2. 크라운 정예리그 경기
  if (isElite) {
    return `${seasonYear} 포스트시즌 정예리그`;
  }

  // 3. 정규시즌 및 기타 경기
  const leagueId = homeClub?.league_id || 1;
  const league = LEAGUE_INFO[leagueId] || { name: '아젤리아', code: 'AL' };
  return `${league.name} 정규리그 | ${league.code}`;
};

const formatNavDate = (date: Date | null) => {
  if (!date) return '-';
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const dayName = DAY_NAMES[date.getDay()];
  return `${month}.${day} ${dayName}`;
};

const formatFullDateStr = (date: Date | null) => {
  if (!date) return '-';
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const dayName = DAY_NAMES[date.getDay()];
  const dayOfWeek = date.getDay();
  const timeStr = dayOfWeek === 0 ? '14:00' : dayOfWeek === 6 ? '17:00' : '18:30';
  return `${year}년 ${month}월 ${day}일 (${dayName}) ${timeStr}`;
};

const getMatchIdFromHash = (): number | null => {
  const hash = window.location.hash;
  if (!hash.includes('?')) return null;
  const queryString = hash.split('?')[1];
  const params = new URLSearchParams(queryString);
  const idStr = params.get('id') || params.get('matchId') || params.get('match_id');
  return idStr ? Number(idStr) : null;
};

export default function MatchDetail() {
  const [activeTab, setActiveTab] = useState<'analysis' | 'lineup' | 'boxscore' | 'broadcast' | 'news'>('analysis');
  const [navDate, setNavDate] = useState<Date | null>(null);
  const [seasonYear, setSeasonYear] = useState<number | null>(null);

  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [currentDayMatches, setCurrentDayMatches] = useState<Match[]>([]);
  const [isMatchesLoading, setIsMatchesLoading] = useState<boolean>(false);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [scoreboard, setScoreboard] = useState<IngameScoreboard | null>(null);
  const [matchDetailData, setMatchDetailData] = useState<MatchDetailData | null>(null);
  const [lineupData, setLineupData] = useState<MatchLineupResponse | null>(null);
  const [analysisApiData, setAnalysisApiData] = useState<MatchAnalysisData | null>(null);
  const [playersMap, setPlayersMap] = useState<Record<number, Player>>({});
  const [placeholders, setPlaceholders] = useState<MatchPlaceholder[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);

  useEffect(() => {
    getMatchPlaceholders()
      .then(list => setPlaceholders(list))
      .catch(e => console.error("Failed to load match placeholders in MatchDetail", e));
  }, []);

  // 초기 시스템 및 구단 정보, 타겟 매치 로드
  useEffect(() => {
    setIsLoading(true);
    Promise.all([getClubs(), getSystemInfo()])
      .then(async ([clubsList, sysInfo]) => {
        const cMap: Record<number, Club> = {};
        clubsList.forEach((c) => {
          cMap[c.id] = c;
        });
        setClubsMap(cMap);

        const sysYear = sysInfo?.season_year || 2026;
        setSeasonYear(sysYear);

        const targetMatchId = getMatchIdFromHash();
        if (targetMatchId) {
          try {
            const m = await getMatch(targetMatchId);
            setSelectedMatchId(m.id);
            const matchDate = simDayToDate(m.sim_day);
            setNavDate(matchDate);
          } catch (e) {
            console.error("Failed to fetch target match", e);
            const currentSimDay = sysInfo?.current_sim_day || 1;
            setNavDate(simDayToDate(currentSimDay));
          }
        } else if (sysInfo) {
          const currentSimDay = sysInfo.current_sim_day || 1;
          setNavDate(simDayToDate(currentSimDay));
        }
        setIsLoading(false);
      })
      .catch((e) => {
        console.error('Failed to load initial match detail data', e);
        setIsLoading(false);
      });
  }, []);

  // 탐색 날짜(navDate)가 실제로 결정된 후 해당 날짜의 경기만 fetch (탐색 패널 전용)
  useEffect(() => {
    if (!navDate || !seasonYear) return;

    const dateStr = `${navDate.getFullYear()}-${String(navDate.getMonth() + 1).padStart(2, '0')}-${String(navDate.getDate()).padStart(2, '0')}`;
    setIsMatchesLoading(true);
    getMatches({ date: dateStr })
      .then((matchesList) => {
        setCurrentDayMatches(matchesList);
        setIsMatchesLoading(false);
      })
      .catch((e) => {
        console.error('Failed to fetch matches for navDate', e);
        setIsMatchesLoading(false);
      });
  }, [navDate, seasonYear]);

  useEffect(() => {
    if (selectedMatchId) {
      setIsDetailLoading(true);
      Promise.all([
        getMatchScoreboard(selectedMatchId).catch((e) => {
          console.error('Failed to load scoreboard', e);
          return null;
        }),
        getMatch(selectedMatchId).catch((e) => {
          console.error('Failed to load match detail log', e);
          return null;
        }),
        getMatchLineup(selectedMatchId).catch((e) => {
          console.error('Failed to load match lineup', e);
          return null;
        }),
        getMatchAnalysis(selectedMatchId).catch((e) => {
          console.error('Failed to load match analysis', e);
          return null;
        }),
      ])
        .then(([sb, detail, lineup, analysis]) => {
          setScoreboard(sb);
          setMatchDetailData(detail);
          setLineupData(lineup);
          if (analysis) {
            setAnalysisApiData(analysis);
          }
        })
        .finally(() => {
          setIsDetailLoading(false);
        });
    }
  }, [selectedMatchId]);

  // 현재 선택된 경기 구하기 (메인 매치는 탐색 날짜와 독립적으로 보장)
  const currentMatch = (matchDetailData as unknown as Match | null) || currentDayMatches.find((m) => m.id === selectedMatchId) || null;

  // 팀 정보 매핑
  const awayClub = currentMatch ? clubsMap[currentMatch.away_club_id] : null;
  const homeClub = currentMatch ? clubsMap[currentMatch.home_club_id] : null;

  useEffect(() => {
    if (awayClub?.id || homeClub?.id) {
      const promises: Promise<Player[]>[] = [];
      if (awayClub?.id) promises.push(getPlayers({ club_id: awayClub.id }).catch(() => []));
      if (homeClub?.id) promises.push(getPlayers({ club_id: homeClub.id }).catch(() => []));

      Promise.all(promises).then((results) => {
        const pMap: Record<number, Player> = {};
        results.flat().forEach((p) => {
          pMap[p.id] = p;
        });
        setPlayersMap((prev) => ({ ...prev, ...pMap }));
      });
    }
  }, [awayClub?.id, homeClub?.id]);

  const handlePrevDay = () => {
    setNavDate((prev) => (prev ? new Date(prev.getFullYear(), prev.getMonth(), prev.getDate() - 1) : null));
  };

  const handleNextDay = () => {
    setNavDate((prev) => (prev ? new Date(prev.getFullYear(), prev.getMonth(), prev.getDate() + 1) : null));
  };

  // 경기 상태 변환
  const parseMatchStatus = (statusStr?: string) => {
    if (statusStr === 'COMPLETED' || statusStr === '종료' || statusStr === '경기 종료') return '종료';
    if (statusStr === 'IN_PROGRESS' || statusStr === 'LIVE' || statusStr === '진행중' || statusStr === '경기 진행중') return '진행중';
    if (statusStr === 'CANCELED' || statusStr === '취소' || statusStr === '경기 취소') return '취소';
    return '예정';
  };

  const currentStatusText = parseMatchStatus(currentMatch?.status);

  const getStatusBadgeInfo = (status: string) => {
    if (status === '진행중' || status === 'LIVE') {
      return { label: 'LIVE', modifier: 'live' };
    }
    if (status === '종료') {
      return { label: '종료', modifier: 'ended' };
    }
    if (status === '취소') {
      return { label: '취소', modifier: 'ended' };
    }
    return { label: '예정', modifier: 'upcoming' };
  };

  const statusInfo = getStatusBadgeInfo(currentStatusText);

  // 매치 타이틀 (정규시즌 / 포스트시즌 / 녹아웃 조건부 포맷)
  const matchTitle = getMatchTitle(currentMatch, homeClub, seasonYear, placeholders);

  // 경기 일자 및 구장
  const matchDateObj = currentMatch ? simDayToDate(currentMatch.sim_day) : navDate;
  const matchDateText = formatFullDateStr(matchDateObj);
  const matchStadiumText = currentMatch?.stadium?.name || (homeClub ? homeClub.stadium_name_ko || `${homeClub.hometown_ko} 야구장` : '서울 잠실야구장');

  // 경기 점수 & 이닝 데이터
  const awayScore = currentMatch?.away_score ?? 0;
  const homeScore = currentMatch?.home_score ?? 0;

  const targetMatch = matchDetailData || currentMatch;

  const getPitcherName = (pitcherId?: number | null) => {
    if (!pitcherId) return '-';
    const player = playersMap[pitcherId];
    if (!player) return `선수 #${pitcherId}`;
    return player.name;
  };

  const pitchRecords = {
    winPitcher: getPitcherName(targetMatch?.winning_pitcher_id),
    losePitcher: getPitcherName(targetMatch?.losing_pitcher_id),
    savePitcher: getPitcherName(targetMatch?.save_pitcher_id),
  };

  const formatLineupList = (lineupItems: MatchLineupItem[]) => {
    return lineupItems.map((item) => {
      const player = playersMap[item.player_id];
      const posCode = POSITION_CODE_MAP[item.position] || item.position || 'P';
      const orderLabel = item.batting_order ? String(item.batting_order) : '선발';
      const playerName = player ? player.name : `선수 #${item.player_id}`;

      return {
        orderLabel,
        posCode,
        name: playerName,
      };
    });
  };

  const lineups = {
    away: lineupData?.away_lineup ? formatLineupList(lineupData.away_lineup) : [],
    home: lineupData?.home_lineup ? formatLineupList(lineupData.home_lineup) : [],
  };

  const newsList = [
    { title: `[Match Review] ${awayClub?.name_ko || '어웨이'} vs ${homeClub?.name_ko || '홈'} 치열한 명승부 전개`, time: '1시간 전', category: '리뷰' },
    { title: '[Interview] 감독 청사진 "선수단의 집중력이 빛난 경기였다"', time: '2시간 전', category: '인터뷰' },
    { title: '[Highlight] 경기 분위기를 바꾼 결정적인 호수비 명장면', time: '3시간 전', category: '하이라이트' },
  ];

  if (isLoading) {
    return (
      <div className="match-detail" style={{ position: 'relative', minHeight: '600px' }}>
        <LoadingSpinner message="데이터를 불러오는 중입니다..." dimmed={true} />
      </div>
    );
  }

  // 동적 이닝 수 계산 (최소 9이닝 기본, 연장전 발생 시 10, 11, 12... 이닝으로 유연 확장)
  const totalInningsCount = Math.max(
    9,
    scoreboard?.away_innings?.length || 0,
    scoreboard?.home_innings?.length || 0
  );
  const inningsHeaderList = Array.from({ length: totalInningsCount }, (_, i) => i + 1);

  return (
    <div className="match-detail">
      <div className="match-detail__container" style={{ position: 'relative' }}>
        {isDetailLoading && (
          <LoadingSpinner message="데이터를 불러오는 중입니다..." dimmed={true} />
        )}
        {/* 상단 경기 정보 서머리 & 이닝별 스코어보드 */}
        <header className="match-detail__header">
          <div className="match-detail__header-layout">
            {/* 좌측: 컴팩트 스코어 & 이닝 스코어보드 */}
            <div className="match-detail__header-main">
              {/* 상단 리그 & 경기 정보 바 */}
              <div className="match-detail__top-meta">
                <span className="match-detail__top-league">{matchTitle}</span>
                <span className="match-detail__top-info">{matchDateText} | {matchStadiumText}</span>
              </div>

              <div className="match-detail__hero">
                {/* 원정팀 (flex: 1) */}
                <div className="match-detail__team match-detail__team--away">
                  <TeamLogo teamCode={awayClub?.team_code} teamName={awayClub?.name_ko || '원정팀'} size={52} />
                  <div className="match-detail__team-info match-detail__team-info--away">
                    <span className="match-detail__team-name">
                      {awayClub ? `${awayClub.hometown_ko} ${awayClub.name_ko}` : '원정팀'}
                    </span>
                    <span className="match-detail__team-code">{awayClub?.abbr_name || awayClub?.team_code || 'AWAY'}</span>
                  </div>
                  <span className="match-detail__score match-detail__score--away">{awayScore}</span>
                </div>

                {/* 중앙 경기 상태 배지 */}
                <div className="match-detail__center-status">
                  <span className={`match-detail__status-badge match-detail__status-badge--${statusInfo.modifier}`}>
                    {statusInfo.label}
                  </span>
                </div>

                {/* 홈팀 (flex: 1) */}
                <div className="match-detail__team match-detail__team--home">
                  <span className="match-detail__score match-detail__score--home">{homeScore}</span>
                  <div className="match-detail__team-info match-detail__team-info--home">
                    <span className="match-detail__team-name">
                      {homeClub ? `${homeClub.hometown_ko} ${homeClub.name_ko}` : '홈팀'}
                      <span className="match-detail__home-label">홈</span>
                    </span>
                    <span className="match-detail__team-code">{homeClub?.abbr_name || homeClub?.team_code || 'HOME'}</span>
                  </div>
                  <TeamLogo teamCode={homeClub?.team_code} teamName={homeClub?.name_ko || '홈팀'} size={52} />
                </div>
              </div>

              {/* 가로형 이닝별 스코어보드 (동적 연장전 이닝 지원) */}
              <div className="match-detail__table-wrapper">
                <table className="match-detail__scoreboard-table">
                  <thead>
                    <tr>
                      <th className="match-detail__th-team">팀</th>
                      {inningsHeaderList.map((i) => (
                        <th key={i}>{i}</th>
                      ))}
                      <th className="match-detail__th-stat">R</th>
                      <th className="match-detail__th-stat">H</th>
                      <th className="match-detail__th-stat">E</th>
                      <th className="match-detail__th-stat">B</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="match-detail__td-team">
                        <span className="match-detail__team-indicator" style={{ backgroundColor: '#888888' }}></span>
                        {awayClub?.name_ko || '원정팀'}
                      </td>
                      {inningsHeaderList.map((_, idx) => (
                        <td key={idx}>{scoreboard?.away_innings?.[idx] ?? '-'}</td>
                      ))}
                      <td className="match-detail__td-stat match-detail__td-stat--highlight">
                        {scoreboard ? scoreboard.away_r : awayScore}
                      </td>
                      <td className="match-detail__td-stat">{scoreboard ? scoreboard.away_h : 0}</td>
                      <td className="match-detail__td-stat">{scoreboard ? scoreboard.away_e : 0}</td>
                      <td className="match-detail__td-stat">{scoreboard ? scoreboard.away_b : 0}</td>
                    </tr>
                    <tr>
                      <td className="match-detail__td-team">
                        <span className="match-detail__team-indicator" style={{ backgroundColor: '#cccccc' }}></span>
                        {homeClub?.name_ko || '홈팀'}
                      </td>
                      {inningsHeaderList.map((_, idx) => (
                        <td key={idx}>{scoreboard?.home_innings?.[idx] ?? '-'}</td>
                      ))}
                      <td className="match-detail__td-stat match-detail__td-stat--highlight">
                        {scoreboard ? scoreboard.home_r : homeScore}
                      </td>
                      <td className="match-detail__td-stat">{scoreboard ? scoreboard.home_h : 0}</td>
                      <td className="match-detail__td-stat">{scoreboard ? scoreboard.home_e : 0}</td>
                      <td className="match-detail__td-stat">{scoreboard ? scoreboard.home_b : 0}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* 우측: 다른 경기 탐색 패널 (실제 API 데이터 기반) */}
            <div className="match-detail__other-matches-panel">
              <div className="match-detail__nav-header">
                <button className="match-detail__nav-arrow-btn" onClick={handlePrevDay} aria-label="이전 날짜">
                  <FaChevronLeft />
                </button>
                <span className="match-detail__nav-date-text">{formatNavDate(navDate)}</span>
                <button className="match-detail__nav-arrow-btn" onClick={handleNextDay} aria-label="다음 날짜">
                  <FaChevronRight />
                </button>
              </div>

              <div className={`match-detail__nav-content ${isMatchesLoading ? 'match-detail__nav-content--loading' : 'match-detail__nav-content--loaded'}`}>
                {currentDayMatches && currentDayMatches.length > 0 ? (
                  <div className="match-detail__other-matches-list">
                    {currentDayMatches.map((m) => {
                      const awayC = clubsMap[m.away_club_id];
                      const homeC = clubsMap[m.home_club_id];
                      const isCurr = currentMatch ? m.id === currentMatch.id : false;
                      const statusText = parseMatchStatus(m.status);

                      return (
                        <div
                          key={m.id}
                          className={`match-detail__other-match-card ${isCurr ? 'match-detail__other-match-card--current' : ''}`}
                          style={{ cursor: 'pointer' }}
                          onClick={() => setSelectedMatchId(m.id)}
                        >
                          <div className="match-detail__other-match-team">
                            <TeamLogo teamCode={awayC?.team_code} teamName={awayC?.name_ko || '어웨이'} size={20} />
                            <span className="match-detail__other-match-team-name">{awayC?.team_code || awayC?.name_ko || 'AWAY'}</span>
                            {m.away_score !== undefined && m.away_score !== null && (
                              <span className="match-detail__other-match-score">{m.away_score}</span>
                            )}
                          </div>
                          <div className="match-detail__other-match-vs">
                            <span className="match-detail__other-match-status">{statusText}</span>
                          </div>
                          <div className="match-detail__other-match-team match-detail__other-match-team--home">
                            {m.home_score !== undefined && m.home_score !== null && (
                              <span className="match-detail__other-match-score">{m.home_score}</span>
                            )}
                            <span className="match-detail__other-match-team-name">{homeC?.team_code || homeC?.name_ko || 'HOME'}</span>
                            <TeamLogo teamCode={homeC?.team_code} teamName={homeC?.name_ko || '홈'} size={20} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="match-detail__no-matches">경기가 없습니다</div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* 메인 콘텐츠 바디 (탭 내비게이션 + 탭 상세 콘텐츠) */}
        <section className="match-detail__body">
          {/* 탭 네비게이션 */}
          <nav className="match-detail__nav">
            <button
              className={`match-detail__tab-btn ${activeTab === 'analysis' ? 'match-detail__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              전력 분석
            </button>
            <button
              className={`match-detail__tab-btn ${activeTab === 'lineup' ? 'match-detail__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('lineup')}
            >
              선발 라인업
            </button>
            <button
              className={`match-detail__tab-btn ${activeTab === 'boxscore' ? 'match-detail__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('boxscore')}
            >
              주요 기록
            </button>
            <button
              className={`match-detail__tab-btn ${activeTab === 'broadcast' ? 'match-detail__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('broadcast')}
            >
              중계
            </button>
            <button
              className={`match-detail__tab-btn ${activeTab === 'news' ? 'match-detail__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('news')}
            >
              관련 뉴스
            </button>
          </nav>

          {/* 싱글 컬럼 탭 컨텐츠 */}
          <main key={selectedMatchId || 'default'} className="match-detail__content">
            {activeTab === 'analysis' && (
              <AnalysisTab
                awayTeamName={awayClub ? (awayClub.hometown_ko ? `${awayClub.hometown_ko} ${awayClub.name_ko}` : awayClub.name_ko) : '원정팀'}
                homeTeamName={homeClub ? (homeClub.hometown_ko ? `${homeClub.hometown_ko} ${homeClub.name_ko}` : homeClub.name_ko) : '홈팀'}
                awayTeamCode={awayClub?.team_code}
                homeTeamCode={homeClub?.team_code}
                awayTeamRecord={analysisApiData?.away_team_record}
                homeTeamRecord={analysisApiData?.home_team_record}
                headToHeadDetail={analysisApiData?.head_to_head_detail}
                metrics={analysisApiData?.metrics}
                pitcherComparison={analysisApiData?.pitcher_comparison}
              />
            )}

            {activeTab === 'lineup' && (
              <LineupTab
                awayTeamName={awayClub?.name_ko || '원정팀'}
                homeTeamName={homeClub?.name_ko || '홈팀'}
                awayTeamCode={awayClub?.team_code}
                homeTeamCode={homeClub?.team_code}
                awayLineup={lineups.away}
                homeLineup={lineups.home}
              />
            )}

            {activeTab === 'boxscore' && (
              <BoxscoreTab pitchRecords={pitchRecords} />
            )}

            {activeTab === 'broadcast' && (
              <BroadcastTab
                matchLog={matchDetailData?.match_log_json || matchDetailData?.match_log}
                awayClub={awayClub}
                homeClub={homeClub}
                playersMap={playersMap}
                lineupData={lineupData}
              />
            )}

            {activeTab === 'news' && (
              <NewsTab newsList={newsList} />
            )}
          </main>
        </section>
      </div>
    </div>
  );
}
