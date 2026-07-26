import React from 'react';
import './MatchSeries.css';

interface MatchSeriesProps {
  stageTitle: string;
  seriesLimit?: number;
  upperSeedTitle?: string;
  upperTeamName?: string;
  upperTeamImage?: string;
  upperTeamSymbol?: string;
  upperTeamColor?: string;
  upperScoreSeries?: number[];
  lowerSeedTitle?: string;
  lowerTeamName?: string;
  lowerTeamImage?: string;
  lowerTeamSymbol?: string;
  lowerTeamColor?: string;
  lowerScoreSeries?: number[];
}

const MatchSeries: React.FC<MatchSeriesProps> = ({
  stageTitle,
  seriesLimit,
  upperSeedTitle,
  upperTeamName = 'TBD',
  upperTeamImage,
  upperTeamSymbol,
  upperTeamColor,
  upperScoreSeries = [],
  lowerSeedTitle,
  lowerTeamName = 'TBD',
  lowerTeamImage,
  lowerTeamSymbol,
  lowerTeamColor,
  lowerScoreSeries = [],
}) => {
  // Determine the number of score columns
  const maxLen = Math.max(upperScoreSeries.length, lowerScoreSeries.length);
  const seriesCount = seriesLimit || (maxLen === 0 ? 3 : (maxLen % 2 === 0 ? maxLen + 1 : maxLen));

  // Calculate wins
  let upperWins = 0;
  let lowerWins = 0;
  for (let i = 0; i < maxLen; i++) {
    const uScore = upperScoreSeries[i];
    const lScore = lowerScoreSeries[i];
    if (uScore !== undefined && lScore !== undefined) {
      if (uScore > lScore) upperWins++;
      else if (lScore > uScore) lowerWins++;
    }
  }

  const winsNeeded = Math.floor(seriesCount / 2) + 1;
  const isSeriesFinished = upperWins >= winsNeeded || lowerWins >= winsNeeded;
  const upperIsWinner = upperWins >= winsNeeded;
  const lowerIsWinner = lowerWins >= winsNeeded;

  const renderScores = (scores: number[], opponentScores: number[], count: number) => {
    const result = [];
    for (let i = 0; i < count; i++) {
      const score = scores[i];
      const opponentScore = opponentScores[i];
      
      const isLoser = score !== undefined && opponentScore !== undefined && score < opponentScore;
      
      let scoreClasses = 'match-series__score-item';
      if (score === undefined) {
        scoreClasses += ' match-series__score-item--empty';
      } else if (isLoser) {
        scoreClasses += ' match-series__score-item--loser';
      }

      result.push(
        <span key={i} className={scoreClasses}>
          {score !== undefined ? score : '-'}
        </span>
      );
    }
    return result;
  };

  const getTeamClasses = (isUpper: boolean) => {
    if (!isSeriesFinished) return 'match-series__team-box match-series__team-box--default';
    
    const isWinner = isUpper ? upperIsWinner : lowerIsWinner;
    return `match-series__team-box match-series__team-box--default ${
      isWinner ? 'match-series__team-box--winner' : 'match-series__team-box--loser'
    }`;
  };

  const renderLogo = (imgSrc?: string, symbol?: string, color?: string) => {
    if (imgSrc) {
      return <img src={imgSrc} alt="" className="match-series__team-logo" />;
    }
    if (symbol) {
      return (
        <div 
          className="match-series__logo-placeholder" 
          style={{ 
            color: color || '#ffffff', 
            border: `1px solid ${color || 'rgba(255, 255, 255, 0.2)'}`,
          }}
        >
          {symbol}
        </div>
      );
    }
    return <div className="match-series__logo-placeholder" />;
  };

  return (
    <div className="match-series">
      <div className="match-series__stage-title">{stageTitle}</div>
      <div className="match-series__teams">
        {/* Upper Team */}
        <div className={getTeamClasses(true)}>
          <div className="match-series__team-info">
            <div className="match-series__logo-wrapper">
              {renderLogo(upperTeamImage, upperTeamSymbol, upperTeamColor)}
            </div>
            <div className="match-series__team-text">
              {upperSeedTitle && <div className="match-series__seed-title">{upperSeedTitle}</div>}
              <div className="match-series__team-name">{upperTeamName}</div>
            </div>
          </div>
          <div className="match-series__scores">
            {renderScores(upperScoreSeries, lowerScoreSeries, seriesCount)}
          </div>
        </div>

        {/* Lower Team */}
        <div className={getTeamClasses(false)}>
          <div className="match-series__team-info">
            <div className="match-series__logo-wrapper">
              {renderLogo(lowerTeamImage, lowerTeamSymbol, lowerTeamColor)}
            </div>
            <div className="match-series__team-text">
              {lowerSeedTitle && <div className="match-series__seed-title">{lowerSeedTitle}</div>}
              <div className="match-series__team-name">{lowerTeamName}</div>
            </div>
          </div>
          <div className="match-series__scores">
            {renderScores(lowerScoreSeries, upperScoreSeries, seriesCount)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchSeries;
