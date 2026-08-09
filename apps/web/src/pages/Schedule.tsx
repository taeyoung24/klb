import { useEffect, useState } from 'react';

import { getClubs, type Club } from '../api/clubs';
import { getMatches, type Match } from '../api/matches';
import { getSystemInfo } from '../api/system';
import TeamLogo from '../components/TeamLogo/TeamLogo';
import './Schedule.css';

const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

interface MatchItem {
  id: number;
  league: string;
  time: string;
  stadium: string;
  status: '종료' | '예정' | '진행중' | '취소';
  awayTeam: { name: string; code?: string; score?: number };
  homeTeam: { name: string; code?: string; score?: number };
}

const getSimDayFromYearMonthDay = (year: number, month: number, day: number): number => {
  const baseDate = new Date(year, 0, 1);
  const targetDate = new Date(year, month - 1, day);
  const diffTime = targetDate.getTime() - baseDate.getTime();
  return Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1;
};

const getMatchTimeByDayOfWeek = (dayOfWeek: number) => {
  if (dayOfWeek === 0) return '14:00';
  if (dayOfWeek === 6) return '17:00';
  return '18:30';
};

export default function Schedule() {
  const [year, setYear] = useState<number>(2026);
  const [month, setMonth] = useState<number>(7);
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [allMatches, setAllMatches] = useState<Match[]>([]);
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

        if (sysInfo) {
          const sysYear = sysInfo.season_year || 2026;
          setYear(sysYear);

          const currentSimDay = sysInfo.current_sim_day || 1;
          const currentDate = new Date(sysYear, 0, currentSimDay);
          setMonth(currentDate.getMonth() + 1);
          setSelectedDay(currentDate.getDate());
        }
        setIsLoading(false);
      })
      .catch((e) => {
        console.error('Failed to load schedule data', e);
        setIsLoading(false);
      });
  }, []);

  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDayOfWeek = new Date(year, month - 1, 1).getDay();
  const emptyDays = Array.from({ length: firstDayOfWeek });
  const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  const matchesBySimDay = allMatches.reduce<Record<number, Match[]>>((acc, m) => {
    if (!acc[m.sim_day]) acc[m.sim_day] = [];
    acc[m.sim_day].push(m);
    return acc;
  }, {});

  const getMatchItemsForDay = (dayNum: number): MatchItem[] => {
    const simDay = getSimDayFromYearMonthDay(year, month, dayNum);
    const rawMatches = matchesBySimDay[simDay] || [];
    const dayOfWeek = new Date(year, month - 1, dayNum).getDay();
    const timeStr = getMatchTimeByDayOfWeek(dayOfWeek);

    return rawMatches.map((m) => {
      const awayClub = clubsMap[m.away_club_id];
      const homeClub = clubsMap[m.home_club_id];

      const awayName = awayClub ? `${awayClub.hometown_ko} ${awayClub.name_ko}` : `팀 #${m.away_club_id}`;
      const homeName = homeClub ? `${homeClub.hometown_ko} ${homeClub.name_ko}` : `팀 #${m.home_club_id}`;

      let statusStr: '종료' | '예정' | '진행중' | '취소' = '예정';
      if (m.status === 'COMPLETED') statusStr = '종료';
      else if (m.status === 'IN_PROGRESS') statusStr = '진행중';
      else if (m.status === 'CANCELED') statusStr = '취소';

      let leagueName = 'KLB';
      if (homeClub && awayClub) {
        if (homeClub.league_id === awayClub.league_id) {
          const LEAGUE_SYMBOLS: Record<number, string> = {
            1: 'AL',
            2: 'CL',
            3: 'GL',
            4: 'ML',
          };
          leagueName = LEAGUE_SYMBOLS[homeClub.league_id] || 'KLB';
        } else {
          leagueName = 'EL';
        }
      }

      const stadiumStr = m.stadium?.name_ko || homeClub?.home_stadium?.name_ko || (homeClub
        ? homeClub.stadium_name_ko || `${homeClub.hometown_ko} 야구장`
        : '야구장');

      return {
        id: m.id,
        league: leagueName,
        time: timeStr,
        stadium: stadiumStr,
        status: statusStr,
        awayTeam: {
          name: awayName,
          code: awayClub?.team_code,
          score: m.status === 'COMPLETED' ? (m.away_score ?? 0) : undefined,
        },
        homeTeam: {
          name: homeName,
          code: homeClub?.team_code,
          score: m.status === 'COMPLETED' ? (m.home_score ?? 0) : undefined,
        },
      };
    });
  };

  const selectedMatchItems = getMatchItemsForDay(selectedDay);

  const visibleYears = Array.from({ length: 9 }, (_, i) => year - 4 + i);

  return (
    <div className="schedule">
      {/* 1. 상단 달력 영역 (Full Width 딤드 배경 + 고정 높이 + 2열 구조) */}
      <section className="schedule__calendar-section">
        <div className="schedule__calendar-container">
          {/* 1열: 시즌 선택 (연도 리스트 - 중앙 정렬 9개 휠 픽커) */}
          <aside className="schedule__season-col">
            <h3 className="schedule__col-title">시즌</h3>
            <div className="schedule__season-list">
              {visibleYears.map((y) => {
                const distance = Math.abs(y - year);
                const isSelected = y === year;
                return (
                  <button
                    key={y}
                    type="button"
                    className={`schedule__season-btn ${isSelected ? 'schedule__season-btn--active' : ''} schedule__season-btn--dist-${distance}`}
                    onClick={() => {
                      setYear(y);
                      setSelectedDay(1);
                    }}
                  >
                    {y}
                  </button>
                );
              })}
            </div>
          </aside>

          {/* 2열: 달 선택 및 달력 그리드 */}
          <main className="schedule__main-col">
            {/* 달 선택 헤더 (1~12월 동그라미) */}
            <div className="schedule__month-header">
              <div className="schedule__month-pills">
                {MONTHS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    className={`schedule__month-pill ${m === month ? 'schedule__month-pill--active' : ''}`}
                    onClick={() => {
                      setMonth(m);
                      setSelectedDay(1);
                    }}
                  >
                    {m}월
                  </button>
                ))}
              </div>
            </div>

            {/* 요일 헤더 */}
            <div className="schedule__week-header">
              <span className="schedule__week-day schedule__week-day--sun">일</span>
              <span className="schedule__week-day">월</span>
              <span className="schedule__week-day">화</span>
              <span className="schedule__week-day">수</span>
              <span className="schedule__week-day">목</span>
              <span className="schedule__week-day">금</span>
              <span className="schedule__week-day schedule__week-day--sat">토</span>
            </div>

            {/* 달력 날짜 그리드 */}
            <div className="schedule__days-grid">
              {emptyDays.map((_, idx) => (
                <div key={`empty-${idx}`} className="schedule__day-cell schedule__day-cell--empty" />
              ))}

              {daysArray.map((day) => {
                const daySimDay = getSimDayFromYearMonthDay(year, month, day);
                const dayMatches = matchesBySimDay[daySimDay] || [];
                const hasMatches = dayMatches.length > 0;
                const isSelected = day === selectedDay;
                const dayOfWeek = new Date(year, month - 1, day).getDay();

                return (
                  <div
                    key={day}
                    className={`schedule__day-cell ${isSelected ? 'schedule__day-cell--selected' : ''} ${
                      hasMatches ? 'schedule__day-cell--has-matches' : ''
                    }`}
                    onClick={() => setSelectedDay(day)}
                  >
                    <span
                      className={`schedule__day-num ${
                        dayOfWeek === 0 ? 'schedule__day-num--sun' : dayOfWeek === 6 ? 'schedule__day-num--sat' : ''
                      }`}
                    >
                      {day}
                    </span>
                    {hasMatches && (
                      <div className="schedule__match-indicator">
                        <span className="schedule__match-count">{dayMatches.length}경기</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </main>
        </div>
      </section>

      {/* 2. 하단 경기 세부사항 영역 */}
      <div className="schedule__detail-container">
        <div className="schedule__detail-panel">
          <h2 className="schedule__main-title">
            {year}년 {month}월 {selectedDay}일 일정
          </h2>

          <section className="schedule__matches-section">
            <h3 className="schedule__section-title">경기 일정</h3>

            {isLoading ? (
              <div className="schedule__no-matches">일정 데이터를 로딩하고 있습니다...</div>
            ) : selectedMatchItems.length > 0 ? (
              <div className="schedule__match-list">
                {selectedMatchItems.map((match) => (
                  <a key={match.id} href={`#match-detail?id=${match.id}`} className="schedule__match-card">
                    {/* 왼쪽 열: 리그명과 시간 (2행) */}
                    <div className="schedule__match-left-col">
                      <span className="schedule__match-league">{match.league}</span>
                      <span className="schedule__match-time">{match.time}</span>
                    </div>

                    {/* 오른쪽 주 영역: 어웨이팀 - 경기상태 - 홈팀 */}
                    <div className="schedule__match-main-col">
                      {/* 어웨이 팀 */}
                      <div className="schedule__team-info schedule__team-info--away">
                        <div className="schedule__team-brand">
                          <TeamLogo teamCode={match.awayTeam.code} teamName={match.awayTeam.name} size={20} />
                          <span className="schedule__team-name">{match.awayTeam.name}</span>
                        </div>
                        {match.awayTeam.score !== undefined && (
                          <span className="schedule__team-score">{match.awayTeam.score}</span>
                        )}
                      </div>

                      {/* 중앙 경기상태 */}
                      <div className="schedule__match-status-wrap">
                        <span className={`schedule__match-status schedule__match-status--${match.status}`}>
                          {match.status}
                        </span>
                      </div>

                      {/* 홈 팀 */}
                      <div className="schedule__team-info schedule__team-info--home">
                        {match.homeTeam.score !== undefined ? (
                          <span className="schedule__team-score">{match.homeTeam.score}</span>
                        ) : (
                          <span />
                        )}
                        <div className="schedule__team-brand">
                          <span className="schedule__team-name">{match.homeTeam.name}</span>
                          <TeamLogo teamCode={match.homeTeam.code} teamName={match.homeTeam.name} size={20} />
                        </div>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <div className="schedule__no-matches">
                해당 일자에는 예정된 경기가 없습니다.
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
