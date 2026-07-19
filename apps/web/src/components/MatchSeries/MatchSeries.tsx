import React from 'react';
import styles from './MatchSeries.module.css';

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
      
      let scoreClasses = styles.scoreItem;
      if (score === undefined) {
        scoreClasses += ` ${styles.scoreEmpty}`;
      } else if (isLoser) {
        scoreClasses += ` ${styles.scoreLoser}`;
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
    if (!isSeriesFinished) return `${styles.teamBox} ${styles.defaultTeam}`;
    
    const isWinner = isUpper ? upperIsWinner : lowerIsWinner;
    return `${styles.teamBox} ${styles.defaultTeam} ${isWinner ? styles.winner : styles.loser}`;
  };

  const renderLogo = (imgSrc?: string, symbol?: string, color?: string) => {
    if (imgSrc) {
      return <img src={imgSrc} alt="" className={styles.teamLogo} />;
    }
    if (symbol) {
      return (
        <div 
          className={styles.logoPlaceholder} 
          style={{ 
            color: color || '#ffffff', 
            border: `1px solid ${color || 'rgba(255,255,255,0.2)'}`,
            background: 'rgba(0,0,0,0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--sans)',
            fontSize: '10px',
            fontWeight: 'bold',
          }}
        >
          {symbol}
        </div>
      );
    }
    return <div className={styles.logoPlaceholder} />;
  };

  return (
    <div className={styles.container}>
      <div className={styles.stageTitle}>{stageTitle}</div>
      <div className={styles.teamsContainer}>
        {/* Upper Team */}
        <div className={getTeamClasses(true)}>
          <div className={styles.teamInfoWrapper}>
            <div className={styles.logoWrapper}>
              {renderLogo(upperTeamImage, upperTeamSymbol, upperTeamColor)}
            </div>
            <div className={styles.teamText}>
              {upperSeedTitle && <div className={styles.seedTitle}>{upperSeedTitle}</div>}
              <div className={styles.teamName}>{upperTeamName}</div>
            </div>
          </div>
          <div className={styles.scoresWrapper}>
            {renderScores(upperScoreSeries, lowerScoreSeries, seriesCount)}
          </div>
        </div>

        {/* Lower Team */}
        <div className={getTeamClasses(false)}>
          <div className={styles.teamInfoWrapper}>
            <div className={styles.logoWrapper}>
              {renderLogo(lowerTeamImage, lowerTeamSymbol, lowerTeamColor)}
            </div>
            <div className={styles.teamText}>
              {lowerSeedTitle && <div className={styles.seedTitle}>{lowerSeedTitle}</div>}
              <div className={styles.teamName}>{lowerTeamName}</div>
            </div>
          </div>
          <div className={styles.scoresWrapper}>
            {renderScores(lowerScoreSeries, upperScoreSeries, seriesCount)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchSeries;
