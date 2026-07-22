import { useState } from 'react';
import { FaChevronLeft, FaChevronRight, FaCalendarAlt, FaMapMarkerAlt, FaClock } from 'react-icons/fa';
import './Schedule.css';

interface MatchItem {
  id: number;
  league: string;
  time: string;
  stadium: string;
  status: '종료' | '예정' | '진행중';
  awayTeam: { name: string; symbol: string; color: string; score?: number };
  homeTeam: { name: string; symbol: string; color: string; score?: number };
}

export default function Schedule() {
  const [selectedDay, setSelectedDay] = useState<number>(17);

  // 2026년 7월 매치 하드코딩 목데이터 (일자별 맵핑)
  const scheduleData: Record<number, MatchItem[]> = {
    15: [
      {
        id: 101,
        league: '매그놀리아 리그',
        time: '18:30',
        stadium: '광주 무등야구장',
        status: '종료',
        awayTeam: { name: '광주 호크스', symbol: 'H', color: '#555555', score: 4 },
        homeTeam: { name: '대전 타이탄', symbol: 'T', color: '#ffffff', score: 2 },
      },
    ],
    16: [
      {
        id: 102,
        league: '젠티아나 리그',
        time: '18:30',
        stadium: '대구 시민야구장',
        status: '종료',
        awayTeam: { name: '대구 스파크', symbol: 'S', color: '#555555', score: 3 },
        homeTeam: { name: '인천 베어스', symbol: 'B', color: '#5c71fb', score: 6 },
      },
    ],
    17: [
      {
        id: 103,
        league: '아젤리아 리그',
        time: '18:30',
        stadium: '서울 잠실야구장',
        status: '종료',
        awayTeam: { name: '서울 코멧스', symbol: 'C', color: '#888888', score: 5 },
        homeTeam: { name: '부산 제니스', symbol: 'Z', color: '#f8369a', score: 3 },
      },
      {
        id: 104,
        league: '카멜리아 리그',
        time: '18:30',
        stadium: '창원 파크',
        status: '종료',
        awayTeam: { name: '창원 드래곤스', symbol: 'D', color: '#888888', score: 2 },
        homeTeam: { name: '수원 나이츠', symbol: 'K', color: '#d22828', score: 4 },
      },
    ],
    18: [
      {
        id: 105,
        league: '아젤리아 리그',
        time: '17:00',
        stadium: '서울 잠실야구장',
        status: '예정',
        awayTeam: { name: '서울 코멧스', symbol: 'C', color: '#888888' },
        homeTeam: { name: '부산 제니스', symbol: 'Z', color: '#f8369a' },
      },
      {
        id: 106,
        league: '카멜리아 리그',
        time: '17:00',
        stadium: '창원 파크',
        status: '예정',
        awayTeam: { name: '창원 드래곤스', symbol: 'D', color: '#888888' },
        homeTeam: { name: '수원 나이츠', symbol: 'K', color: '#d22828' },
      },
    ],
    19: [
      {
        id: 107,
        league: '아젤리아 리그',
        time: '14:00',
        stadium: '서울 잠실야구장',
        status: '예정',
        awayTeam: { name: '서울 코멧스', symbol: 'C', color: '#888888' },
        homeTeam: { name: '부산 제니스', symbol: 'Z', color: '#f8369a' },
      },
    ],
    24: [
      {
        id: 108,
        league: '젠티아나 리그',
        time: '18:30',
        stadium: '인천 문학야구장',
        status: '예정',
        awayTeam: { name: '인천 베어스', symbol: 'B', color: '#888888' },
        homeTeam: { name: '대구 스파크', symbol: 'S', color: '#5c71fb' },
      },
    ],
  };

  // 2026년 7월: 수요일 시작(빈 칸 3개: 일,월,화), 총 31일
  const emptyDays = [null, null, null];
  const daysInJuly = Array.from({ length: 31 }, (_, i) => i + 1);

  const selectedMatches = scheduleData[selectedDay] || [];

  return (
    <div className="schedule">
      <div className="schedule__container">
        {/* 달력 & 상세 사이드 패널 그리드 */}
        <div className="schedule__body">
          {/* 좌측: 월간 달력 */}
          <div className="schedule__calendar-card">
            <div className="schedule__month-bar">
              <button className="schedule__month-nav-btn" aria-label="이전 달">
                <FaChevronLeft />
              </button>
              <h2 className="schedule__month-label">
                <FaCalendarAlt className="schedule__calendar-icon" />
                2026년 7월
              </h2>
              <button className="schedule__month-nav-btn" aria-label="다음 달">
                <FaChevronRight />
              </button>
            </div>

            {/* 달력 헤더 (요일) */}
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

              {daysInJuly.map((day) => {
                const matches = scheduleData[day];
                const hasMatches = matches && matches.length > 0;
                const isSelected = day === selectedDay;
                const dayOfWeek = (day + 3 - 1) % 7; // 0:일, 6:토

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
                        <span className="schedule__match-count">{matches.length}경기</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* 우측: 선택한 날짜 세부 경기 목록 패널 */}
          <div className="schedule__detail-panel">
            <h3 className="schedule__detail-title">
              2026년 7월 {selectedDay}일 경기 세부사항
            </h3>

            {selectedMatches.length > 0 ? (
              <div className="schedule__match-list">
                {selectedMatches.map((match) => (
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
