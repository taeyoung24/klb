import React from 'react';
import TeamLogo from '../../components/TeamLogo/TeamLogo';
import './AnalysisTab.css';

import type { HeadToHeadDetailData, MetricItemData, PitcherComparisonData } from '../../api/matches';

export interface MetricItem {
  label: string;
  away: string;
  home: string;
  awayWin?: boolean;
  away_win?: boolean;
}

export interface PitcherMetric {
  label: string;
  away: string;
  home: string;
  awayWin?: boolean;
  away_win?: boolean;
}

export interface AnalysisTabProps {
  awayTeamName?: string;
  homeTeamName?: string;
  awayTeamCode?: string;
  homeTeamCode?: string;
  awayTeamRecord?: string;
  homeTeamRecord?: string;
  headToHead?: string;
  headToHeadDetail?: {
    awayWins?: number;
    homeWins?: number;
    away_wins?: number;
    home_wins?: number;
    draws: number;
    recentResults?: string;
    recent_results?: string;
  } | HeadToHeadDetailData;
  metrics?: (MetricItem | MetricItemData)[];
  pitcherComparison?: {
    awayPitcher?: {
      name: string;
      hand: string;
      era: string;
      record: string;
    };
    homePitcher?: {
      name: string;
      hand: string;
      era: string;
      record: string;
    };
    away_pitcher?: {
      name: string;
      hand: string;
      era: string;
      record: string;
    };
    home_pitcher?: {
      name: string;
      hand: string;
      era: string;
      record: string;
    };
    metrics: (PitcherMetric | MetricItemData)[];
  } | PitcherComparisonData;
}

const parseNumericValue = (valStr: string): number => {
  if (!valStr) return 0;
  const cleaned = valStr.replace(/[^0-9.]/g, '');
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
};

const isLowerBetterMetric = (label: string): boolean => {
  const lowerCase = label.toLowerCase();
  return lowerCase.includes('era') || lowerCase.includes('whip') || lowerCase.includes('피안타율') || lowerCase.includes('실책');
};

/**
 * 편차 비선형 증폭 후 합(Total Sum)으로 재정규화하는 연산
 * 클램핑(Math.max/min) 없이 0~100% 사이에서 자연스럽고 매끄럽게 연속(Smooth Continuous Scale)
 */
const calculateAmplifiedPercent = (
  valStrA: string,
  valStrB: string,
  label: string = ''
): { awayPct: string; homePct: string } => {
  const rawA = parseNumericValue(valStrA);
  const rawB = parseNumericValue(valStrB);

  if (rawA <= 0 && rawB <= 0) return { awayPct: '50%', homePct: '50%' };
  if (rawA <= 0) return { awayPct: '0%', homePct: '100%' };
  if (rawB <= 0) return { awayPct: '100%', homePct: '0%' };

  const isLowerBetter = isLowerBetterMetric(label);

  // ERA, WHIP, 피안타율 등 숫자가 작을수록 우세한 지표는 역수 취함
  const valA = isLowerBetter ? 1 / rawA : rawA;
  const valB = isLowerBetter ? 1 / rawB : rawB;

  // 비선형 편차 증폭 계수 (p = 5.0)
  const POWER = 5.0;
  const ampA = Math.pow(valA, POWER);
  const ampB = Math.pow(valB, POWER);

  const ampSum = ampA + ampB;
  if (ampSum === 0) return { awayPct: '50%', homePct: '50%' };

  // 증폭값들의 합(ampSum)을 전체폭(100%)으로 하는 매끄러운 자연 연속 정규화
  const pctA = Math.round((ampA / ampSum) * 100);
  const pctB = 100 - pctA;

  return { awayPct: `${pctA}%`, homePct: `${pctB}%` };
};

export const AnalysisTab: React.FC<AnalysisTabProps> = ({
  awayTeamName = '원정팀',
  homeTeamName = '홈팀',
  awayTeamCode,
  homeTeamCode,
  awayTeamRecord,
  homeTeamRecord,
  headToHeadDetail,
  metrics,
  pitcherComparison,
}) => {
  const awayWins = (headToHeadDetail as any)?.awayWins ?? (headToHeadDetail as any)?.away_wins ?? 0;
  const homeWins = (headToHeadDetail as any)?.homeWins ?? (headToHeadDetail as any)?.home_wins ?? 0;

  const awayPitcher = (pitcherComparison as any)?.awayPitcher || (pitcherComparison as any)?.away_pitcher || { name: '선발투수', hand: '우투우타', era: '3.50', record: '0승 0패' };
  const homePitcher = (pitcherComparison as any)?.homePitcher || (pitcherComparison as any)?.home_pitcher || { name: '선발투수', hand: '우투우타', era: '3.50', record: '0승 0패' };

  // 상대 전적 지표를 지표 비교 최상단에 통합
  const h2hMetric = {
    label: '시즌 상대전적',
    away: `${awayWins}승`,
    home: `${homeWins}승`,
    awayWin: awayWins >= homeWins,
  };

  const allTeamMetrics = [h2hMetric, ...(metrics || [])];

  return (
    <div className="analysis-tab">
      {/* 1. 팀 지표 및 상대전적 통합 비교 */}
      <section className="analysis-tab__section">
        {/* 상단 팀 로고 - VS - 팀 로고 (가운데 집중 대칭 헤더) */}
        <div className="analysis-tab__vs-header">
          {/* 어웨이 팀: 1열(팀명/승무패) + 2열(구단 로고) */}
          <div className="analysis-tab__vs-side analysis-tab__vs-side--away">
            <div className="analysis-tab__vs-text-col analysis-tab__vs-text-col--away">
              <span className="analysis-tab__vs-team-name">{awayTeamName}</span>
              {awayTeamRecord && (
                <span className="analysis-tab__vs-team-sub">{awayTeamRecord}</span>
              )}
            </div>
            <TeamLogo teamCode={awayTeamCode} teamName={awayTeamName} size={44} />
          </div>

          <div className="analysis-tab__vs-badge">VS</div>

          {/* 홈 팀: 1열(구단 로고) + 2열(팀명/승무패) */}
          <div className="analysis-tab__vs-side analysis-tab__vs-side--home">
            <TeamLogo teamCode={homeTeamCode} teamName={homeTeamName} size={44} />
            <div className="analysis-tab__vs-text-col analysis-tab__vs-text-col--home">
              <span className="analysis-tab__vs-team-name">{homeTeamName}</span>
              {homeTeamRecord && (
                <span className="analysis-tab__vs-team-sub">{homeTeamRecord}</span>
              )}
            </div>
          </div>
        </div>

        {/* 하단 지표 바 리스트 */}
        <div className="analysis-tab__metrics-group">
          {allTeamMetrics.map((item: any, idx) => {
            const isAwayAdvantage = item.awayWin !== undefined ? item.awayWin : item.away_win;
            const { awayPct, homePct } = calculateAmplifiedPercent(item.away, item.home, item.label);
            return (
              <div key={idx} className="analysis-tab__symmetric-row">
                {/* 어웨이 바 */}
                <div className="analysis-tab__bar-wrapper analysis-tab__bar-wrapper--away">
                  <div
                    className={`analysis-tab__bar-fill ${isAwayAdvantage ? 'analysis-tab__bar-fill--advantage' : ''}`}
                    style={{ width: awayPct }}
                  />
                </div>

                {/* 중앙 수치 & 라벨 모음 */}
                <div className="analysis-tab__center-group">
                  <span className={`analysis-tab__metric-val ${isAwayAdvantage ? 'analysis-tab__metric-val--advantage' : ''}`}>
                    {item.away}
                  </span>
                  <span className="analysis-tab__metric-label">{item.label}</span>
                  <span className={`analysis-tab__metric-val ${!isAwayAdvantage ? 'analysis-tab__metric-val--advantage' : ''}`}>
                    {item.home}
                  </span>
                </div>

                {/* 홈 바 */}
                <div className="analysis-tab__bar-wrapper analysis-tab__bar-wrapper--home">
                  <div
                    className={`analysis-tab__bar-fill ${!isAwayAdvantage ? 'analysis-tab__bar-fill--advantage' : ''}`}
                    style={{ width: homePct }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 2. 선발투수 비교 */}
      <section className="analysis-tab__section">
        <div className="analysis-tab__pitcher-box">
          <div className="analysis-tab__pitcher-header">
            <div className="analysis-tab__pitcher-profile analysis-tab__pitcher-profile--away">
              <div className="analysis-tab__pitcher-name-row">
                <TeamLogo teamCode={awayTeamCode} teamName={awayTeamName} size={20} />
                <span className="analysis-tab__pitcher-name">{awayPitcher.name}</span>
              </div>
              <span className="analysis-tab__pitcher-sub">{awayPitcher.hand} · {awayPitcher.record}</span>
            </div>
            <div className="analysis-tab__pitcher-vs">VS</div>
            <div className="analysis-tab__pitcher-profile analysis-tab__pitcher-profile--home">
              <div className="analysis-tab__pitcher-name-row">
                <span className="analysis-tab__pitcher-name">{homePitcher.name}</span>
                <TeamLogo teamCode={homeTeamCode} teamName={homeTeamName} size={20} />
              </div>
              <span className="analysis-tab__pitcher-sub">{homePitcher.hand} · {homePitcher.record}</span>
            </div>
          </div>

          <div className="analysis-tab__metrics-group">
            {((pitcherComparison as any)?.metrics || []).map((pm: any, idx: number) => {
              const isAwayAdvantage = pm.awayWin !== undefined ? pm.awayWin : pm.away_win;
              const { awayPct, homePct } = calculateAmplifiedPercent(pm.away, pm.home, pm.label);
              return (
                <div key={idx} className="analysis-tab__symmetric-row">
                  {/* 어웨이 바 */}
                  <div className="analysis-tab__bar-wrapper analysis-tab__bar-wrapper--away">
                    <div
                      className={`analysis-tab__bar-fill ${isAwayAdvantage ? 'analysis-tab__bar-fill--advantage' : ''}`}
                      style={{ width: awayPct }}
                    />
                  </div>

                  {/* 중앙 수치 & 라벨 모음 */}
                  <div className="analysis-tab__center-group">
                    <span className={`analysis-tab__metric-val ${isAwayAdvantage ? 'analysis-tab__metric-val--advantage' : ''}`}>
                      {pm.away}
                    </span>
                    <span className="analysis-tab__metric-label">{pm.label}</span>
                    <span className={`analysis-tab__metric-val ${!isAwayAdvantage ? 'analysis-tab__metric-val--advantage' : ''}`}>
                      {pm.home}
                    </span>
                  </div>

                  {/* 홈 바 */}
                  <div className="analysis-tab__bar-wrapper analysis-tab__bar-wrapper--home">
                    <div
                      className={`analysis-tab__bar-fill ${!isAwayAdvantage ? 'analysis-tab__bar-fill--advantage' : ''}`}
                      style={{ width: homePct }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
};

export default AnalysisTab;
