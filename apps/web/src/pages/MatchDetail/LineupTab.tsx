import React from 'react';

export interface PlayerLineup {
  pos: string;
  name: string;
  avg: string;
  stat: string;
}

export interface LineupTabProps {
  awayTeamName: string;
  homeTeamName: string;
  awayLineup: PlayerLineup[];
  homeLineup: PlayerLineup[];
  awayColor?: string;
  homeColor?: string;
}

export const LineupTab: React.FC<LineupTabProps> = ({
  awayTeamName,
  homeTeamName,
  awayLineup,
  homeLineup,
  awayColor = '#888888',
  homeColor = '#cccccc',
}) => {
  return (
    <div className="match-detail__panel">
      <h3 className="match-detail__panel-title">양 팀 선발 타순 및 출전 선수</h3>
      <div className="match-detail__lineup-columns">
        <div className="match-detail__lineup-side">
          <h4 className="match-detail__lineup-sub-title" style={{ color: awayColor }}>
            {awayTeamName} (어웨이)
          </h4>
          <ul className="match-detail__lineup-list">
            {awayLineup.map((p, i) => (
              <li key={i} className="match-detail__lineup-item">
                <span className="match-detail__lineup-pos">{p.pos}</span>
                <span className="match-detail__lineup-name">{p.name}</span>
                <span className="match-detail__lineup-stat">{p.stat}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="match-detail__lineup-side">
          <h4 className="match-detail__lineup-sub-title" style={{ color: homeColor }}>
            {homeTeamName} (홈)
          </h4>
          <ul className="match-detail__lineup-list">
            {homeLineup.map((p, i) => (
              <li key={i} className="match-detail__lineup-item">
                <span className="match-detail__lineup-pos">{p.pos}</span>
                <span className="match-detail__lineup-name">{p.name}</span>
                <span className="match-detail__lineup-stat">{p.stat}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default LineupTab;
