import { useEffect, useState } from 'react';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { getClubs, type Club } from '../../api/clubs';
import { getMatches, getMatchScoreboard, type Match, type IngameScoreboard } from '../../api/matches';
import { getSystemInfo } from '../../api/system';
import TeamLogo from '../../components/TeamLogo/TeamLogo';
import './index.css';

import AnalysisTab from './AnalysisTab';
import LineupTab from './LineupTab';
import BoxscoreTab from './BoxscoreTab';
import CheerTab from './CheerTab';
import NewsTab from './NewsTab';

const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];

const LEAGUE_INFO: Record<number, { name: string; code: string }> = {
  1: { name: '아젤리아', code: 'AL' },
  2: { name: '카멜리아', code: 'CL' },
  3: { name: '젠티아나', code: 'GL' },
  4: { name: '매그놀리아', code: 'ML' },
};

const getMatchTitle = (match: Match | null, homeClub: Club | null, seasonYear: number): string => {
  if (!match) return `${seasonYear} KLB 정규리그`;

  const simDay = match.sim_day;
  const isPostSeason = simDay >= 229;

  // 1. 포스트시즌 경기 (sim_day >= 229)
  if (isPostSeason) {
    const isKnockout = match.limit_extra_innings === false;
    if (isKnockout) {
      if (simDay >= 261) {
        return `${seasonYear} 포스트시즌 결승전`;
      } else if (simDay >= 245) {
        return `${seasonYear} 포스트시즌 준결승전`;
      } else {
        return `${seasonYear} 포스트시즌 8강전`;
      }
    } else {
      return `${seasonYear} 포스트시즌 정예리그`;
    }
  }

  // 2. 정규시즌 경기 (sim_day <= 228)
  const leagueId = homeClub?.league_id || 1;
  const league = LEAGUE_INFO[leagueId] || { name: '아젤리아', code: 'AL' };
  return `${league.name} 정규리그 | ${league.code}`;
};

const getSimDayFromDate = (year: number, date: Date): number => {
  const baseDate = new Date(year, 0, 1);
  const targetDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffTime = targetDate.getTime() - baseDate.getTime();
  return Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1;
};

const formatNavDate = (date: Date) => {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const dayName = DAY_NAMES[date.getDay()];
  return `${month}.${day} ${dayName}`;
};

const formatFullDateStr = (date: Date) => {
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
  const [activeTab, setActiveTab] = useState<'analysis' | 'lineup' | 'boxscore' | 'cheer' | 'news'>('analysis');
  const [navDate, setNavDate] = useState<Date>(new Date(2026, 6, 17));
  const [seasonYear, setSeasonYear] = useState<number>(2026);

  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [allMatches, setAllMatches] = useState<Match[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [scoreboard, setScoreboard] = useState<IngameScoreboard | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([getClubs(), getMatches(), getSystemInfo()])
      .then(([clubsList, matchesList, sysInfo]) => {
        const cMap: Record<number, Club> = {};
        clubsList.forEach((c) => {
          cMap[c.id] = c;
        });
        setClubsMap(cMap);
        setAllMatches(matchesList);

        const sysYear = sysInfo?.season_year || 2026;
        setSeasonYear(sysYear);

        // URL 해시 파싱으로 전달받은 Match ID 확인
        const targetMatchId = getMatchIdFromHash();
        let matchedMatch: Match | undefined;

        if (targetMatchId) {
          matchedMatch = matchesList.find((m) => m.id === targetMatchId);
        }

        if (matchedMatch) {
          setSelectedMatchId(matchedMatch.id);
          const matchDate = new Date(sysYear, 0, matchedMatch.sim_day);
          setNavDate(matchDate);
        } else if (sysInfo) {
          const currentSimDay = sysInfo.current_sim_day || 1;
          const currentDate = new Date(sysYear, 0, currentSimDay);
          setNavDate(currentDate);

          const todayMatches = matchesList.filter((m) => m.sim_day === currentSimDay);
          if (todayMatches.length > 0) {
            setSelectedMatchId(todayMatches[0].id);
          } else if (matchesList.length > 0) {
            setSelectedMatchId(matchesList[0].id);
          }
        }
        setIsLoading(false);
      })
      .catch((e) => {
        console.error('Failed to load match detail API data', e);
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    if (selectedMatchId) {
      getMatchScoreboard(selectedMatchId)
        .then((sb) => setScoreboard(sb))
        .catch((e) => {
          console.error('Failed to load scoreboard', e);
          setScoreboard(null);
        });
    }
  }, [selectedMatchId]);

  const handlePrevDay = () => {
    setNavDate((prev) => new Date(prev.getFullYear(), prev.getMonth(), prev.getDate() - 1));
  };

  const handleNextDay = () => {
    setNavDate((prev) => new Date(prev.getFullYear(), prev.getMonth(), prev.getDate() + 1));
  };

  // 현재 선택된 경기 구하기
  const currentMatch = allMatches.find((m) => m.id === selectedMatchId) || allMatches[0];

  // 현재 탐색 날짜(navDate)의 sim_day에 해당하는 경기 목록
  const currentSimDay = getSimDayFromDate(seasonYear, navDate);
  const currentDayMatches = allMatches.filter((m) => m.sim_day === currentSimDay);

  // 팀 정보 매핑
  const awayClub = currentMatch ? clubsMap[currentMatch.away_club_id] : null;
  const homeClub = currentMatch ? clubsMap[currentMatch.home_club_id] : null;

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
  const matchTitle = getMatchTitle(currentMatch, homeClub, seasonYear);

  // 경기 일자 및 구장
  const matchDateObj = currentMatch ? new Date(seasonYear, 0, currentMatch.sim_day) : navDate;
  const matchDateText = formatFullDateStr(matchDateObj);
  const matchStadiumText = currentMatch?.stadium?.name || (homeClub ? homeClub.stadium_name_ko || `${homeClub.hometown_ko} 야구장` : '서울 잠실야구장');

  // 경기 점수 & 이닝 데이터
  const awayScore = currentMatch?.away_score ?? 0;
  const homeScore = currentMatch?.home_score ?? 0;

  // 탭 목데이터
  const analysisData = {
    headToHead: `${awayClub?.name_ko || '원정팀'} VS ${homeClub?.name_ko || '홈팀'} 시즌 첫 맞대결`,
    metrics: [
      { label: '팀 타율', away: '.278', home: '.262', awayWin: true },
      { label: '팀 평균자책점', away: '3.42', home: '3.98', awayWin: true },
      { label: '팀 홈런', away: '84개', home: '92개', awayWin: false },
      { label: '득점권 타율', away: '.295', home: '.251', awayWin: true },
    ],
  };

  const pitchRecords = {
    winPitcher: '김서진',
    losePitcher: '박현우',
    savePitcher: '정우진',
    keyHomeRun: '이동현 (4회 초 2점 홈런, 시즌 14호)',
  };

  const lineups = {
    away: [
      { pos: '1B / 1번', name: '이동현', avg: '.312', stat: '4타수 2안타 1홈런 2타점' },
      { pos: 'CF / 2번', name: '김민준', avg: '.295', stat: '4타수 1안타 1볼넷' },
      { pos: 'LF / 3번', name: '강태양', avg: '.335', stat: '3타수 2안타 1타점' },
      { pos: 'DH / 4번', name: '최현석', avg: '.288', stat: '4타수 1안타' },
      { pos: '3B / 5번', name: '윤성민', avg: '.274', stat: '3타수 1안타 1볼넷' },
      { pos: 'SS / 6번', name: '한지훈', avg: '.260', stat: '4타수 1안타 1득점' },
      { pos: 'RF / 7번', name: '임도현', avg: '.245', stat: '3타수 0안타 1볼넷' },
      { pos: 'C / 8번', name: '송재호', avg: '.232', stat: '3타수 1안타' },
      { pos: '2B / 9번', name: '오세훈', avg: '.251', stat: '3타수 0안타' },
    ],
    home: [
      { pos: 'SS / 1번', name: '박지환', avg: '.305', stat: '4타수 2안타 1득점' },
      { pos: '2B / 2번', name: '서동주', avg: '.281', stat: '4타수 1안타' },
      { pos: 'RF / 3번', name: '조유진', avg: '.320', stat: '3타수 1안타 1홈런' },
      { pos: '1B / 4번', name: '장민호', avg: '.294', stat: '4타수 1안타 1타점' },
      { pos: 'DH / 5번', name: '권우진', avg: '.268', stat: '3타수 0안타 1볼넷' },
      { pos: '3B / 6번', name: '배성우', avg: '.255', stat: '4타수 1안타' },
      { pos: 'LF / 7번', name: '신동현', avg: '.240', stat: '3타수 0안타' },
      { pos: 'C / 8번', name: '황보건', avg: '.218', stat: '3타수 0안타' },
      { pos: 'CF / 9번', name: '유승범', avg: '.238', stat: '3타수 0안타' },
    ],
  };

  const cheers = [
    { user: '야구팬1', team: awayClub?.team_code || 'AWAY', text: `${awayClub?.name_ko || '어웨이'}팀 오늘 경기 힘내서 승리 가져옵시다!` },
    { user: '홈팀수호신', team: homeClub?.team_code || 'HOME', text: `${homeClub?.name_ko || '홈'}팀 홈경기 꼭 승리로 닫아주세요!` },
  ];

  const newsList = [
    { title: `[Match Review] ${awayClub?.name_ko || '어웨이'} vs ${homeClub?.name_ko || '홈'} 치열한 명승부 전개`, time: '1시간 전', category: '리뷰' },
    { title: '[Interview] 감독 청사진 "선수단의 집중력이 빛난 경기였다"', time: '2시간 전', category: '인터뷰' },
    { title: '[Highlight] 경기 분위기를 바꾼 결정적인 호수비 명장면', time: '3시간 전', category: '하이라이트' },
  ];

  if (isLoading) {
    return (
      <div className="match-detail">
        <div className="match-detail__container" style={{ textAlign: 'center', padding: '60px 0', color: '#6b7280' }}>
          경기 데이터를 로딩 중입니다...
        </div>
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
      <div className="match-detail__container">
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
                  <TeamLogo teamCode={awayClub?.team_code} teamName={awayClub?.name_ko || '원정팀'} size={44} />
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
                  <TeamLogo teamCode={homeClub?.team_code} teamName={homeClub?.name_ko || '홈팀'} size={44} />
                </div>
              </div>

              {/* 가로형 이닝별 스코어보드 (동적 연장전 이닝 지원) */}
              <div className="match-detail__table-wrapper">
                <table className="match-detail__scoreboard-table">
                  <thead>
                    <tr>
                      <th className="match-detail__th-team">구단</th>
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

              <div className="match-detail__nav-content">
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
              className={`match-detail__tab-btn ${activeTab === 'cheer' ? 'match-detail__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('cheer')}
            >
              승부예측 & 응원
            </button>
            <button
              className={`match-detail__tab-btn ${activeTab === 'news' ? 'match-detail__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('news')}
            >
              관련 뉴스
            </button>
          </nav>

          {/* 싱글 컬럼 탭 컨텐츠 */}
          <main className="match-detail__content">
            {activeTab === 'analysis' && (
              <AnalysisTab
                headToHead={analysisData.headToHead}
                metrics={analysisData.metrics}
              />
            )}

            {activeTab === 'lineup' && (
              <LineupTab
                awayTeamName={awayClub?.name_ko || '원정팀'}
                homeTeamName={homeClub?.name_ko || '홈팀'}
                awayLineup={lineups.away}
                homeLineup={lineups.home}
              />
            )}

            {activeTab === 'boxscore' && (
              <BoxscoreTab pitchRecords={pitchRecords} />
            )}

            {activeTab === 'cheer' && (
              <CheerTab
                cheers={cheers}
                awayTeamCode={awayClub?.team_code}
                homeTeamCode={homeClub?.team_code}
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
