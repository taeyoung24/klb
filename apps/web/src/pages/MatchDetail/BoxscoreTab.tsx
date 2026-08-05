import React from 'react';

export interface PitchRecords {
  winPitcher: string;
  losePitcher: string;
  savePitcher: string;
  keyHomeRun: string;
}

export interface BoxscoreTabProps {
  pitchRecords: PitchRecords;
}

export const BoxscoreTab: React.FC<BoxscoreTabProps> = ({ pitchRecords }) => {
  return (
    <div className="match-detail__panel">
      <h3 className="match-detail__panel-title">투타 주요 경기 기록</h3>
      <div className="match-detail__records-grid">
        <div className="match-detail__record-box">
          <span className="match-detail__record-label">승리투수</span>
          <span className="match-detail__record-val">{pitchRecords.winPitcher}</span>
        </div>
        <div className="match-detail__record-box">
          <span className="match-detail__record-label">패전투수</span>
          <span className="match-detail__record-val">{pitchRecords.losePitcher}</span>
        </div>
        <div className="match-detail__record-box">
          <span className="match-detail__record-label">세이브</span>
          <span className="match-detail__record-val">{pitchRecords.savePitcher}</span>
        </div>
        <div className="match-detail__record-box">
          <span className="match-detail__record-label">주요 홈런</span>
          <span className="match-detail__record-val">{pitchRecords.keyHomeRun}</span>
        </div>
      </div>
    </div>
  );
};

export default BoxscoreTab;
