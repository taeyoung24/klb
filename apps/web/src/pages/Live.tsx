import { AWAY_TEAM_COLOR, LEAGUE_COLORS } from '../constants/leagues';
import { FaTv, FaMapMarkerAlt } from 'react-icons/fa';
import './Live.css';

interface LiveMatch {
  id: number;
  league: string;
  inning: string;
  stadium: string;
  awayTeam: {
    name: string;
    fullName: string;
    score: number;
    color: string;
    symbol: string;
  };
  homeTeam: {
    name: string;
    fullName: string;
    score: number;
    color: string;
    symbol: string;
  };
}

export default function Live() {
  const liveMatches: LiveMatch[] = [
    {
      id: 1,
      league: '아젤리아 리그',
      inning: 'LIVE 6회초',
      stadium: '서울 잠실야구장',
      awayTeam: {
        name: '코멧스',
        fullName: '서울 코멧스',
        score: 5,
        color: AWAY_TEAM_COLOR.primary,
        symbol: 'C',
      },
      homeTeam: {
        name: '제니스',
        fullName: '부산 제니스',
        score: 3,
        color: LEAGUE_COLORS.AL.primary,
        symbol: 'Z',
      },
    },
    {
      id: 2,
      league: '카멜리아 리그',
      inning: 'LIVE 4회말',
      stadium: '창원 파크',
      awayTeam: {
        name: '드래곤스',
        fullName: '창원 드래곤스',
        score: 2,
        color: AWAY_TEAM_COLOR.primary,
        symbol: 'D',
      },
      homeTeam: {
        name: '나이츠',
        fullName: '수원 나이츠',
        score: 4,
        color: LEAGUE_COLORS.CL.primary,
        symbol: 'K',
      },
    },
    {
      id: 3,
      league: '젠티아나 리그',
      inning: 'LIVE 8회초',
      stadium: '인천 문학야구장',
      awayTeam: {
        name: '베어스',
        fullName: '인천 베어스',
        score: 1,
        color: AWAY_TEAM_COLOR.primary,
        symbol: 'B',
      },
      homeTeam: {
        name: '스파크',
        fullName: '대구 스파크',
        score: 7,
        color: LEAGUE_COLORS.GL.primary,
        symbol: 'S',
      },
    },
  ];

  return (
    <div className="live">
      <div className="live__container">
        {/* 라이브 매치 심플 카드 리스트 */}
        <div className="live__grid">
          {liveMatches.map((match) => (
            <div key={match.id} className="live__card">
              <div className="live__card-header">
                <span className="live__league-tag">{match.league}</span>
                <span className="live__inning-tag">{match.inning}</span>
              </div>

              <div className="live__match-hero">
                {/* 어웨이 팀 */}
                <div className="live__team live__team--away">
                  <div className="live__logo-circle" style={{ color: match.awayTeam.color }}>
                    {match.awayTeam.symbol}
                  </div>
                  <span className="live__team-name">{match.awayTeam.fullName}</span>
                </div>

                {/* 중앙 스코어 */}
                <div className="live__score-box">
                  <span className="live__score">{match.awayTeam.score}</span>
                  <span className="live__divider">:</span>
                  <span className="live__score">{match.homeTeam.score}</span>
                </div>

                {/* 홈 팀 */}
                <div className="live__team live__team--home">
                  <span className="live__team-name">{match.homeTeam.fullName}</span>
                  <div className="live__logo-circle" style={{ color: match.homeTeam.color }}>
                    {match.homeTeam.symbol}
                  </div>
                </div>
              </div>

              <div className="live__card-footer">
                <span className="live__stadium">
                  <FaMapMarkerAlt className="live__footer-icon" /> {match.stadium}
                </span>
                <a href="#match-detail" className="live__watch-btn">
                  <FaTv className="live__watch-icon" />
                  중계 보기
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
