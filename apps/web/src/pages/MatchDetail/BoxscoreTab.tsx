import React from 'react';

export interface PitchRecords {
  winPitcher: string;
  losePitcher: string;
  savePitcher: string;
}

export interface BoxscoreTabProps {
  pitchRecords: PitchRecords;
}

export const BoxscoreTab: React.FC<BoxscoreTabProps> = ({ pitchRecords }) => {
  return (
    <div className="match-detail__panel">
      <div className="match-detail__pitcher-records">
        <div className="match-detail__pitcher-item">
          <span className="match-detail__pitcher-tag">승</span>
          <span className="match-detail__pitcher-name">{pitchRecords.winPitcher}</span>
        </div>
        <div className="match-detail__pitcher-item">
          <span className="match-detail__pitcher-tag">패</span>
          <span className="match-detail__pitcher-name">{pitchRecords.losePitcher}</span>
        </div>
        <div className="match-detail__pitcher-item">
          <span className="match-detail__pitcher-tag">세</span>
          <span className="match-detail__pitcher-name">{pitchRecords.savePitcher}</span>
        </div>
      </div>
    </div>
  );
};

export default BoxscoreTab;
