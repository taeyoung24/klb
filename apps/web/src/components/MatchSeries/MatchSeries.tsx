import React from 'react';
import styles from './MatchSeries.module.css';

interface MatchSeriesProps {
  stageTitle: string;
  upperSeedTitle?: string;
  upperTeamName?: string;
  upperTeamImage?: string;
  upperScoreSeries?: number[];
  lowerSeedTitle?: string;
  lowerTeamName?: string;
  lowerTeamImage?: string;
  lowerScoreSeries?: number[];
}

const MatchSeries: React.FC<MatchSeriesProps> = ({
  stageTitle,
  upperSeedTitle,
  upperTeamName = 'TBD',
  upperTeamImage,
  upperScoreSeries = [],
  lowerSeedTitle,
  lowerTeamName = 'TBD',
  lowerTeamImage,
  lowerScoreSeries = [],
}) => {
  // Determine the number of score columns (next odd number, default 3 if empty)
  const maxLen = Math.max(upperScoreSeries.length, lowerScoreSeries.length);
  let seriesCount = maxLen;
  if (seriesCount === 0) seriesCount = 3;
  else if (seriesCount % 2 === 0) seriesCount += 1;

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

  return (
    <div className={styles.container}>
      <div className={styles.stageTitle}>{stageTitle}</div>
      <div className={styles.teamsContainer}>
        {/* Upper Team */}
        <div className={getTeamClasses(true)}>
          <div className={styles.teamInfoWrapper}>
            <div className={styles.logoWrapper}>
              {upperTeamImage ? (
                <img src={upperTeamImage} alt="" className={styles.teamLogo} />
              ) : (
                <div className={styles.logoPlaceholder} />
              )}
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
              {lowerTeamImage ? (
                <img src={lowerTeamImage} alt="" className={styles.teamLogo} />
              ) : (
                <div className={styles.logoPlaceholder} />
              )}
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
