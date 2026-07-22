import { useState } from 'react';
import './Records.css';

interface BatterRecord {
  rank: number;
  name: string;
  team: string;
  avg: string;
  hr: number;
  rbi: number;
  h: number;
  games: number;
}

interface PitcherRecord {
  rank: number;
  name: string;
  team: string;
  era: string;
  wins: number;
  losses: number;
  so: number;
  sv: number;
  ip: string;
}

export default function Records() {
  const [activeCategory, setActiveCategory] = useState<'batter' | 'pitcher'>('batter');

  const batterRankings: BatterRecord[] = [
    { rank: 1, name: '강태양', team: '서울 코멧스', avg: '.348', hr: 22, rbi: 78, h: 112, games: 84 },
    { rank: 2, name: '조유진', team: '부산 제니스', avg: '.332', hr: 18, rbi: 65, h: 104, games: 82 },
    { rank: 3, name: '이동현', team: '서울 코멧스', avg: '.315', hr: 25, rbi: 82, h: 98, games: 85 },
    { rank: 4, name: '박지환', team: '부산 제니스', avg: '.308', hr: 12, rbi: 49, h: 95, games: 80 },
    { rank: 5, name: '김민준', team: '대구 스파크', avg: '.298', hr: 15, rbi: 54, h: 91, games: 83 },
    { rank: 6, name: '장민호', team: '인천 베어스', avg: '.295', hr: 19, rbi: 61, h: 88, games: 81 },
    { rank: 7, name: '최현석', team: '서울 코멧스', avg: '.289', hr: 14, rbi: 52, h: 85, games: 84 },
    { rank: 8, name: '서동주', team: '광주 호크스', avg: '.283', hr: 9, rbi: 38, h: 82, games: 79 },
  ];

  const pitcherRankings: PitcherRecord[] = [
    { rank: 1, name: '김서진', team: '서울 코멧스', era: '2.45', wins: 12, losses: 3, so: 115, sv: 0, ip: '110.1' },
    { rank: 2, name: '박현우', team: '부산 제니스', era: '2.88', wins: 10, losses: 4, so: 98, sv: 0, ip: '103.0' },
    { rank: 3, name: '이준호', team: '대구 스파크', era: '3.12', wins: 9, losses: 5, so: 105, sv: 0, ip: '98.0' },
    { rank: 4, name: '최재혁', team: '인천 베어스', era: '3.35', wins: 8, losses: 6, so: 89, sv: 0, ip: '94.0' },
    { rank: 5, name: '정우진', team: '서울 코멧스', era: '1.85', wins: 3, losses: 1, so: 48, sv: 24, ip: '39.0' },
    { rank: 6, name: '한승민', team: '광주 호크스', era: '3.62', wins: 7, losses: 7, so: 82, sv: 0, ip: '89.2' },
    { rank: 7, name: '윤성호', team: '대전 타이탄', era: '3.78', wins: 6, losses: 8, so: 75, sv: 0, ip: '85.2' },
    { rank: 8, name: '임태양', team: '부산 제니스', era: '2.10', wins: 2, losses: 2, so: 42, sv: 18, ip: '34.1' },
  ];

  return (
    <div className="records">
      <div className="records__container">
        {/* 탭 네비게이션 */}
        <div className="records__tabs">
          <button
            className={`records__tab-btn ${activeCategory === 'batter' ? 'records__tab-btn--active' : ''}`}
            onClick={() => setActiveCategory('batter')}
          >
            타자 기록 순위
          </button>
          <button
            className={`records__tab-btn ${activeCategory === 'pitcher' ? 'records__tab-btn--active' : ''}`}
            onClick={() => setActiveCategory('pitcher')}
          >
            투수 기록 순위
          </button>
        </div>

        {/* 테이블 영역 */}
        <div className="records__table-wrapper">
          {activeCategory === 'batter' ? (
            <table className="records__table">
              <thead>
                <tr>
                  <th className="records__th-rank">순위</th>
                  <th className="records__th-player">선수명</th>
                  <th className="records__th-team">소속 구단</th>
                  <th>경기</th>
                  <th className="records__th-highlight">타율 (AVG)</th>
                  <th>안타 (H)</th>
                  <th>홈런 (HR)</th>
                  <th>타점 (RBI)</th>
                </tr>
              </thead>
              <tbody>
                {batterRankings.map((player) => (
                  <tr key={player.rank}>
                    <td className={`records__td-rank ${player.rank <= 3 ? 'records__td-rank--top' : ''}`}>
                      {player.rank}
                    </td>
                    <td className="records__td-player">{player.name}</td>
                    <td className="records__td-team">{player.team}</td>
                    <td>{player.games}</td>
                    <td className="records__td-highlight">{player.avg}</td>
                    <td>{player.h}</td>
                    <td>{player.hr}</td>
                    <td>{player.rbi}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className="records__table">
              <thead>
                <tr>
                  <th className="records__th-rank">순위</th>
                  <th className="records__th-player">선수명</th>
                  <th className="records__th-team">소속 구단</th>
                  <th>이닝 (IP)</th>
                  <th className="records__th-highlight">평균자책점 (ERA)</th>
                  <th>승</th>
                  <th>패</th>
                  <th>세이브 (SV)</th>
                  <th>탈삼진 (SO)</th>
                </tr>
              </thead>
              <tbody>
                {pitcherRankings.map((player) => (
                  <tr key={player.rank}>
                    <td className={`records__td-rank ${player.rank <= 3 ? 'records__td-rank--top' : ''}`}>
                      {player.rank}
                    </td>
                    <td className="records__td-player">{player.name}</td>
                    <td className="records__td-team">{player.team}</td>
                    <td>{player.ip}</td>
                    <td className="records__td-highlight">{player.era}</td>
                    <td>{player.wins}</td>
                    <td>{player.losses}</td>
                    <td>{player.sv}</td>
                    <td>{player.so}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
