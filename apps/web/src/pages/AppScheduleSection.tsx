import { useEffect, useState } from 'react'
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import { getClubs, type Club } from '../api/clubs'
import { getMatches, type Match } from '../api/matches'
import TeamLogo from '../components/TeamLogo/TeamLogo'
import './AppScheduleSection.css'

const getSimDayFromDate = (date: Date, year: number): number => {
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const baseDate = new Date(year, 0, 1);
  const diffTime = target.getTime() - baseDate.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  return diffDays + 1;
};

const getDisplayMatchDate = (date: Date) => {
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekDays = ["일", "월", "화", "수", "목", "금", "토"];
  const weekDay = weekDays[date.getDay()];
  return `${year}.${month}.${day} (${weekDay})`;
};

const LEAGUE_MAPPING: Record<string, { id: number; name: string }> = {
  '아젤리아': { id: 1, name: '아젤리아 리그' },
  '카멜리아': { id: 2, name: '카멜리아 리그' },
  '젠티아나': { id: 3, name: '젠티아나 리그' },
  '매그놀리아': { id: 4, name: '매그놀리아 리그' },
};

const getStatusLabel = (status: string) => {
  if (status === 'COMPLETED') return '종료';
  if (status === 'IN_PROGRESS') return '진행중';
  if (status === 'CANCELED') return '취소';
  return '18:30';
};

interface AppScheduleSectionProps {
  matchDate: Date;
  onDateChange: (days: number) => void;
}

export default function AppScheduleSection({
  matchDate,
  onDateChange,
}: AppScheduleSectionProps) {
  const [activeTier, setActiveTier] = useState<'1군' | '2군' | '3군'>('1군');
  const [activeLeagueFilter, setActiveLeagueFilter] = useState<string>('전체');

  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [matches, setMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 1. 전체 구단 정보 조회
  useEffect(() => {
    getClubs()
      .then(list => {
        const map: Record<number, Club> = {};
        list.forEach(c => {
          map[c.id] = c;
        });
        setClubsMap(map);
      })
      .catch(e => {
        console.error("Failed to fetch clubs", e);
      });
  }, []);

  // 2. 선택 날짜(sim_day)에 따른 매치 목록 조회
  useEffect(() => {
    const simDay = getSimDayFromDate(matchDate, 2026);
    setIsLoading(true);
    getMatches({ sim_day: simDay })
      .then(res => {
        setMatches(res);
        setIsLoading(false);
      })
      .catch(e => {
        console.error("Failed to fetch matches", e);
        setMatches([]);
        setIsLoading(false);
      });
  }, [matchDate]);

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
              {['전체', '아젤리아', '카멜리아', '젠티아나', '매그놀리아'].map(league => (
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
            {isLoading ? (
              <div className="match-schedule__empty">경기 일정을 불러오는 중입니다...</div>
            ) : (() => {
              // 1. 선택한 등급 및 리그 필터에 따라 필터링 수행
              const filtered = matches.filter(match => {
                const homeClub = clubsMap[match.home_club_id];
                if (!homeClub) return false;

                // 2, 3군 리그 데이터는 DB에 현재 없음 ➔ 1군 필터만 지원
                if (activeTier !== '1군') return false;

                if (activeLeagueFilter === '전체') return true;

                const targetLeague = LEAGUE_MAPPING[activeLeagueFilter];
                return targetLeague ? homeClub.league_id === targetLeague.id : false;
              });

              if (filtered.length === 0) {
                return (
                  <div className="match-schedule__empty">
                    선택하신 날짜 및 리그에 예정된 경기가 없습니다.
                  </div>
                );
              }

              // 2. 리그별 그룹 생성
              const grouped: Record<string, Match[]> = {};
              filtered.forEach(match => {
                const homeClub = clubsMap[match.home_club_id];
                const leagueId = homeClub?.league_id || 1;

                // 매핑용 이름 획득
                let groupKey = '기타 리그';
                const foundEntry = Object.entries(LEAGUE_MAPPING).find(([_, val]) => val.id === leagueId);
                if (foundEntry) {
                  groupKey = `${foundEntry[0]} 리그`;
                }

                if (!grouped[groupKey]) {
                  grouped[groupKey] = [];
                }
                grouped[groupKey].push(match);
              });

              // 3. 그룹별 경기 렌더링
              return Object.entries(grouped).map(([groupName, list]) => (
                <div key={groupName} className="match-schedule__league-group">
                  <h4 className="match-schedule__group-title">{groupName}</h4>
                  <div className="match-schedule__grid">
                    {list.map((match) => {
                      const awayClub = clubsMap[match.away_club_id];
                      const homeClub = clubsMap[match.home_club_id];

                      const awayName = awayClub ? awayClub.team_code : 'AWAY';
                      const homeName = homeClub ? homeClub.team_code : 'HOME';

                      return (
                        <a key={match.id} href={`#match-detail?id=${match.id}`} className="match-card">
                          <div className="match-card__status-col">
                            <span className={`match-card__status-badge match-card__status-badge--${match.status === 'COMPLETED' ? 'ended' : match.status === 'IN_PROGRESS' ? 'live' : 'upcoming'}`}>
                              {getStatusLabel(match.status)}
                            </span>
                            <span className="match-card__time">18:30</span>
                          </div>

                          <div className="match-card__versus-col">
                            <div className="match-card__team match-card__team--away">
                              <span className="match-card__team-name">{awayName}</span>
                              <TeamLogo teamCode={awayClub?.team_code} teamName={awayClub?.name_ko} size={28} />
                            </div>

                            <div className="match-card__score-board">
                              {match.status === 'COMPLETED' || match.status === 'IN_PROGRESS' ? (
                                <>
                                  <span className="match-card__score">{match.away_score ?? 0}</span>
                                  <span className="match-card__score-divider">:</span>
                                  <span className="match-card__score">{match.home_score ?? 0}</span>
                                </>
                              ) : (
                                <span className="match-card__vs-label">VS</span>
                              )}
                            </div>

                            <div className="match-card__team match-card__team--home">
                              <TeamLogo teamCode={homeClub?.team_code} teamName={homeClub?.name_ko} size={28} />
                              <span className="match-card__team-name">{homeName}</span>
                            </div>
                          </div>

                          <div className="match-card__venue-col">
                            <span className="match-card__venue">
                              {match.stadium?.name_ko || homeClub?.home_stadium?.name_ko || homeClub?.stadium_name_ko || '야구장'}
                            </span>
                          </div>
                        </a>
                      );
                    })}
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
