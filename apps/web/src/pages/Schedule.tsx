import { useEffect, useState } from 'react';
import { FaChevronLeft, FaChevronRight, FaCalendarAlt, FaMapMarkerAlt, FaClock } from 'react-icons/fa';
import { getClubs, type Club } from '../api/clubs';
import { getMatches, type Match } from '../api/matches';
import { getSystemInfo } from '../api/system';
import './Schedule.css';

const LEAGUES: Record<number, string> = {
  1: '아젤리아 리그',
  2: '카멜리아 리그',
  3: '젠티아나 리그',
  4: '매그놀리아 리그',
};

const TEAM_META: Record<string, { color: string; symbol: string }> = {
  // AL
  COM: { color: "#1f77b4", symbol: "C" },
  END: { color: "#8c564b", symbol: "E" },
  PHN: { color: "#7f7f7f", symbol: "P" },
  PUM: { color: "#17becf", symbol: "K" },
  GUA: { color: "#bcbd22", symbol: "G" },
  SAT: { color: "#ff7f0e", symbol: "T" },
  SEN: { color: "#9467bd", symbol: "S" },
  VAL: { color: "#e377c2", symbol: "V" },
  WHL: { color: "#2ca02c", symbol: "W" },
  ZEN: { color: "#e01e3c", symbol: "Z" },
  // CL
  ARC: { color: "#4682b4", symbol: "A" },
  CAT: { color: "#2f4f4f", symbol: "C" },
  DIN: { color: "#556b2f", symbol: "D" },
  EFL: { color: "#ff4500", symbol: "F" },
  FST: { color: "#daa520", symbol: "I" },
  HRO: { color: "#8b008b", symbol: "H" },
  RED: { color: "#ff0000", symbol: "R" },
  SOL: { color: "#ffd700", symbol: "O" },
  TAL: { color: "#d2691e", symbol: "L" },
  UND: { color: "#4b0082", symbol: "U" },
  // GL
  WIS: { color: "#00ffff", symbol: "C" },
  FAL: { color: "#708090", symbol: "F" },
  NUF: { color: "#afeeee", symbol: "Z" },
  GLI: { color: "#ee82ee", symbol: "G" },
  TKN: { color: "#b0c4de", symbol: "K" },
  VPE: { color: "#db7093", symbol: "P" },
  GSW: { color: "#40e0d0", symbol: "S" },
  IVO: { color: "#ffc0cb", symbol: "V" },
  WYV: { color: "#ba55d3", symbol: "W" },
  HOB: { color: "#cd853f", symbol: "B" },
  // ML
  BLU: { color: "#1e90ff", symbol: "B" },
  DRG: { color: "#32cd32", symbol: "D" },
  EAG: { color: "#ff8c00", symbol: "E" },
  ETR: { color: "#9932cc", symbol: "T" },
  GIA: { color: "#8b0000", symbol: "G" },
  LUN: { color: "#e9967a", symbol: "L" },
  PST: { color: "#00ced1", symbol: "P" },
  RPN: { color: "#9370db", symbol: "N" },
  UNI: { color: "#ff69b4", symbol: "U" },
  VBC: { color: "#000000", symbol: "C" },
};

interface MatchItem {
  id: number;
  league: string;
  time: string;
  stadium: string;
  status: '종료' | '예정' | '진행중' | '취소';
  awayTeam: { name: string; symbol: string; color: string; score?: number };
  homeTeam: { name: string; symbol: string; color: string; score?: number };
}

const getSimDayFromYearMonthDay = (year: number, month: number, day: number): number => {
  const baseDate = new Date(year, 0, 1);
  const targetDate = new Date(year, month - 1, day);
  const diffTime = targetDate.getTime() - baseDate.getTime();
  return Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1;
};

const getTeamMeta = (teamCode: string, nameKo: string) => {
  return TEAM_META[teamCode] || { color: '#cccccc', symbol: nameKo[0] || 'T' };
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

  const handlePrevMonth = () => {
    if (month === 1) {
      setYear((y) => y - 1);
      setMonth(12);
    } else {
      setMonth((m) => m - 1);
    }
    setSelectedDay(1);
  };

  const handleNextMonth = () => {
    if (month === 12) {
      setYear((y) => y + 1);
      setMonth(1);
    } else {
      setMonth((m) => m + 1);
    }
    setSelectedDay(1);
  };

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

      const awayMeta = awayClub ? getTeamMeta(awayClub.team_code, awayClub.name_ko) : { color: '#888888', symbol: 'A' };
      const homeMeta = homeClub ? getTeamMeta(homeClub.team_code, homeClub.name_ko) : { color: '#ffffff', symbol: 'H' };

      let statusStr: '종료' | '예정' | '진행중' | '취소' = '예정';
      if (m.status === 'COMPLETED') statusStr = '종료';
      else if (m.status === 'IN_PROGRESS') statusStr = '진행중';
      else if (m.status === 'CANCELED') statusStr = '취소';

      let leagueName = 'KLB 리그';
      if (homeClub && awayClub) {
        if (homeClub.league_id === awayClub.league_id) {
          leagueName = LEAGUES[homeClub.league_id] || 'KLB 리그';
        } else {
          leagueName = '크라운 정예리그';
        }
      }

      const stadiumStr = homeClub
        ? homeClub.stadium_name_ko || `${homeClub.hometown_ko} 야구장`
        : '야구장';

      return {
        id: m.id,
        league: leagueName,
        time: timeStr,
        stadium: stadiumStr,
        status: statusStr,
        awayTeam: {
          name: awayName,
          symbol: awayMeta.symbol,
          color: awayMeta.color,
          score: m.status === 'COMPLETED' ? (m.away_score ?? 0) : undefined,
        },
        homeTeam: {
          name: homeName,
          symbol: homeMeta.symbol,
          color: homeMeta.color,
          score: m.status === 'COMPLETED' ? (m.home_score ?? 0) : undefined,
        },
      };
    });
  };

  const selectedMatchItems = getMatchItemsForDay(selectedDay);

  return (
    <div className="schedule">
      <div className="schedule__container">
        <div className="schedule__body">
          <div className="schedule__calendar-card">
            <div className="schedule__month-bar">
              <button className="schedule__month-nav-btn" onClick={handlePrevMonth} aria-label="이전 달">
                <FaChevronLeft />
              </button>
              <h2 className="schedule__month-label">
                <FaCalendarAlt className="schedule__calendar-icon" />
                {year}년 {month}월
              </h2>
              <button className="schedule__month-nav-btn" onClick={handleNextMonth} aria-label="다음 달">
                <FaChevronRight />
              </button>
            </div>

            <div className="schedule__week-header">
              <span className="schedule__week-day schedule__week-day--sun">일</span>
              <span className="schedule__week-day">월</span>
              <span className="schedule__week-day">화</span>
              <span className="schedule__week-day">수</span>
              <span className="schedule__week-day">목</span>
              <span className="schedule__week-day">금</span>
              <span className="schedule__week-day schedule__week-day--sat">토</span>
            </div>

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
          </div>

          <div className="schedule__detail-panel">
            <h3 className="schedule__detail-title">
              {year}년 {month}월 {selectedDay}일 경기 세부사항
            </h3>

            {isLoading ? (
              <div className="schedule__no-matches">일정 데이터를 로딩하고 있습니다...</div>
            ) : selectedMatchItems.length > 0 ? (
              <div className="schedule__match-list">
                {selectedMatchItems.map((match) => (
                  <a key={match.id} href="#match-detail" className="schedule__match-card">
                    <div className="schedule__match-meta">
                      <span className="schedule__match-league">{match.league}</span>
                      <span className={`schedule__match-status schedule__match-status--${match.status}`}>
                        {match.status}
                      </span>
                    </div>

                    <div className="schedule__match-teams">
                      <div className="schedule__team-info">
                        <span className="schedule__team-name">{match.awayTeam.name}</span>
                        {match.awayTeam.score !== undefined && (
                          <span className="schedule__team-score">{match.awayTeam.score}</span>
                        )}
                      </div>

                      <div className="schedule__vs-divider">VS</div>

                      <div className="schedule__team-info schedule__team-info--home">
                        {match.homeTeam.score !== undefined && (
                          <span className="schedule__team-score">{match.homeTeam.score}</span>
                        )}
                        <span className="schedule__team-name">{match.homeTeam.name}</span>
                      </div>
                    </div>

                    <div className="schedule__match-footer">
                      <span className="schedule__match-info-item">
                        <FaClock /> {match.time}
                      </span>
                      <span className="schedule__match-info-item">
                        <FaMapMarkerAlt /> {match.stadium}
                      </span>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <div className="schedule__no-matches">
                해당 일자에는 예정된 경기가 없습니다.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
