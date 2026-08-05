import React from 'react';

export interface CheerItem {
  user: string;
  team: string;
  text: string;
}

export interface CheerTabProps {
  cheers: CheerItem[];
  awayTeamCode?: string;
  homeTeamCode?: string;
  awayColor?: string;
  homeColor?: string;
}

export const CheerTab: React.FC<CheerTabProps> = ({
  cheers,
  awayTeamCode = 'COM',
  homeTeamCode = 'ZEN',
  awayColor = '#888888',
  homeColor = '#cccccc',
}) => {
  return (
    <div className="match-detail__panel">
      <h3 className="match-detail__panel-title">팬 승부 예측 및 실시간 응원</h3>
      <div className="match-detail__prediction-box">
        <div className="match-detail__prediction-header">
          <span>승리 예측 비율</span>
          <span className="match-detail__prediction-ratio">42% vs 58%</span>
        </div>
        <div className="match-detail__prediction-bar">
          <div
            className="match-detail__prediction-fill match-detail__prediction-fill--away"
            style={{ width: '42%', backgroundColor: awayColor }}
          >
            {awayTeamCode} 42%
          </div>
          <div
            className="match-detail__prediction-fill match-detail__prediction-fill--home"
            style={{ width: '58%', backgroundColor: homeColor }}
          >
            {homeTeamCode} 58%
          </div>
        </div>
      </div>

      <div className="match-detail__cheer-list">
        {cheers.map((c, i) => (
          <div key={i} className="match-detail__cheer-item">
            <div className="match-detail__cheer-header">
              <span className="match-detail__cheer-user">{c.user}</span>
              <span className={`match-detail__cheer-tag match-detail__cheer-tag--${c.team.toLowerCase()}`}>{c.team}</span>
            </div>
            <p className="match-detail__cheer-text">{c.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CheerTab;
