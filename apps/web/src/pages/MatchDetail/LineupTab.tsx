import React from 'react';
import TeamLogo from '../../components/TeamLogo/TeamLogo';

export interface PlayerLineup {
  orderLabel: string;
  posCode: string;
  name: string;
}

export interface LineupTabProps {
  awayTeamName: string;
  homeTeamName: string;
  awayTeamCode?: string;
  homeTeamCode?: string;
  awayLineup: PlayerLineup[];
  homeLineup: PlayerLineup[];
}

export const LineupTab: React.FC<LineupTabProps> = ({
  awayTeamName,
  homeTeamName,
  awayTeamCode,
  homeTeamCode,
  awayLineup,
  homeLineup,
}) => {
  return (
    <div className="match-detail__panel match-detail__panel--flat">
      <div className="match-detail__lineup-columns">
        <div className="match-detail__lineup-side">
          <h4 className="match-detail__lineup-sub-title">
            <TeamLogo teamCode={awayTeamCode} teamName={awayTeamName} size={22} />
            <span>{awayTeamName}</span>
          </h4>
          <ul className="match-detail__lineup-list">
            {awayLineup.map((p, i) => (
              <li key={i} className="match-detail__lineup-item">
                <span className="match-detail__lineup-order">{p.orderLabel}</span>
                <span className="match-detail__lineup-player-info">
                  <span className="match-detail__lineup-pos-code">{p.posCode}</span>
                  <span className="match-detail__lineup-name">{p.name}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="match-detail__lineup-side">
          <h4 className="match-detail__lineup-sub-title">
            <TeamLogo teamCode={homeTeamCode} teamName={homeTeamName} size={22} />
            <span>{homeTeamName}</span>
          </h4>
          <ul className="match-detail__lineup-list">
            {homeLineup.map((p, i) => (
              <li key={i} className="match-detail__lineup-item">
                <span className="match-detail__lineup-order">{p.orderLabel}</span>
                <span className="match-detail__lineup-player-info">
                  <span className="match-detail__lineup-pos-code">{p.posCode}</span>
                  <span className="match-detail__lineup-name">{p.name}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default LineupTab;
