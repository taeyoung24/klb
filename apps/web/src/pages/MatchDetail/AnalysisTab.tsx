import React from 'react';
import './AnalysisTab.css';

export interface MetricItem {
  label: string;
  away: string;
  home: string;
  awayWin: boolean;
}

export interface AnalysisTabProps {
  headToHead: string;
  metrics: MetricItem[];
  awayColor?: string;
  homeColor?: string;
}

export const AnalysisTab: React.FC<AnalysisTabProps> = ({
  headToHead,
  metrics,
  awayColor = '#888888',
  homeColor = '#cccccc',
}) => {
  return (
    <div className="match-detail__panel">
      <h3 className="match-detail__panel-title">팀 상대 전적 및 지표 비교</h3>
      <div className="match-detail__analysis-summary">
        <span className="match-detail__analysis-h2h">상대 전적: {headToHead}</span>
      </div>
      <div className="match-detail__metrics-list">
        {metrics.map((item, idx) => (
          <div key={idx} className="match-detail__metric-item">
            <div className="match-detail__metric-label-bar">
              <span className={`match-detail__metric-val ${item.awayWin ? 'match-detail__metric-val--win' : ''}`}>{item.away}</span>
              <span className="match-detail__metric-title">{item.label}</span>
              <span className={`match-detail__metric-val ${!item.awayWin ? 'match-detail__metric-val--win' : ''}`}>{item.home}</span>
            </div>
            <div className="match-detail__metric-track">
              <div
                className="match-detail__metric-fill match-detail__metric-fill--away"
                style={{ width: item.awayWin ? '55%' : '45%', backgroundColor: awayColor }}
              ></div>
              <div
                className="match-detail__metric-fill match-detail__metric-fill--home"
                style={{ width: !item.awayWin ? '55%' : '45%', backgroundColor: homeColor }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AnalysisTab;
