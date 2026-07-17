import { useState, useEffect } from 'react'
import './App.css'
import Intro from './pages/Intro'
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import newsThumbnail from './assets/news_baseball_thumbnail.png'

interface NewsItem {
  id: number;
  title: string;
  excerpt: string;
  date: string;
  press: string;
  thumbnailUrl?: string;
}

interface StandingItem {
  rank: number;
  teamName: string;
  logoSymbol: string;
  logoColor: string;
  games: number;
  wins: number;
  draws: number;
  losses: number;
  pct: string;
  gb: string;
  streak: string;
}

const mockStandings: Record<'AL' | 'CL', StandingItem[]> = {
  AL: [
    { rank: 1, teamName: "제니스", logoSymbol: "Z", logoColor: "#e01e3c", games: 45, wins: 28, draws: 0, losses: 17, pct: ".622", gb: "-", streak: "3승" },
    { rank: 2, teamName: "코메츠", logoSymbol: "C", logoColor: "#1f77b4", games: 45, wins: 26, draws: 1, losses: 18, pct: ".578", gb: "2.0", streak: "1패" },
    { rank: 3, teamName: "웨일스", logoSymbol: "W", logoColor: "#2ca02c", games: 45, wins: 23, draws: 0, losses: 22, pct: ".511", gb: "5.0", streak: "2승" },
    { rank: 4, teamName: "센티넬즈", logoSymbol: "S", logoColor: "#9467bd", games: 45, wins: 20, draws: 2, losses: 23, pct: ".444", gb: "8.0", streak: "1패" },
    { rank: 5, teamName: "새턴즈", logoSymbol: "T", logoColor: "#ff7f0e", games: 45, wins: 15, draws: 0, losses: 30, pct: ".333", gb: "13.0", streak: "4패" },
  ],
  CL: [
    { rank: 1, teamName: "엔더스", logoSymbol: "E", logoColor: "#8c564b", games: 45, wins: 30, draws: 0, losses: 15, pct: ".667", gb: "-", streak: "5승" },
    { rank: 2, teamName: "밸리언츠", logoSymbol: "V", logoColor: "#e377c2", games: 45, wins: 25, draws: 1, losses: 19, pct: ".556", gb: "5.0", streak: "2패" },
    { rank: 3, teamName: "팬텀즈", logoSymbol: "P", logoColor: "#7f7f7f", games: 45, wins: 22, draws: 0, losses: 23, pct: ".489", gb: "8.0", streak: "1승" },
    { rank: 4, teamName: "가디언즈", logoSymbol: "G", logoColor: "#bcbd22", games: 45, wins: 19, draws: 2, losses: 24, pct: ".422", gb: "11.0", streak: "3패" },
    { rank: 5, teamName: "펌킨스", logoSymbol: "K", logoColor: "#17becf", games: 45, wins: 17, draws: 1, losses: 27, pct: ".378", gb: "13.0", streak: "1승" },
  ]
};

const mockNews: NewsItem[] = [
  {
    id: 1,
    title: "Krown League Baseball 2026 시즌 공식 일정 확정",
    excerpt: "대한민국 야구 독립 리그의 새 바람, KLB의 2026 정규 시즌 공식 일정이 발표되었습니다. 개막전은 오는 4월 7일 제니스 구장을 비롯한 전국 5개 구장에서 동시에 열리며, 팀당 144경기의 대장정이 시작됩니다...",
    date: "2026.07.17",
    press: "스포츠크라운",
    thumbnailUrl: newsThumbnail
  },
  {
    id: 2,
    title: "새턴즈, 도미니카 출신 불펜 투수 영입 발표",
    excerpt: "새턴즈 구단은 마운드 보강을 위해 도미니카 공화국 출신의 강속구 우완 불펜 투수 카를로스 산체스와 계약을 맺었다고 공식 발표했습니다. 계약 금액은 옵션을 포함하여...",
    date: "2026.07.15",
    press: "KLB Daily"
  },
  {
    id: 3,
    title: "Krown Star Weekend 올스타전 팬 투표 시작",
    excerpt: "시즌 80경기 시점에 개최되는 초대형 연합 이벤트 'Krown Star Weekend'의 올스타 투표가 오늘 오전 10시부터 공식 앱을 통해 개시되었습니다. 선발 명단은 100% 팬 투표로...",
    date: "2026.07.12",
    press: "네오베이스볼",
    thumbnailUrl: newsThumbnail
  },
  {
    id: 4,
    title: "가디언즈, 유소년 야구단 초청 재능 기부 클리닉",
    excerpt: "가디언즈 선수단은 비시즌을 맞아 연고지 지역 아동 센터 소속의 유소년 야구 선수 50명을 구단 훈련장으로 초청하여 1일 멘토링 프로그램 및 야구 기술 교육을 성황리에 진행했습니다...",
    date: "2026.07.08",
    press: "구단 소식지"
  },
  {
    id: 5,
    title: "KLB 하부 디비전 육성 리그 통합 시스템 개편안 발표",
    excerpt: "리그 사무국은 2군 및 3군 디비전 활성화와 유기적인 콜업/강등 체계를 확립하기 위한 통합 육성 시스템 개편안을 의결했습니다. 이번 개편으로 유망주들의 출전 기회가 더욱...",
    date: "2026.07.05",
    press: "리그 리포트",
    thumbnailUrl: newsThumbnail
  }
];

const getFormattedDate = () => {
  const today = new Date();
  const month = today.getMonth() + 1;
  const date = today.getDate();
  return `${month}.${date}`;
};

interface MatchItem {
  id: number;
  time: string;
  status: string;
  tier: '1군' | '2군' | '3군';
  league: '아젤리아' | '코스모스' | '지오메트리' | '메트로' | '퓨처스' | '루키';
  awayTeam: string;
  awaySymbol: string;
  awayColor: string;
  awayScore?: number;
  homeTeam: string;
  homeSymbol: string;
  homeColor: string;
  homeScore?: number;
  stadium: string;
}

const mockMatches: Record<string, MatchItem[]> = {
  "2026-07-16": [
    /* 1군 */
    { id: 101, time: "18:30", status: "종료", tier: "1군", league: "아젤리아", awayTeam: "제니스", awaySymbol: "Z", awayColor: "#e01e3c", awayScore: 5, homeTeam: "코메츠", homeSymbol: "C", homeColor: "#1f77b4", homeScore: 3, stadium: "제니스 돔" },
    { id: 102, time: "18:30", status: "종료", tier: "1군", league: "아젤리아", awayTeam: "웨일스", awaySymbol: "W", awayColor: "#2ca02c", awayScore: 2, homeTeam: "센티넬즈", homeSymbol: "S", homeColor: "#9467bd", homeScore: 4, stadium: "센티넬즈 파크" },
    { id: 103, time: "18:30", status: "종료", tier: "1군", league: "코스모스", awayTeam: "새턴즈", awaySymbol: "T", awayColor: "#ff7f0e", awayScore: 1, homeTeam: "엔더스", homeSymbol: "E", homeColor: "#8c564b", homeScore: 7, stadium: "엔더스 필드" },
    { id: 104, time: "18:30", status: "종료", tier: "1군", league: "코스모스", awayTeam: "팬텀즈", awaySymbol: "P", awayColor: "#7f7f7f", awayScore: 3, homeTeam: "가디언즈", homeSymbol: "G", homeColor: "#bcbd22", homeScore: 2, stadium: "가디언즈 필드" },
    { id: 105, time: "18:30", status: "종료", tier: "1군", league: "지오메트리", awayTeam: "타이탄즈", awaySymbol: "TI", awayColor: "#e5a93b", awayScore: 4, homeTeam: "스파크스", homeSymbol: "SP", homeColor: "#88cc44", homeScore: 8, stadium: "스파크스 파크" },
    { id: 106, time: "18:30", status: "종료", tier: "1군", league: "메트로", awayTeam: "네온즈", awaySymbol: "NE", awayColor: "#ff007f", awayScore: 6, homeTeam: "시티즈", homeSymbol: "CT", homeColor: "#00ffff", homeScore: 5, stadium: "메트로 돔" },
    /* 2군 */
    { id: 121, time: "14:00", status: "종료", tier: "2군", league: "퓨처스", awayTeam: "제니스 2군", awaySymbol: "Z2", awayColor: "#e01e3c", awayScore: 2, homeTeam: "코메츠 2군", homeSymbol: "C2", homeColor: "#1f77b4", homeScore: 6, stadium: "제니스 챔피언스 필드" },
    /* 3군 */
    { id: 131, time: "11:00", status: "종료", tier: "3군", league: "루키", awayTeam: "제니스 육성군", awaySymbol: "ZR", awayColor: "#e01e3c", awayScore: 8, homeTeam: "웨일스 육성군", homeSymbol: "WR", homeColor: "#2ca02c", homeScore: 3, stadium: "웨일스 드림 파크" }
  ],
  "2026-07-17": [
    /* 1군 */
    { id: 201, time: "18:30", status: "진행중", tier: "1군", league: "아젤리아", awayTeam: "제니스", awaySymbol: "Z", awayColor: "#e01e3c", awayScore: 1, homeTeam: "코메츠", homeSymbol: "C", homeColor: "#1f77b4", homeScore: 2, stadium: "제니스 돔" },
    { id: 202, time: "18:30", status: "18:30", tier: "1군", league: "아젤리아", awayTeam: "웨일스", awaySymbol: "W", awayColor: "#2ca02c", homeTeam: "센티넬즈", homeSymbol: "S", homeColor: "#9467bd", stadium: "센티넬즈 파크" },
    { id: 203, time: "18:30", status: "종료", tier: "1군", league: "코스모스", awayTeam: "새턴즈", awaySymbol: "T", awayColor: "#ff7f0e", awayScore: 4, homeTeam: "엔더스", homeSymbol: "E", homeColor: "#8c564b", homeScore: 5, stadium: "엔더스 필드" },
    { id: 204, time: "18:30", status: "18:30", tier: "1군", league: "코스모스", awayTeam: "팬텀즈", awaySymbol: "P", awayColor: "#7f7f7f", homeTeam: "가디언즈", homeSymbol: "G", homeColor: "#bcbd22", stadium: "가디언즈 필드" },
    { id: 205, time: "18:30", status: "진행중", tier: "1군", league: "지오메트리", awayTeam: "타이탄즈", awaySymbol: "TI", awayColor: "#e5a93b", awayScore: 0, homeTeam: "스파크스", homeSymbol: "SP", homeColor: "#88cc44", homeScore: 3, stadium: "스파크스 파크" },
    { id: 206, time: "18:30", status: "18:30", tier: "1군", league: "메트로", awayTeam: "네온즈", awaySymbol: "NE", awayColor: "#ff007f", homeTeam: "시티즈", homeSymbol: "CT", homeColor: "#00ffff", stadium: "메트로 돔" },
    /* 2군 */
    { id: 221, time: "14:00", status: "종료", tier: "2군", league: "퓨처스", awayTeam: "제니스 2군", awaySymbol: "Z2", awayColor: "#e01e3c", awayScore: 5, homeTeam: "코메츠 2군", homeSymbol: "C2", homeColor: "#1f77b4", homeScore: 4, stadium: "제니스 챔피언스 필드" },
    { id: 222, time: "14:00", status: "종료", tier: "2군", league: "퓨처스", awayTeam: "새턴즈 2군", awaySymbol: "T2", awayColor: "#ff7f0e", awayScore: 1, homeTeam: "엔더스 2군", homeSymbol: "E2", homeColor: "#8c564b", homeScore: 9, stadium: "엔더스 드림 필드" },
    /* 3군 */
    { id: 231, time: "11:00", status: "종료", tier: "3군", league: "루키", awayTeam: "제니스 육성군", awaySymbol: "ZR", awayColor: "#e01e3c", awayScore: 3, homeTeam: "웨일스 육성군", homeSymbol: "WR", homeColor: "#2ca02c", homeScore: 3, stadium: "웨일스 드림 파크" }
  ],
  "2026-07-18": [
    /* 1군 */
    { id: 301, time: "18:30", status: "18:30", tier: "1군", league: "아젤리아", awayTeam: "제니스", awaySymbol: "Z", awayColor: "#e01e3c", homeTeam: "코메츠", homeSymbol: "C", homeColor: "#1f77b4", stadium: "제니스 돔" },
    { id: 302, time: "18:30", status: "18:30", tier: "1군", league: "아젤리아", awayTeam: "웨일스", awaySymbol: "W", awayColor: "#2ca02c", homeTeam: "센티넬즈", homeSymbol: "S", homeColor: "#9467bd", stadium: "센티넬즈 파크" },
    { id: 303, time: "18:30", status: "18:30", tier: "1군", league: "코스모스", awayTeam: "새턴즈", awaySymbol: "T", awayColor: "#ff7f0e", homeTeam: "엔더스", homeSymbol: "E", homeColor: "#8c564b", stadium: "엔더스 필드" },
    { id: 304, time: "18:30", status: "18:30", tier: "1군", league: "코스모스", awayTeam: "팬텀즈", awaySymbol: "P", awayColor: "#7f7f7f", homeTeam: "가디언즈", homeSymbol: "G", homeColor: "#bcbd22", stadium: "가디언즈 필드" },
    { id: 305, time: "18:30", status: "18:30", tier: "1군", league: "지오메트리", awayTeam: "타이탄즈", awaySymbol: "TI", awayColor: "#e5a93b", homeTeam: "스파크스", homeSymbol: "SP", homeColor: "#88cc44", stadium: "스파크스 파크" },
    { id: 306, time: "18:30", status: "18:30", tier: "1군", league: "메트로", awayTeam: "네온즈", awaySymbol: "NE", awayColor: "#ff007f", homeTeam: "시티즈", homeSymbol: "CT", homeColor: "#00ffff", stadium: "메트로 돔" },
    /* 2군 */
    { id: 321, time: "14:00", status: "14:00", tier: "2군", league: "퓨처스", awayTeam: "제니스 2군", awaySymbol: "Z2", awayColor: "#e01e3c", homeTeam: "코메츠 2군", homeSymbol: "C2", homeColor: "#1f77b4", stadium: "제니스 챔피언스 필드" },
    /* 3군 */
    { id: 331, time: "11:00", status: "11:00", tier: "3군", league: "루키", awayTeam: "제니스 육성군", awaySymbol: "ZR", awayColor: "#e01e3c", homeTeam: "웨일스 육성군", homeSymbol: "WR", homeColor: "#2ca02c", stadium: "웨일스 드림 파크" }
  ]
};

const getFormattedISOString = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getDisplayMatchDate = (date: Date) => {
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekDays = ["일", "월", "화", "수", "목", "금", "토"];
  const weekDay = weekDays[date.getDay()];
  return `${year}.${month}.${day} (${weekDay})`;
};



function App() {
  const [currentHash, setCurrentHash] = useState(window.location.hash || '#home')
  const [activeLeague, setActiveLeague] = useState<'AL' | 'CL'>('AL')
  const [matchDate, setMatchDate] = useState<Date>(new Date("2026-07-17"))

  const [activeTier, setActiveTier] = useState<'1군' | '2군' | '3군'>('1군')
  const [activeLeagueFilter, setActiveLeagueFilter] = useState<string>('전체')

  const changeMatchDate = (days: number) => {
    const nextDate = new Date(matchDate);
    nextDate.setDate(nextDate.getDate() + days);
    setMatchDate(nextDate);
    setActiveLeagueFilter('전체');
  };

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentHash(window.location.hash || '#home')
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  return (
    <>
      <header className="header">
        <a href="#home" className="header__logo">
          <img className="header__logo-img" src="/klb-logo-256.svg" alt="KLB Logo" />
          <span className="header__logo-text">KLB</span>
        </a>
        <nav className="header__nav">
          <ul className="header__nav-list">
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#intro' ? 'header__nav-link--active' : ''}`} href="#intro">소개</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#schedule' ? 'header__nav-link--active' : ''}`} href="#schedule">통합 일정</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#teams' ? 'header__nav-link--active' : ''}`} href="#teams">리그 구성</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#live' ? 'header__nav-link--active' : ''}`} href="#live">LIVE</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#community' ? 'header__nav-link--active' : ''}`} href="#community">커뮤니티</a>
            </li>
          </ul>
        </nav>
      </header>

      {currentHash === '#intro' ? (
        <Intro />
      ) : ['#schedule', '#teams', '#live', '#community'].includes(currentHash) ? (
        <div className="empty-page" />
      ) : (
        <>
          <section className="section section--black section--first">
            <div className="section__container">
              {/* 시즌 진행 현황 5단계 스텝 바 */}
              <div className="progress-status">
                <div className="progress-status__season-title">KLB 2026 시즌</div>
                <div className="progress-status__steps">
                  <div className="progress-status__step progress-status__step--active">
                    <span className="progress-status__step-num">1</span>
                    <span className="progress-status__step-text">정규리그 전반</span>
                  </div>
                  <div className="progress-status__connector"></div>
                  <div className="progress-status__step progress-status__step--inactive">
                    <span className="progress-status__step-num">2</span>
                    <span className="progress-status__step-text">인터리그</span>
                  </div>
                  <div className="progress-status__connector"></div>
                  <div className="progress-status__step progress-status__step--inactive">
                    <span className="progress-status__step-num">3</span>
                    <span className="progress-status__step-text">정규리그 후반</span>
                  </div>
                  <div className="progress-status__connector"></div>
                  <div className="progress-status__step progress-status__step--inactive">
                    <span className="progress-status__step-num">4</span>
                    <span className="progress-status__step-text">포스트 리그</span>
                  </div>
                  <div className="progress-status__connector"></div>
                  <div className="progress-status__step progress-status__step--inactive">
                    <span className="progress-status__step-num">5</span>
                    <span className="progress-status__step-text">포스트 파이널</span>
                  </div>
                </div>
              </div>

              {/* 리그별 순위표 */}
              <div className="standings">
                <div className="standings__header">
                  <h3 className="standings__title">
                    {getFormattedDate()} {activeLeague === 'AL' ? '아젤리아 리그' : '코스모스 리그'}
                  </h3>
                  <div className="standings__tabs">
                    <button
                      className={`standings__tab ${activeLeague === 'AL' ? 'standings__tab--active' : ''}`}
                      onClick={() => setActiveLeague('AL')}
                    >
                      AL 리그
                    </button>
                    <button
                      className={`standings__tab ${activeLeague === 'CL' ? 'standings__tab--active' : ''}`}
                      onClick={() => setActiveLeague('CL')}
                    >
                      CL 리그
                    </button>
                  </div>
                </div>

                <div className="standings__table-wrapper">
                  <table className="standings__table">
                    <thead>
                      <tr>
                        <th>순위</th>
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
                      {mockStandings[activeLeague].map((row, idx) => (
                        <tr key={`${row.teamName}-${idx}`}>
                          <td className="standings__rank">{row.rank}</td>
                          <td className="standings__team-name">
                            <div className="standings__team-cell">
                              <div
                                className="standings__team-logo-placeholder"
                                style={{ color: row.logoColor }}
                              >
                                {row.logoSymbol}
                              </div>
                              <span className="standings__team-text">{row.teamName}</span>
                            </div>
                          </td>
                          <td>{row.games}</td>
                          <td>{row.wins}</td>
                          <td>{row.draws}</td>
                          <td>{row.losses}</td>
                          <td className="standings__pct">{row.pct}</td>
                          <td>{row.gb}</td>
                          <td>{row.streak}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          <section className="section section--light">
            <div className="section__container">
              <div className="section__header">
                <h2 className="section__title">통합 소식</h2>
                <a href="#news" className="section__more-link">뉴스 더보기</a>
              </div>
              <div className="news-list">
                {mockNews.map((news) => (
                  <div key={news.id} className="news-card">
                    {news.thumbnailUrl && (
                      <div className="news-card__thumbnail-wrapper">
                        <img className="news-card__thumbnail" src={news.thumbnailUrl} alt={news.title} />
                      </div>
                    )}
                    <div className="news-card__content">
                      <div className="news-card__meta">
                        <span className="news-card__press">{news.press}</span>
                        <span className="news-card__date">{news.date}</span>
                      </div>
                      <h3 className="news-card__title">
                        <a href={`#news-${news.id}`} className="news-card__link">{news.title}</a>
                      </h3>
                      <p className="news-card__excerpt">{news.excerpt}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="section section--light">
            <div className="section__container">
              <div className="section__header">
                <h2 className="section__title">통합 경기 일정</h2>
              </div>
              
              <div className="match-schedule">
                {/* 데이트 컨트롤러 */}
                <div className="match-schedule__date-controller">
                  <button className="match-schedule__date-btn" onClick={() => changeMatchDate(-1)}>
                    <FiChevronLeft size={16} style={{ display: 'block' }} />
                  </button>
                  <span className="match-schedule__date-text">{getDisplayMatchDate(matchDate)}</span>
                  <button className="match-schedule__date-btn" onClick={() => changeMatchDate(1)}>
                    <FiChevronRight size={16} style={{ display: 'block' }} />
                  </button>
                </div>

                {/* 등급 필터 탭 (1군 / 2군 / 3군) */}
                <div className="match-schedule__tier-tabs">
                  {(['1군', '2군', '3군'] as const).map(tier => (
                    <button
                      key={tier}
                      className={`match-schedule__tier-tab ${activeTier === tier ? 'match-schedule__tier-tab--active' : ''}`}
                      onClick={() => {
                        setActiveTier(tier);
                        setActiveLeagueFilter('전체');
                      }}
                    >
                      {tier} 리그
                    </button>
                  ))}
                </div>

                {/* 1군일 때만 세부 리그 필터 칩스 노출 */}
                {activeTier === '1군' && (
                  <div className="match-schedule__league-chips">
                    {['전체', '아젤리아', '코스모스', '지오메트리', '메트로'].map(league => (
                      <button
                        key={league}
                        className={`match-schedule__league-chip ${activeLeagueFilter === league ? 'match-schedule__league-chip--active' : ''}`}
                        onClick={() => setActiveLeagueFilter(league)}
                      >
                        {league === '전체' ? '전체 보기' : `${league} 리그`}
                      </button>
                    ))}
                  </div>
                )}

                {/* 매치 리스트 (필터링 및 리그별 그룹핑 반영) */}
                <div className="match-schedule__content-area">
                  {(() => {
                    const dateKey = getFormattedISOString(matchDate);
                    const dayMatches = mockMatches[dateKey] || [];
                    
                    const filtered = dayMatches.filter(m => 
                      m.tier === activeTier && 
                      (activeLeagueFilter === '전체' || m.league === activeLeagueFilter)
                    );

                    if (filtered.length === 0) {
                      return (
                        <div className="match-schedule__empty">
                          선택하신 날짜 및 리그에 예정된 경기가 없습니다.
                        </div>
                      );
                    }

                    const grouped: Record<string, MatchItem[]> = {};
                    filtered.forEach(m => {
                      const groupKey = activeTier === '1군' ? `${m.league} 리그` : `${m.tier} 통합 리그`;
                      if (!grouped[groupKey]) {
                        grouped[groupKey] = [];
                      }
                      grouped[groupKey].push(m);
                    });

                    return Object.entries(grouped).map(([groupName, list]) => (
                      <div key={groupName} className="match-schedule__league-group">
                        <h4 className="match-schedule__group-title">{groupName}</h4>
                        <div className="match-schedule__grid">
                          {list.map((match) => (
                            <div key={match.id} className="match-card">
                              <div className="match-card__status-col">
                                <span className={`match-card__status-badge match-card__status-badge--${match.status === '종료' ? 'ended' : match.status.includes('진행') ? 'live' : 'upcoming'}`}>
                                  {match.status}
                                </span>
                                <span className="match-card__time">{match.time}</span>
                              </div>

                              <div className="match-card__versus-col">
                                <div className="match-card__team match-card__team--away">
                                  <span className="match-card__team-name">{match.awayTeam}</span>
                                  <div className="match-card__logo-placeholder" style={{ color: match.awayColor }}>
                                    {match.awaySymbol}
                                  </div>
                                </div>

                                <div className="match-card__score-board">
                                  {match.awayScore !== undefined && match.homeScore !== undefined ? (
                                    <>
                                      <span className="match-card__score">{match.awayScore}</span>
                                      <span className="match-card__score-divider">:</span>
                                      <span className="match-card__score">{match.homeScore}</span>
                                    </>
                                  ) : (
                                    <span className="match-card__vs-label">VS</span>
                                  )}
                                </div>

                                <div className="match-card__team match-card__team--home">
                                  <div className="match-card__logo-placeholder" style={{ color: match.homeColor }}>
                                    {match.homeSymbol}
                                  </div>
                                  <span className="match-card__team-name">{match.homeTeam}</span>
                                </div>
                              </div>

                              <div className="match-card__venue-col">
                                <span className="match-card__venue">{match.stadium}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ));
                  })()}
                </div>
              </div>
            </div>
          </section>
        </>
      )}

      <footer className="footer">
        <div className="footer__container">
          <div className="footer__info">
            <div className="footer__logo">
              <img className="footer__logo-img" src="/klb-logo-256.svg" alt="KLB Logo" />
              <span className="footer__logo-text">KLB</span>
            </div>
            <p className="footer__desc">
              Krown League Baseball은 대한민국 야구의 새로운 역사와 혁신을 만들어갑니다.
            </p>
          </div>
          <div className="footer__links-section">
            <div className="footer__link-group">
              <h4 className="footer__link-title">League</h4>
              <a href="#intro" className="footer__link">소개</a>
              <a href="#schedule" className="footer__link">일정 진행</a>
              <a href="#teams" className="footer__link">리그 및 구단</a>
            </div>
            <div className="footer__link-group">
              <h4 className="footer__link-title">Support</h4>
              <a href="#live" className="footer__link">LIVE</a>
              <a href="#community" className="footer__link">커뮤니티</a>
              <a href="#terms" className="footer__link">이용약관</a>
            </div>
          </div>
        </div>
        <div className="footer__bottom">
          <p className="footer__copyright">
            © 2026 Krown League Baseball. All rights reserved.
          </p>
        </div>
      </footer>
    </>
  )
}

export default App

