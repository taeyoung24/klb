import { useState } from 'react'
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import './AppScheduleSection.css'

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

interface AppScheduleSectionProps {
  matchDate: Date;
  onDateChange: (days: number) => void;
}

export default function AppScheduleSection({
  matchDate,
  onDateChange,
}: AppScheduleSectionProps) {
  const [activeTier, setActiveTier] = useState<'1군' | '2군' | '3군'>('1군')
  const [activeLeagueFilter, setActiveLeagueFilter] = useState<string>('전체')

  return (
    <section className="section section--light">
      <div className="section__container">
        <div className="section__header">
          <h2 className="section__title">통합 경기 일정</h2>
        </div>

        <div className="match-schedule">
          {/* 데이트 컨트롤러 */}
          <div className="match-schedule__date-controller">
            <button className="match-schedule__date-btn" onClick={() => onDateChange(-1)}>
              <FiChevronLeft size={16} style={{ display: 'block' }} />
            </button>
            <span className="match-schedule__date-text">{getDisplayMatchDate(matchDate)}</span>
            <button className="match-schedule__date-btn" onClick={() => onDateChange(1)}>
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
  );
}
