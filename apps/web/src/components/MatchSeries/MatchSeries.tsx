import React from 'react';
import TeamLogo from '../TeamLogo/TeamLogo';
import './MatchSeries.css';

interface MatchSeriesProps {
  stageTitle: string;
  seriesLimit?: number;
  upperSeedTitle?: string;
  upperTeamName?: string;
  upperTeamCode?: string;
  upperTeamImage?: string;
  upperScoreSeries?: number[];
  lowerSeedTitle?: string;
  lowerTeamName?: string;
  lowerTeamCode?: string;
  lowerTeamImage?: string;
  lowerScoreSeries?: number[];
  matchIds?: (number | null | undefined)[];
}

const MatchSeries: React.FC<MatchSeriesProps> = ({
  stageTitle,
  seriesLimit,
  upperSeedTitle,
  upperTeamName = 'TBD',
  upperTeamCode,
  upperTeamImage,
  upperScoreSeries = [],
  lowerSeedTitle,
  lowerTeamName = 'TBD',
  lowerTeamCode,
  lowerTeamImage,
  lowerScoreSeries = [],
  matchIds = [],
}) => {
  const [hoveredGameIndex, setHoveredGameIndex] = React.useState<number | null>(null);

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

  const handleScoreClick = (index: number) => {
    const targetMatchId = matchIds[index];
    if (targetMatchId) {
      window.location.hash = `#match-detail?id=${targetMatchId}`;
    } else {
      window.location.hash = '#match-detail';
    }
  };

  const renderScores = (scores: number[], opponentScores: number[], count: number) => {
    const result = [];
    for (let i = 0; i < count; i++) {
      const score = scores[i];
      const opponentScore = opponentScores[i];

      const isLoser = score !== undefined && opponentScore !== undefined && score < opponentScore;
      const hasMatch = matchIds[i] !== undefined && matchIds[i] !== null;
      const isHovered = hoveredGameIndex === i && hasMatch;

      let scoreClasses = 'match-series__score-item';
      if (score === undefined) {
        scoreClasses += ' match-series__score-item--empty';
      } else if (isLoser) {
        scoreClasses += ' match-series__score-item--loser';
      }

      if (hasMatch) {
        scoreClasses += ' match-series__score-item--clickable';
      }

      if (isHovered) {
        scoreClasses += ' match-series__score-item--hovered';
      }

      result.push(
        <span
          key={i}
          className={scoreClasses}
          onMouseEnter={() => hasMatch && setHoveredGameIndex(i)}
          onMouseLeave={() => hasMatch && setHoveredGameIndex(null)}
          onClick={() => hasMatch && handleScoreClick(i)}
        >
          {score !== undefined && matchIds[i] !== null ? score : '-'}
        </span>
      );
    }
    return result;
  };

  const getTeamClasses = (isUpper: boolean) => {
    if (!isSeriesFinished) return 'match-series__team-box match-series__team-box--default';

    const isWinner = isUpper ? upperIsWinner : lowerIsWinner;
    return `match-series__team-box match-series__team-box--default ${isWinner ? 'match-series__team-box--winner' : 'match-series__team-box--loser'
      }`;
  };

  return (
    <div className="match-series">
      <div className="match-series__stage-title">{stageTitle}</div>
      <div className="match-series__teams">
        {/* Upper Team */}
        <div className={getTeamClasses(true)}>
          <div className="match-series__team-info">
            <div className="match-series__logo-wrapper">
              <TeamLogo
                teamCode={upperTeamCode}
                teamName={upperTeamName}
                logoUrl={upperTeamImage}
                size={22}
              />
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
              <TeamLogo
                teamCode={lowerTeamCode}
                teamName={lowerTeamName}
                logoUrl={lowerTeamImage}
                size={22}
              />
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
