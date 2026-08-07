import React, { useMemo, useState } from 'react';
import type { Club } from '../../api/clubs';
import type { IngameInstructionLog } from '../../api/matches';
import type { Player } from '../../api/players';
import './BroadcastTab.css';

export interface BroadcastTabProps {
  matchLog?: IngameInstructionLog | string | null;
  awayClub?: Club | null;
  homeClub?: Club | null;
  playersMap?: Record<number, Player>;
}

const POSITION_KO_MAP: Record<string, string> = {
  PITCHER: '투수',
  CATCHER: '포수',
  FIRST_BASE: '1루수',
  SECOND_BASE: '2루수',
  THIRD_BASE: '3루수',
  SHORT_STOP: '유격수',
  LEFT_FIELD: '좌익수',
  CENTER_FIELD: '중견수',
  RIGHT_FIELD: '우익수',
  DESIGNATED_HITTER: '지명타자',
};

const getPlayerLabel = (playerId?: number, playersMap?: Record<number, Player>, fallbackRole: string = '선수') => {
  if (!playerId) return fallbackRole;
  const player = playersMap?.[playerId];
  if (!player) return `${fallbackRole} #${playerId}`;

  const posKo = POSITION_KO_MAP[player.position] || player.position || '';
  const numStr = player.uniform_number ? ` (No.${player.uniform_number})` : '';
  return posKo ? `${posKo} ${player.name}${numStr}` : `${player.name}${numStr}`;
};

interface PitchRecord {
  pitchNum: number;
  pitchType?: string;
  result?: string;
  balls: number;
  strikes: number;
  outs: number;
  text: string;
}

interface PlateAppearance {
  paIndex: number;
  batterId?: number;
  pitcherId?: number;
  summary: string;
  resultType: 'HIT' | 'HOMERUN' | 'OUT' | 'WALK' | 'STRIKE_OUT' | 'ETC';
  pitches: PitchRecord[];
  textLogs: { id: string; text: string; type?: 'normal' | 'highlight' | 'score' }[];
}

interface InningData {
  id: string;
  inning: number;
  isTop: boolean;
  shortLabel: string;
  fullLabel: string;
  awayScore: number;
  homeScore: number;
  plateAppearances: PlateAppearance[];
}

const PITCH_RESULT_MAP: Record<string, string> = {
  STRIKE_LOOKING: '루킹 스트라이크',
  STRIKE_SWINGING: '헛스윙 스트라이크',
  BALL: '볼',
  FOUL: '파울',
  IN_PLAY: '인플레이 (타격)',
  HIT: '안타',
  HOMERUN: '홈런',
  OUT: '아웃',
};

const BASE_RUN_RESULT_MAP: Record<string, string> = {
  SAFE: '세이프',
  TAG_OUT: '태그아웃',
  FORCE_OUT: '포스아웃',
  SCORE: '득점',
};

export const BroadcastTab: React.FC<BroadcastTabProps> = ({ matchLog, awayClub, homeClub, playersMap }) => {
  // 1. match_log_json 데이터 해석 및 이닝별 타석 데이터 그룹화
  const inningsData = useMemo<InningData[]>(() => {
    if (!matchLog) return [];

    let log: IngameInstructionLog | null = null;
    if (typeof matchLog === 'string') {
      try {
        log = JSON.parse(matchLog);
      } catch (e) {
        console.error('Failed to parse match_log_json string', e);
      }
    } else {
      log = matchLog;
    }

    if (!log || !Array.isArray(log.logged_events) || log.logged_events.length === 0) {
      return [];
    }

    const innings: InningData[] = [];
    let currentInning: InningData | null = null;
    let currentPA: PlateAppearance | null = null;

    let balls = 0;
    let strikes = 0;
    let outs = 0;
    let awayScore = 0;
    let homeScore = 0;
    let pitchCountInPA = 0;
    let paCounter = 1;

    for (const ev of log.logged_events) {
      const type = ev.event_type;

      if (type === 'GAME_STATE') {
        const stateType = ev.state_type;
        if (stateType === 'MATCH_START') {
          awayScore = 0;
          homeScore = 0;
        } else if (stateType === 'INNING_START' || stateType === 'INNING_CHANGE') {
          const innNum = ev.inning || 1;
          const isTop = ev.is_top !== undefined ? ev.is_top : true;
          const innId = `${innNum}_${isTop ? 'top' : 'bot'}`;
          
          if (ev.home_score !== undefined) homeScore = ev.home_score;
          if (ev.away_score !== undefined) awayScore = ev.away_score;

          balls = 0;
          strikes = 0;
          outs = 0;
          pitchCountInPA = 0;

          currentInning = {
            id: innId,
            inning: innNum,
            isTop,
            shortLabel: `${innNum}회${isTop ? '초' : '말'}`,
            fullLabel: `${innNum}회 ${isTop ? '초 (원정팀 공격)' : '말 (홈팀 공격)'}`,
            awayScore,
            homeScore,
            plateAppearances: [],
          };
          innings.push(currentInning);
          currentPA = null;
        } else if (stateType === 'SCORE_CHANGE') {
          if (ev.home_score !== undefined) homeScore = ev.home_score;
          if (ev.away_score !== undefined) awayScore = ev.away_score;
          if (currentInning) {
            currentInning.homeScore = homeScore;
            currentInning.awayScore = awayScore;
          }
        }
      } else if (type === 'BATTER_ENTER') {
        if (!currentInning) {
          // 기본 이닝 생성 Fallback
          currentInning = {
            id: '1_top',
            inning: 1,
            isTop: true,
            shortLabel: '1회초',
            fullLabel: '1회 초 (원정팀 공격)',
            awayScore: 0,
            homeScore: 0,
            plateAppearances: [],
          };
          innings.push(currentInning);
        }

        balls = 0;
        strikes = 0;
        pitchCountInPA = 0;

        currentPA = {
          paIndex: paCounter++,
          batterId: ev.batter_id,
          pitcherId: ev.pitcher_id,
          summary: '타석 진행 중',
          resultType: 'ETC',
          pitches: [],
          textLogs: [],
        };
        currentInning.plateAppearances.push(currentPA);
      } else if (type === 'PITCH') {
        if (currentPA) {
          pitchCountInPA++;
          const resultStr = PITCH_RESULT_MAP[ev.result] || ev.result || '투구';
          
          if (ev.result === 'BALL') balls++;
          else if (ev.result === 'STRIKE_LOOKING' || ev.result === 'STRIKE_SWINGING') strikes++;
          else if (ev.result === 'FOUL' && strikes < 2) strikes++;

          const pitchText = `${pitchCountInPA}구 ${resultStr} (B:${balls} S:${strikes} O:${outs})`;
          currentPA.pitches.push({
            pitchNum: pitchCountInPA,
            result: ev.result,
            balls,
            strikes,
            outs,
            text: pitchText,
          });

          currentPA.textLogs.push({
            id: `ev_${pitchCountInPA}_${Math.random()}`,
            text: pitchText,
            type: 'normal',
          });
        }
      } else if (type === 'BAT_CONTACT') {
        if (currentPA) {
          const contactType = ev.contact_type || '타격';
          const vel = ev.hit_velocity ? `${Math.round(ev.hit_velocity)}km/h` : '';
          const angle = ev.launch_angle ? `${Math.round(ev.launch_angle)}°` : '';
          const detail = [vel, angle].filter(Boolean).join(', ');
          const contactText = `타격! [${contactType}] ${detail ? `(${detail})` : ''}`;

          currentPA.textLogs.push({
            id: `contact_${Math.random()}`,
            text: contactText,
            type: 'highlight',
          });
        }
      } else if (type === 'BASE_RUN_RESULT') {
        if (currentPA) {
          const res = ev.result;
          const baseName = ev.target_base === 4 ? '홈' : `${ev.target_base}루`;
          let resText = `${baseName}에서 ${BASE_RUN_RESULT_MAP[res] || res}`;

          if (res === 'SCORE') {
            resText = `주자 ${baseName} 대성공! 득점!`;
            currentPA.textLogs.push({
              id: `score_${Math.random()}`,
              text: resText,
              type: 'score',
            });
            currentPA.resultType = 'HOMERUN';
          } else if (res === 'SAFE') {
            if (ev.target_base === 1) {
              currentPA.summary = '1루타 출루';
              if (currentPA.resultType !== 'HOMERUN') currentPA.resultType = 'HIT';
            } else if (ev.target_base === 2) {
              currentPA.summary = '2루타 출루';
              if (currentPA.resultType !== 'HOMERUN') currentPA.resultType = 'HIT';
            } else if (ev.target_base === 3) {
              currentPA.summary = '3루타 출루';
              if (currentPA.resultType !== 'HOMERUN') currentPA.resultType = 'HIT';
            }
            currentPA.textLogs.push({
              id: `run_${Math.random()}`,
              text: resText,
              type: 'highlight',
            });
          } else if (res === 'TAG_OUT' || res === 'FORCE_OUT') {
            outs++;
            if (currentPA.resultType === 'ETC') {
              currentPA.summary = `${baseName} ${BASE_RUN_RESULT_MAP[res]}`;
              currentPA.resultType = 'OUT';
            }
            currentPA.textLogs.push({
              id: `out_${Math.random()}`,
              text: resText,
              type: 'normal',
            });
          }
        }
      } else if (type === 'NOTICE') {
        if (currentPA && ev.message) {
          currentPA.textLogs.push({
            id: `notice_${Math.random()}`,
            text: ev.message,
            type: ev.message.includes('홈런') ? 'score' : ev.message.includes('안타') ? 'highlight' : 'normal',
          });

          if (ev.message.includes('홈런')) {
            currentPA.summary = '홈런!';
            currentPA.resultType = 'HOMERUN';
          } else if (ev.message.includes('삼진')) {
            currentPA.summary = '삼진 아웃';
            currentPA.resultType = 'STRIKE_OUT';
          } else if (ev.message.includes('볼넷') || ev.message.includes('사구')) {
            currentPA.summary = '볼넷/사구 출루';
            currentPA.resultType = 'WALK';
          } else if (ev.message.includes('아웃') || ev.message.includes('플라이') || ev.message.includes('땅볼')) {
            currentPA.summary = '아웃';
            currentPA.resultType = 'OUT';
          } else if (ev.message.includes('안타')) {
            currentPA.summary = '안타';
            currentPA.resultType = 'HIT';
          }
        }
      }
    }

    return innings;
  }, [matchLog, awayClub, homeClub]);

  // 2. 선택된 이닝 상태 관리
  const [selectedInningId, setSelectedInningId] = useState<string>('');

  // default 선택 이닝
  const activeInningId = selectedInningId || (inningsData.length > 0 ? inningsData[0].id : '');
  const activeInning = inningsData.find((inn) => inn.id === activeInningId) || inningsData[0];

  if (!matchLog || inningsData.length === 0) {
    return (
      <div className="match-broadcast">
        <div className="match-broadcast__empty-card" style={{ width: '100%' }}>
          <div className="match-broadcast__empty-title">중계 기록이 준비 중이거나 존재하지 않습니다.</div>
          <p className="match-broadcast__empty-desc">
            경기 진행 기록(Instruction Log)이 아직 수집되지 않았거나 예정된 경기입니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="match-broadcast">
      {/* 좌측 이닝 컨트롤러 (Sticky 적용) */}
      <aside className="match-broadcast__sidebar">
        <div className="match-broadcast__inning-list">
          {inningsData.map((inn, idx) => {
            const isActive = inn.id === activeInningId;
            const prevInn = idx > 0 ? inningsData[idx - 1] : null;
            const hasScoreChanged = prevInn
              ? prevInn.awayScore !== inn.awayScore || prevInn.homeScore !== inn.homeScore
              : inn.awayScore > 0 || inn.homeScore > 0;

            return (
              <button
                key={inn.id}
                className={`match-broadcast__inning-btn ${isActive ? 'match-broadcast__inning-btn--active' : ''}`}
                onClick={() => setSelectedInningId(inn.id)}
              >
                <span className="match-broadcast__inning-label">{inn.shortLabel}</span>
                <span className={`match-broadcast__inning-score ${hasScoreChanged ? 'match-broadcast__inning-score--changed' : ''}`}>
                  {inn.awayScore}:{inn.homeScore}
                </span>
              </button>
            );
          })}
        </div>
      </aside>

      {/* 우측 선택 이닝의 타석별 중계 로그 영역 */}
      <main className="match-broadcast__main">
        {activeInning && (
          <>
            <div className="match-broadcast__header-card">
              <div className="match-broadcast__header-info">
                <span className="match-broadcast__header-title">{activeInning.fullLabel}</span>
              </div>
              <div className="match-broadcast__header-score">
                {awayClub?.abbr_name || '원정'} {activeInning.awayScore} : {activeInning.homeScore} {homeClub?.abbr_name || '홈'}
              </div>
            </div>

            {activeInning.plateAppearances.length === 0 ? (
              <div className="match-broadcast__empty-card">
                <div className="match-broadcast__empty-title">해당 이닝 중계 기록이 없습니다.</div>
              </div>
            ) : (
              activeInning.plateAppearances.map((pa, idx) => {
                let badgeClass = 'match-broadcast__pa-badge--etc';
                if (pa.resultType === 'HOMERUN') badgeClass = 'match-broadcast__pa-badge--homerun';
                else if (pa.resultType === 'HIT') badgeClass = 'match-broadcast__pa-badge--hit';
                else if (pa.resultType === 'WALK') badgeClass = 'match-broadcast__pa-badge--walk';
                else if (pa.resultType === 'OUT' || pa.resultType === 'STRIKE_OUT') badgeClass = 'match-broadcast__pa-badge--out';

                return (
                  <div key={idx} className="match-broadcast__pa-card">
                    <div className="match-broadcast__pa-header">
                      <div className="match-broadcast__pa-title-group">
                        <span className="match-broadcast__pa-num">타석 #{pa.paIndex}</span>
                        <span className="match-broadcast__pa-player">
                          {getPlayerLabel(pa.batterId, playersMap, '타자')}
                        </span>
                        {pa.pitcherId && (
                          <span className="match-broadcast__pa-vs">
                            vs {getPlayerLabel(pa.pitcherId, playersMap, '투수')}
                          </span>
                        )}
                      </div>
                      <span className={`match-broadcast__pa-badge ${badgeClass}`}>
                        {pa.summary}
                      </span>
                    </div>

                    <div className="match-broadcast__pa-body">
                      {pa.textLogs.length > 0 ? (
                        <div className="match-broadcast__timeline">
                          {pa.textLogs.map((log) => {
                            let itemClass = '';
                            if (log.type === 'score') itemClass = 'match-broadcast__timeline-item--score';
                            else if (log.type === 'highlight') itemClass = 'match-broadcast__timeline-item--highlight';
                            return (
                              <div key={log.id} className={`match-broadcast__timeline-item ${itemClass}`}>
                                {log.text}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div style={{ color: '#718096', fontSize: '0.85rem' }}>상세 투구 로그 기록 없음</div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default BroadcastTab;
