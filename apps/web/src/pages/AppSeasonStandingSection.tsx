import { useState, useEffect } from 'react'
import { getClubs, type Club } from '../api/clubs'
import { getStandings, type DailyClubStanding } from '../api/standings'
import './AppSeasonStandingSection.css'

const LEAGUES = [
  { code: 'AL' as const, id: 1, name: '아젤리아' },
  { code: 'CL' as const, id: 2, name: '카멜리아' },
  { code: 'GL' as const, id: 3, name: '젠티아나' },
  { code: 'ML' as const, id: 4, name: '매그놀리아' },
];

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

const getSimDayFromDate = (date: Date, year: number): number => {
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const baseDate = new Date(year, 0, 1);
  const diffTime = target.getTime() - baseDate.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  return diffDays + 1;
};

const formatPct = (pct: number) => {
  if (pct === 1) return "1.000";
  if (pct === 0) return ".000";
  const formatted = pct.toFixed(3);
  return formatted.startsWith("0") ? formatted.substring(1) : formatted;
};

const formatGb = (gb: number) => {
  if (gb === 0) return "-";
  return (gb / 10).toFixed(1);
};

const formatStreak = (streak: number) => {
  if (streak === 0) return "-";
  if (streak > 0) return `${streak}승`;
  return `${Math.abs(streak)}패`;
};

const getTeamMeta = (teamCode: string, nameKo: string) => {
  return TEAM_META[teamCode] || { color: "#cccccc", symbol: nameKo[0] || "T" };
};

interface AppSeasonStandingSectionProps {
  matchDate: Date;
  seasonYear: number | null;
  isSeasonYearLoaded: boolean;
}

export default function AppSeasonStandingSection({
  matchDate,
  seasonYear,
  isSeasonYearLoaded,
}: AppSeasonStandingSectionProps) {
  const [activeLeague, setActiveLeague] = useState<'AL' | 'CL' | 'GL' | 'ML'>('AL')
  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [allStandings, setAllStandings] = useState<Record<'AL' | 'CL' | 'GL' | 'ML', DailyClubStanding[]>>({
    AL: [],
    CL: [],
    GL: [],
    ML: [],
  });
  const [isStandingsLoaded, setIsStandingsLoaded] = useState(false);

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

  useEffect(() => {
    const simDay = getSimDayFromDate(matchDate, seasonYear || 2026);
    setIsStandingsLoaded(false);

    Promise.all(
      LEAGUES.map(league => getStandings(league.id, simDay))
    )
      .then(([alData, clData, glData, mlData]) => {
        setAllStandings({
          AL: alData,
          CL: clData,
          GL: glData,
          ML: mlData,
        });
        setIsStandingsLoaded(true);
      })
      .catch(e => {
        console.error("Failed to fetch all standings", e);
        setAllStandings({
          AL: [],
          CL: [],
          GL: [],
          ML: [],
        });
        setIsStandingsLoaded(true);
      });
  }, [matchDate, seasonYear]);

  const isSectionLoaded = isSeasonYearLoaded && isStandingsLoaded && Object.keys(clubsMap).length > 0;

  return (
    <section className="section section--black section--first">
      <div className="section__container">
        {/* 시즌 진행 현황 5단계 스텝 바 */}
        <div className={`progress-status ${isSectionLoaded ? 'loaded' : 'loading'}`}>
          <div className="progress-status__season-title">KLB {seasonYear}</div>
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
        <div className={`standings ${isSectionLoaded ? 'loaded' : 'loading'}`}>
          <div className="standings__header">
            <h3 className="standings__title">
              {matchDate.getMonth() + 1}.{matchDate.getDate()} {LEAGUES.find(l => l.code === activeLeague)?.name}
            </h3>
            <div className="standings__tabs">
              {LEAGUES.map((league) => (
                <button
                  key={league.code}
                  className={`standings__tab ${activeLeague === league.code ? 'standings__tab--active' : ''}`}
                  onClick={() => setActiveLeague(league.code)}
                >
                  {league.code}
                </button>
              ))}
            </div>
          </div>

          <div className="standings__table-wrapper">
            <table className="standings__table">
              <thead>
                <tr>
                  <th className="standings__rank-col">순위</th>
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
                {allStandings[activeLeague].map((row, idx) => {
                  const club = clubsMap[row.club_id];
                  const clubName = club ? club.name_ko : '로딩중...';
                  const teamCode = club ? club.team_code : '';
                  const meta = getTeamMeta(teamCode, clubName);

                  const isTied = allStandings[activeLeague].filter(item => item.rank === row.rank).length > 1;
                  const displayRank = isTied ? `T${row.rank}` : row.rank;

                  return (
                    <tr key={`${row.club_id}-${idx}`}>
                      <td className={`standings__rank ${row.rank <= 4 ? 'standings__rank--playoff' : ''}`}>{displayRank}</td>
                      <td className="standings__team-name">
                        <div className="standings__team-cell">
                          <div
                            className="standings__team-logo-placeholder"
                            style={{ color: meta.color }}
                          >
                            {meta.symbol}
                          </div>
                          <span className="standings__team-text">{clubName}</span>
                        </div>
                      </td>
                      <td>{row.games_played}</td>
                      <td>{row.wins}</td>
                      <td>{row.draws}</td>
                      <td>{row.losses}</td>
                      <td className="standings__pct">{formatPct(row.win_rate)}</td>
                      <td>{formatGb(row.games_back)}</td>
                      <td>{formatStreak(row.streak)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
