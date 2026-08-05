import { useState } from 'react';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import TeamLogo from '../../components/TeamLogo/TeamLogo';
import './index.css';

import AnalysisTab from './AnalysisTab';
import LineupTab from './LineupTab';
import BoxscoreTab from './BoxscoreTab';
import CheerTab from './CheerTab';
import NewsTab from './NewsTab';

const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];

const formatNavDate = (date: Date) => {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const dayName = DAY_NAMES[date.getDay()];
  return `${month}.${day} ${dayName}`;
};

const getDateKey = (date: Date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

interface OtherMatchItem {
  id: number;
  awayTeam: { code: string; name: string; score?: number };
  homeTeam: { code: string; name: string; score?: number };
  status: string;
  isCurrent?: boolean;
}

export default function MatchDetail() {
  const [activeTab, setActiveTab] = useState<'analysis' | 'lineup' | 'boxscore' | 'cheer' | 'news'>('analysis');
  const [navDate, setNavDate] = useState<Date>(new Date(2026, 6, 17));

  const handlePrevDay = () => {
    setNavDate((prev) => new Date(prev.getFullYear(), prev.getMonth(), prev.getDate() - 1));
  };

  const handleNextDay = () => {
    setNavDate((prev) => new Date(prev.getFullYear(), prev.getMonth(), prev.getDate() + 1));
  };

  // 날짜별 경기 목데이터
  const otherMatchesData: Record<string, OtherMatchItem[]> = {
    '2026-07-17': [
      { id: 101, awayTeam: { code: 'COM', name: '코멧스', score: 15 }, homeTeam: { code: 'ZEN', name: '제니스', score: 3 }, status: '종료', isCurrent: true },
      { id: 102, awayTeam: { code: 'DRG', name: '드래곤스', score: 2 }, homeTeam: { code: 'BER', name: '베어스', score: 4 }, status: '종료' },
      { id: 103, awayTeam: { code: 'EAG', name: '이글스', score: 6 }, homeTeam: { code: 'GIA', name: '자이언츠', score: 5 }, status: '종료' },
      { id: 104, awayTeam: { code: 'LUN', name: '루나스', score: 1 }, homeTeam: { code: 'UNI', name: '유니콘스', score: 8 }, status: '종료' },
    ],
    '2026-07-18': [
      { id: 105, awayTeam: { code: 'COM', name: '코멧스' }, homeTeam: { code: 'ZEN', name: '제니스' }, status: '18:30' },
      { id: 106, awayTeam: { code: 'DRG', name: '드래곤스' }, homeTeam: { code: 'BER', name: '베어스' }, status: '18:30' },
      { id: 107, awayTeam: { code: 'EAG', name: '이글스' }, homeTeam: { code: 'GIA', name: '자이언츠' }, status: '18:30' },
    ],
  };

  const currentDayMatches = otherMatchesData[getDateKey(navDate)];

  // 가상 하드코딩 목데이터
  const matchInfo = {
    league: '아젤리아 리그 (AL)',
    date: '2026년 7월 17일 (금) 18:30',
    stadium: '서울 잠실야구장',
    status: '경기 종료',
    awayTeam: {
      code: 'COM',
      name: '코멧스',
      fullName: '서울 코멧스',
      abbrName: 'S. Comets',
      color: '#888888',
      score: 15,
      r: 5,
      h: 9,
      e: 0,
      b: 4,
      innings: [0, 1, 0, 2, 0, 0, 1, 1, 0],
    },
    homeTeam: {
      code: 'ZEN',
      name: '제니스',
      fullName: '부산 제니스',
      abbrName: 'B. Zenith',
      color: '#cccccc',
      score: 3,
      r: 3,
      h: 6,
      e: 1,
      b: 3,
      innings: [1, 0, 0, 0, 0, 1, 0, 1, 0],
    },
  };

  const analysisData = {
    headToHead: '코멧스 4승 2패 우세',
    recent5Matches: {
      away: ['W', 'W', 'L', 'W', 'W'],
      home: ['L', 'W', 'W', 'L', 'L'],
    },
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
    { user: '코멧스수호신', team: 'COM', text: '오늘 이동현 선수 4회 초 투런홈런 진짜 소름 돋았습니다! 승리 가자!' },
    { user: '부산제니스팬', team: 'ZEN', text: '아쉽게 졌지만 6회 추격 타점 멋졌습니다. 다음 경기 꼭 잡읍시다!' },
    { user: 'KLB마니아', team: 'COM', text: '정우진 마무리가 9회 깔끔하게 닫아줘서 안심하고 봤네요. 7승 달성 축하!' },
  ];

  const newsList = [
    { title: '[Match Review] 코멧스, 이동현의 결승 2점포로 제니스 꺾고 2연승 달려', time: '1시간 전', category: '리뷰' },
    { title: '[Interview] 7승째 달성 김서진 "야수들의 득점 지원과 호수비 덕분"', time: '2시간 전', category: '인터뷰' },
    { title: '[Highlight] 4회 초 경기 흐름을 바꾼 이동현의 비거리 125m 대형 홈런', time: '3시간 전', category: '하이라이트' },
  ];

  const getStatusBadgeInfo = (status: string) => {
    if (status === '경기 진행중' || status === 'IN_PROGRESS' || status === 'LIVE') {
      return { label: 'LIVE', modifier: 'live' };
    }
    if (status === '경기 종료' || status === 'COMPLETED') {
      return { label: '경기 종료', modifier: 'ended' };
    }
    return { label: status, modifier: 'upcoming' };
  };

  const statusInfo = getStatusBadgeInfo(matchInfo.status);

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
                <span className="match-detail__top-league">{matchInfo.league}</span>
                <span className="match-detail__top-info">{matchInfo.date} | {matchInfo.stadium}</span>
              </div>

              <div className="match-detail__hero">
                <div className="match-detail__team match-detail__team--away">
                  <TeamLogo teamCode={matchInfo.awayTeam.code} teamName={matchInfo.awayTeam.fullName} size={44} />
                  <div className="match-detail__team-info match-detail__team-info--away">
                    <span className="match-detail__team-name">{matchInfo.awayTeam.fullName}</span>
                    <span className="match-detail__team-code">{matchInfo.awayTeam.abbrName}</span>
                  </div>
                </div>

                <div className="match-detail__center-score">
                  <span className="match-detail__score">{matchInfo.awayTeam.score}</span>
                  <span className={`match-detail__status-badge match-detail__status-badge--${statusInfo.modifier}`}>
                    {statusInfo.label}
                  </span>
                  <span className="match-detail__score">{matchInfo.homeTeam.score}</span>
                </div>

                <div className="match-detail__team match-detail__team--home">
                  <div className="match-detail__team-info match-detail__team-info--home">
                    <span className="match-detail__team-name">
                      {matchInfo.homeTeam.fullName}
                      <span className="match-detail__home-label">홈</span>
                    </span>
                    <span className="match-detail__team-code">{matchInfo.homeTeam.abbrName}</span>
                  </div>
                  <TeamLogo teamCode={matchInfo.homeTeam.code} teamName={matchInfo.homeTeam.fullName} size={44} />
                </div>
              </div>

              {/* 가로형 이닝별 스코어보드 */}
              <div className="match-detail__table-wrapper">
                <table className="match-detail__scoreboard-table">
                  <thead>
                    <tr>
                      <th className="match-detail__th-team">구단</th>
                      <th>1</th>
                      <th>2</th>
                      <th>3</th>
                      <th>4</th>
                      <th>5</th>
                      <th>6</th>
                      <th>7</th>
                      <th>8</th>
                      <th>9</th>
                      <th className="match-detail__th-stat">R</th>
                      <th className="match-detail__th-stat">H</th>
                      <th className="match-detail__th-stat">E</th>
                      <th className="match-detail__th-stat">B</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="match-detail__td-team">
                        <span className="match-detail__team-indicator" style={{ backgroundColor: matchInfo.awayTeam.color }}></span>
                        {matchInfo.awayTeam.name}
                      </td>
                      {matchInfo.awayTeam.innings.map((val, idx) => (
                        <td key={idx}>{val}</td>
                      ))}
                      <td className="match-detail__td-stat match-detail__td-stat--highlight">{matchInfo.awayTeam.r}</td>
                      <td className="match-detail__td-stat">{matchInfo.awayTeam.h}</td>
                      <td className="match-detail__td-stat">{matchInfo.awayTeam.e}</td>
                      <td className="match-detail__td-stat">{matchInfo.awayTeam.b}</td>
                    </tr>
                    <tr>
                      <td className="match-detail__td-team">
                        <span className="match-detail__team-indicator" style={{ backgroundColor: matchInfo.homeTeam.color }}></span>
                        {matchInfo.homeTeam.name}
                      </td>
                      {matchInfo.homeTeam.innings.map((val, idx) => (
                        <td key={idx}>{val}</td>
                      ))}
                      <td className="match-detail__td-stat match-detail__td-stat--highlight">{matchInfo.homeTeam.r}</td>
                      <td className="match-detail__td-stat">{matchInfo.homeTeam.h}</td>
                      <td className="match-detail__td-stat">{matchInfo.homeTeam.e}</td>
                      <td className="match-detail__td-stat">{matchInfo.homeTeam.b}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* 우측: 다른 경기 탐색 패널 */}
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
                    {currentDayMatches.map((m) => (
                      <div
                        key={m.id}
                        className={`match-detail__other-match-card ${m.isCurrent ? 'match-detail__other-match-card--current' : ''}`}
                      >
                        <div className="match-detail__other-match-team">
                          <TeamLogo teamCode={m.awayTeam.code} teamName={m.awayTeam.name} size={16} />
                          <span className="match-detail__other-match-team-name">{m.awayTeam.name}</span>
                          {m.awayTeam.score !== undefined && (
                            <span className="match-detail__other-match-score">{m.awayTeam.score}</span>
                          )}
                        </div>
                        <div className="match-detail__other-match-vs">
                          <span className="match-detail__other-match-status">{m.status}</span>
                        </div>
                        <div className="match-detail__other-match-team match-detail__other-match-team--home">
                          {m.homeTeam.score !== undefined && (
                            <span className="match-detail__other-match-score">{m.homeTeam.score}</span>
                          )}
                          <span className="match-detail__other-match-team-name">{m.homeTeam.name}</span>
                          <TeamLogo teamCode={m.homeTeam.code} teamName={m.homeTeam.name} size={16} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="match-detail__no-matches">경기가 없습니다</div>
                )}
              </div>
            </div>
          </div>
        </header>

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

        {/* 싱글 컬럼 탭 컨텐츠 (분할된 컴포넌트 호출) */}
        <main className="match-detail__content">
          {activeTab === 'analysis' && (
            <AnalysisTab
              headToHead={analysisData.headToHead}
              metrics={analysisData.metrics}
              awayColor={matchInfo.awayTeam.color}
              homeColor={matchInfo.homeTeam.color}
            />
          )}

          {activeTab === 'lineup' && (
            <LineupTab
              awayTeamName={matchInfo.awayTeam.fullName}
              homeTeamName={matchInfo.homeTeam.fullName}
              awayLineup={lineups.away}
              homeLineup={lineups.home}
              awayColor={matchInfo.awayTeam.color}
              homeColor={matchInfo.homeTeam.color}
            />
          )}

          {activeTab === 'boxscore' && (
            <BoxscoreTab pitchRecords={pitchRecords} />
          )}

          {activeTab === 'cheer' && (
            <CheerTab
              cheers={cheers}
              awayTeamCode={matchInfo.awayTeam.code}
              homeTeamCode={matchInfo.homeTeam.code}
              awayColor={matchInfo.awayTeam.color}
              homeColor={matchInfo.homeTeam.color}
            />
          )}

          {activeTab === 'news' && (
            <NewsTab newsList={newsList} />
          )}
        </main>
      </div>
    </div>
  );
}
