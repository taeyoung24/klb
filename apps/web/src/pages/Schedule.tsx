import { useEffect, useState } from 'react';

import { getCalendarEvents, type CalendarEvent } from '../api/calendar';
import { getClubs, type Club } from '../api/clubs';
import { getMatches, type Match } from '../api/matches';
import { getSystemInfo } from '../api/system';
import TeamLogo from '../components/TeamLogo/TeamLogo';
import { BASE_YEAR } from '../constants/config';
import { simDayToDate, simDayToDateStr } from '../utils/date';
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

const getMatchTimeByDayOfWeek = (dayOfWeek: number) => {
  if (dayOfWeek === 0) return '14:00';
  if (dayOfWeek === 6) return '17:00';
  return '18:30';
};

export default function Schedule() {
  const [year, setYear] = useState<number | null>(null);
  const [month, setMonth] = useState<number | null>(null);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [allMatches, setAllMatches] = useState<Match[]>([]);
  const [calendarEventsMap, setCalendarEventsMap] = useState<Record<string, CalendarEvent[]>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const daysInMonth = (year && month) ? new Date(year, month, 0).getDate() : 0;
  const firstDayOfWeek = (year && month) ? new Date(year, month - 1, 1).getDay() : 0;
  const emptyDays = Array.from({ length: firstDayOfWeek });
  const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  // 1-1. 초기 마운트 시 전체 구단 정보 및 현재 시스템 연도/월/일 로드
  useEffect(() => {
    Promise.all([getClubs(), getSystemInfo()])
      .then(([clubsList, sysInfo]) => {
        const cMap: Record<number, Club> = {};
        clubsList.forEach((c) => {
          cMap[c.id] = c;
        });
        setClubsMap(cMap);

        if (sysInfo) {
          const sysYear = sysInfo.season_year || BASE_YEAR;
          setYear(sysYear);

          const currentSimDay = sysInfo.current_sim_day || 1;
          const currentDate = simDayToDate(currentSimDay);
          setMonth(currentDate.getMonth() + 1);
          setSelectedDay(currentDate.getDate());
        }
      })
      .catch((e) => {
        console.error('Failed to load initial schedule metadata', e);
      });
  }, []);

  // 1-2. 선택된 연도(year) 변경 시 달력 주요 이벤트 조회
  useEffect(() => {
    if (!year) return;

    getCalendarEvents(year)
      .then((eventsList) => {
        const evMap: Record<string, CalendarEvent[]> = {};
        eventsList.forEach((ev) => {
          if (!evMap[ev.date]) evMap[ev.date] = [];
          evMap[ev.date].push(ev);
        });
        setCalendarEventsMap(evMap);
      })
      .catch((e) => {
        console.error('Failed to load calendar events for year', e);
      });
  }, [year]);

  // 2. 선택된 연도/월(year, month)에 해당하는 시작일~종료일 범위 매치 쿼리
  useEffect(() => {
    if (!year || !month) return;

    setIsLoading(true);
    const startDateStr = `${year}-${String(month).padStart(2, '0')}-01`;
    const lastDay = new Date(year, month, 0).getDate();
    const endDateStr = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

    getMatches({ start_date: startDateStr, end_date: endDateStr })
      .then((matchesList) => {
        setAllMatches(matchesList);
        setIsLoading(false);
      })
      .catch((e) => {
        console.error('Failed to load matches for month range', e);
        setAllMatches([]);
        setIsLoading(false);
      });
  }, [year, month]);

  // ISO 날짜 문자열(YYYY-MM-DD)을 키로 한 매치 맵핑 (BASE_YEAR 기준 정확한 날짜 변환)
  const matchesByDateStr = allMatches.reduce<Record<string, Match[]>>((acc, m) => {
    const dStr = simDayToDateStr(m.sim_day);
    if (!acc[dStr]) acc[dStr] = [];
    acc[dStr].push(m);
    return acc;
  }, {});

  const getMatchItemsForDay = (dayNum: number | null): MatchItem[] => {
    if (!year || !month || !dayNum) return [];
    const targetDate = new Date(year, month - 1, dayNum);
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
    const rawMatches = matchesByDateStr[dateStr] || [];
    const dayOfWeek = targetDate.getDay();
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

  const selectedMatchItems = selectedDay ? getMatchItemsForDay(selectedDay) : [];

  const activeYear = year || BASE_YEAR;
  const visibleYears = Array.from({ length: 9 }, (_, i) => activeYear - 4 + i);

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
                const distance = Math.abs(y - activeYear);
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
                const dateStr = (year && month) ? `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}` : '';
                const dayMatches = matchesByDateStr[dateStr] || [];
                const hasMatches = dayMatches.length > 0;
                const dayEvents = calendarEventsMap[dateStr] || [];
                const isSelected = day === selectedDay;
                const dayOfWeek = (year && month) ? new Date(year, month - 1, day).getDay() : 0;

                return (
                  <div
                    key={day}
                    className={`schedule__day-cell ${isSelected ? 'schedule__day-cell--selected' : ''} ${hasMatches ? 'schedule__day-cell--has-matches' : ''
                      }`}
                    onClick={() => setSelectedDay(day)}
                  >
                    <span
                      className={`schedule__day-num ${dayOfWeek === 0 ? 'schedule__day-num--sun' : dayOfWeek === 6 ? 'schedule__day-num--sat' : ''
                        }`}
                    >
                      {day}
                    </span>
                    {dayEvents.length > 0 && (
                      <div className="schedule__event-container">
                        {dayEvents.map((ev, idx) => (
                          <span
                            key={idx}
                            className={`schedule__event-badge schedule__event-badge--${ev.event_type.toLowerCase()}`}
                          >
                            {ev.label}
                          </span>
                        ))}
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
