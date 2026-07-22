import { useState } from 'react';
import { AWAY_TEAM_COLOR, LEAGUE_COLORS } from '../constants/leagues';
import './MatchDetail.css';

export default function MatchDetail() {
  const [activeTab, setActiveTab] = useState<'analysis' | 'lineup' | 'boxscore' | 'cheer' | 'news'>('analysis');

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
      color: AWAY_TEAM_COLOR.primary,
      symbol: 'C',
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
      color: LEAGUE_COLORS.AL.primary,
      symbol: 'Z',
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
    winPitcher: '김서진 (6이닝 2실점 5K, 7승 2패)',
    losePitcher: '박현우 (5.1이닝 4실점 3K, 5승 4패)',
    savePitcher: '정우진 (1이닝 무실점 1K, 18세이브)',
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

  return (
    <div className="match-detail">
      <div className="match-detail__container">
        {/* 상단 경기 정보 서머리 & 이닝별 스코어보드 */}
        <header className="match-detail__header">
          <div className="match-detail__meta">
            <span className="match-detail__league-badge">{matchInfo.league}</span>
            <span className="match-detail__status-badge">{matchInfo.status}</span>
            <span className="match-detail__info-text">{matchInfo.date} | {matchInfo.stadium}</span>
          </div>

          <div className="match-detail__hero">
            <div className="match-detail__team match-detail__team--away">
              <div className="match-detail__logo-placeholder" style={{ color: matchInfo.awayTeam.color }}>
                {matchInfo.awayTeam.symbol}
              </div>
              <div className="match-detail__team-info match-detail__team-info--away">
                <span className="match-detail__team-name">{matchInfo.awayTeam.fullName}</span>
                <span className="match-detail__team-code">{matchInfo.awayTeam.abbrName}</span>
              </div>
            </div>

            <div className="match-detail__center-score">
              <span className="match-detail__score">{matchInfo.awayTeam.score}</span>
              <span className="match-detail__versus-divider">:</span>
              <span className="match-detail__score">{matchInfo.homeTeam.score}</span>
            </div>

            <div className="match-detail__team match-detail__team--home">
              <div className="match-detail__team-info match-detail__team-info--home">
                <span className="match-detail__team-name">{matchInfo.homeTeam.fullName}</span>
                <span className="match-detail__team-code">{matchInfo.homeTeam.abbrName}</span>
              </div>
              <div className="match-detail__logo-placeholder" style={{ color: matchInfo.homeTeam.color }}>
                {matchInfo.homeTeam.symbol}
              </div>
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

        {/* 싱글 컬럼 탭 컨텐츠 */}
        <main className="match-detail__content">
          {/* 1. 전력 분석 탭 */}
          {activeTab === 'analysis' && (
            <div className="match-detail__panel">
              <h3 className="match-detail__panel-title">팀 상대 전적 및 지표 비교</h3>
              <div className="match-detail__analysis-summary">
                <span className="match-detail__analysis-h2h">상대 전적: {analysisData.headToHead}</span>
              </div>
              <div className="match-detail__metrics-list">
                {analysisData.metrics.map((item, idx) => (
                  <div key={idx} className="match-detail__metric-item">
                    <div className="match-detail__metric-label-bar">
                      <span className={`match-detail__metric-val ${item.awayWin ? 'match-detail__metric-val--win' : ''}`}>{item.away}</span>
                      <span className="match-detail__metric-title">{item.label}</span>
                      <span className={`match-detail__metric-val ${!item.awayWin ? 'match-detail__metric-val--win' : ''}`}>{item.home}</span>
                    </div>
                    <div className="match-detail__metric-track">
                      <div
                        className="match-detail__metric-fill match-detail__metric-fill--away"
                        style={{ width: item.awayWin ? '55%' : '45%', backgroundColor: matchInfo.awayTeam.color }}
                      ></div>
                      <div
                        className="match-detail__metric-fill match-detail__metric-fill--home"
                        style={{ width: !item.awayWin ? '55%' : '45%', backgroundColor: matchInfo.homeTeam.color }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 2. 선발 라인업 탭 */}
          {activeTab === 'lineup' && (
            <div className="match-detail__panel">
              <h3 className="match-detail__panel-title">양 팀 선발 타순 및 출전 선수</h3>
              <div className="match-detail__lineup-columns">
                <div className="match-detail__lineup-side">
                  <h4 className="match-detail__lineup-sub-title" style={{ color: matchInfo.awayTeam.color }}>
                    {matchInfo.awayTeam.fullName} (어웨이)
                  </h4>
                  <ul className="match-detail__lineup-list">
                    {lineups.away.map((p, i) => (
                      <li key={i} className="match-detail__lineup-item">
                        <span className="match-detail__lineup-pos">{p.pos}</span>
                        <span className="match-detail__lineup-name">{p.name}</span>
                        <span className="match-detail__lineup-stat">{p.stat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="match-detail__lineup-side">
                  <h4 className="match-detail__lineup-sub-title" style={{ color: matchInfo.homeTeam.color }}>
                    {matchInfo.homeTeam.fullName} (홈)
                  </h4>
                  <ul className="match-detail__lineup-list">
                    {lineups.home.map((p, i) => (
                      <li key={i} className="match-detail__lineup-item">
                        <span className="match-detail__lineup-pos">{p.pos}</span>
                        <span className="match-detail__lineup-name">{p.name}</span>
                        <span className="match-detail__lineup-stat">{p.stat}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* 3. 주요 기록 탭 */}
          {activeTab === 'boxscore' && (
            <div className="match-detail__panel">
              <h3 className="match-detail__panel-title">투타 주요 경기 기록</h3>
              <div className="match-detail__records-grid">
                <div className="match-detail__record-box">
                  <span className="match-detail__record-label">승리투수</span>
                  <span className="match-detail__record-val">{pitchRecords.winPitcher}</span>
                </div>
                <div className="match-detail__record-box">
                  <span className="match-detail__record-label">패전투수</span>
                  <span className="match-detail__record-val">{pitchRecords.losePitcher}</span>
                </div>
                <div className="match-detail__record-box">
                  <span className="match-detail__record-label">세이브</span>
                  <span className="match-detail__record-val">{pitchRecords.savePitcher}</span>
                </div>
                <div className="match-detail__record-box">
                  <span className="match-detail__record-label">주요 홈런</span>
                  <span className="match-detail__record-val">{pitchRecords.keyHomeRun}</span>
                </div>
              </div>
            </div>
          )}

          {/* 4. 승부예측 & 응원 탭 */}
          {activeTab === 'cheer' && (
            <div className="match-detail__panel">
              <h3 className="match-detail__panel-title">팬 승부 예측 및 실시간 응원</h3>
              <div className="match-detail__prediction-box">
                <div className="match-detail__prediction-header">
                  <span>승리 예측 비율</span>
                  <span className="match-detail__prediction-ratio">42% vs 58%</span>
                </div>
                <div className="match-detail__prediction-bar">
                  <div className="match-detail__prediction-fill match-detail__prediction-fill--away" style={{ width: '42%', backgroundColor: matchInfo.awayTeam.color }}>
                    COM 42%
                  </div>
                  <div className="match-detail__prediction-fill match-detail__prediction-fill--home" style={{ width: '58%', backgroundColor: matchInfo.homeTeam.color }}>
                    ZEN 58%
                  </div>
                </div>
              </div>

              <div className="match-detail__cheer-list">
                {cheers.map((c, i) => (
                  <div key={i} className="match-detail__cheer-item">
                    <div className="match-detail__cheer-header">
                      <span className="match-detail__cheer-user">{c.user}</span>
                      <span className={`match-detail__cheer-tag match-detail__cheer-tag--${c.team.toLowerCase()}`}>{c.team}</span>
                    </div>
                    <p className="match-detail__cheer-text">{c.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 5. 관련 뉴스 탭 */}
          {activeTab === 'news' && (
            <div className="match-detail__panel">
              <h3 className="match-detail__panel-title">매치 관련 뉴스 및 하이라이트</h3>
              <div className="match-detail__news-list">
                {newsList.map((n, i) => (
                  <div key={i} className="match-detail__news-item">
                    <span className="match-detail__news-category">{n.category}</span>
                    <h5 className="match-detail__news-headline">{n.title}</h5>
                    <span className="match-detail__news-time">{n.time}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
