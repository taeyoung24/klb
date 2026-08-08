import React, { useMemo, useState } from 'react';
import type { Club } from '../../api/clubs';
import type { IngameInstructionLog, MatchLineupResponse } from '../../api/matches';
import type { Player } from '../../api/players';
import './BroadcastTab.css';

export interface BroadcastTabProps {
  matchLog?: IngameInstructionLog | string | null;
  awayClub?: Club | null;
  homeClub?: Club | null;
  playersMap?: Record<number, Player>;
  lineupData?: MatchLineupResponse | null;
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

const getPlayerLabel = (
  playerId?: number | string,
  playersMap?: Record<number, Player>,
  fallbackRole: string = '선수',
  batterOrderMap?: Record<number, number>
) => {
  if (!playerId) return fallbackRole;
  const pId = Number(playerId);
  const player = playersMap?.[pId] || (playersMap ? Object.values(playersMap).find((p) => p.id === pId) : undefined);
  if (!player) return `${fallbackRole} #${pId}`;

  const posKo = POSITION_KO_MAP[player.position] || player.position || '';
  const order = batterOrderMap?.[pId];
  const orderPrefix = order ? `${order}번 ` : '';

  return posKo ? `${orderPrefix}${posKo} ${player.name}` : `${orderPrefix}${player.name}`;
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

export interface TextLogItem {
  id: string;
  pitchNum?: number;
  labelTag?: string;
  resultText: string;
  countText?: string;
  type?: 'normal' | 'highlight' | 'score';
}

interface PlateAppearance {
  paIndex: number;
  batterId?: number;
  pitcherId?: number;
  summary: string;
  resultType: 'HIT' | 'HOMERUN' | 'OUT' | 'WALK' | 'STRIKE_OUT' | 'ETC';
  runsScored?: number;
  awayScore?: number;
  homeScore?: number;
  pitches: PitchRecord[];
  textLogs: TextLogItem[];
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
  STRIKE: '스트라이크',
  STRIKE_LOOKING: '루킹 스트라이크',
  STRIKE_SWINGING: '헛스윙 스트라이크',
  BALL: '볼',
  FOUL: '파울',
  HIT_BY_PITCH: '몸에 맞은 공(사구)',
  WILD_PITCH: '폭투',
  INTENTIONAL_WALK: '고의사구',
  IN_PLAY: '인플레이 (타격)',
  HIT: '안타',
  HOMERUN: '홈런',
  OUT: '아웃',
};

const CONTACT_TYPE_MAP: Record<string, string> = {
  CONTACT_IN_PLAY: '인플레이 타구',
  FOUL: '파울 타구',
  BUNT: '번트 타구',
};

const PITCH_TYPE_MAP: Record<string, string> = {
  FASTBALL: '직구',
  SLIDER: '슬라이더',
  CURVEBALL: '커브',
  CHANGEUP: '체인지업',
  SINKER: '싱커',
  SPLITTER: '스플리터',
};

const FIELDING_ACTION_MAP: Record<string, string> = {
  CATCH: '포구 성공',
  ERROR: '수비 실책 (에러)',
  DROP: '타구 낙구 (포구 실패)',
};

const BASE_RUN_REASON_MAP: Record<string, string> = {
  STEAL: '도루 시도',
  HIT_RUN: '인플레이 진루',
  TAG_UP: '태그업 진루',
};

const BASE_RUN_RESULT_MAP: Record<string, string> = {
  SAFE: '세이프',
  OUT: '아웃',
  TAG_OUT: '태그아웃',
  FORCE_OUT: '포스아웃',
  SCORE: '득점',
};


export const BroadcastTab: React.FC<BroadcastTabProps> = ({ matchLog, awayClub, homeClub, playersMap, lineupData }) => {
  // 1. 라인업 데이터 및 이닝 이벤트 기반 타자별 타순(1번~9번) 맵 생성
  const batterOrderMap = useMemo<Record<number, number>>(() => {
    const map: Record<number, number> = {};

    // 선발 라인업 정보 반영
    if (lineupData) {
      const allLineups = [...(lineupData.away_lineup || []), ...(lineupData.home_lineup || [])];
      for (const item of allLineups) {
        if (item.player_id && item.batting_order) {
          map[item.player_id] = item.batting_order;
        }
      }
    }

    // 인스트럭션 로그 이벤트를 순회하며 미등록 타자 타순 동적 보정 (1번~9번 순환)
    if (matchLog) {
      let log: IngameInstructionLog | null = null;
      if (typeof matchLog === 'string') {
        try {
          log = JSON.parse(matchLog);
        } catch (e) { }
      } else {
        log = matchLog;
      }

      if (log && Array.isArray(log.logged_events)) {
        let awayOrderCounter = 1;
        let homeOrderCounter = 1;
        let isTop = true;

        for (const ev of log.logged_events) {
          if (ev.event_type === 'GAME_STATE') {
            if (ev.is_top !== undefined) isTop = ev.is_top;
          } else if (ev.event_type === 'BATTER_ENTER' && ev.batter_id) {
            const bId = ev.batter_id;
            if (!map[bId]) {
              if (isTop) {
                map[bId] = awayOrderCounter;
                awayOrderCounter = (awayOrderCounter % 9) + 1;
              } else {
                map[bId] = homeOrderCounter;
                homeOrderCounter = (homeOrderCounter % 9) + 1;
              }
            }
          }
        }
      }
    }

    return map;
  }, [lineupData, matchLog]);

  // 2. match_log_json 데이터 해석 및 이닝별 타석 데이터 그룹화
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
    let currentPitchType: string | null = null;
    let currentPitchVel: number | null = null;
    const runnerStartBaseMap: Record<number, number> = {};




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

          if (ev.home_score !== undefined && ev.home_score > homeScore) homeScore = ev.home_score;
          if (ev.away_score !== undefined && ev.away_score > awayScore) awayScore = ev.away_score;

          // 이전 이닝(직전 반이닝)의 종료 시점 최종 점수를 동기화
          if (currentInning) {
            currentInning.awayScore = awayScore;
            currentInning.homeScore = homeScore;
          }

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
        } else if (stateType === 'SCORE_CHANGE' || stateType === 'MATCH_END') {
          if (ev.home_score !== undefined && ev.home_score > homeScore) homeScore = ev.home_score;
          if (ev.away_score !== undefined && ev.away_score > awayScore) awayScore = ev.away_score;
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
          summary: '타석 진행',
          resultType: 'ETC',
          runsScored: 0,
          pitches: [],
          textLogs: [],
        };
        currentInning.plateAppearances.push(currentPA);
      } else if (type === 'PITCH_START') {
        if (ev.pitch_type) {
          currentPitchType = ev.pitch_type;
        }
        if (ev.pitch_velocity) {
          currentPitchVel = ev.pitch_velocity;
        }
      } else if (type === 'PITCH') {
        if (currentPA) {
          pitchCountInPA++;
          const resultStr = PITCH_RESULT_MAP[ev.result] || ev.result || '투구';
          const pitchName = currentPitchType ? (PITCH_TYPE_MAP[currentPitchType] || currentPitchType) : '';
          const velVal = ev.pitch_velocity || currentPitchVel;
          const velStr = velVal ? `${Math.round(velVal)}km/h` : '';

          let pitchDetailStr = '';
          if (pitchName && velStr) pitchDetailStr = ` (${pitchName} ${velStr})`;
          else if (pitchName) pitchDetailStr = ` (${pitchName})`;
          else if (velStr) pitchDetailStr = ` (${velStr})`;

          const resultWithPitch = `${resultStr}${pitchDetailStr}`;

          if (ev.result === 'BALL') balls++;
          else if (ev.result === 'STRIKE' || ev.result === 'STRIKE_LOOKING' || ev.result === 'STRIKE_SWINGING') strikes++;
          else if (ev.result === 'FOUL' && strikes < 2) strikes++;

          // 3스트라이크 삼진 아웃 처리
          if (strikes >= 3) {
            outs++;
            currentPA.summary = '삼진 아웃';
            currentPA.resultType = 'STRIKE_OUT';
          }

          const countStr = `${balls}-${strikes}`;
          const pitchText = `${pitchCountInPA}구 ${resultWithPitch} (${countStr})`;

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
            pitchNum: pitchCountInPA,
            resultText: resultWithPitch,
            countText: countStr,
            type: 'normal',
          });
          currentPitchType = null;
          currentPitchVel = null;
        }
      }


 else if (type === 'BAT_CONTACT') {
        if (currentPA) {
          const contactRaw = ev.contact_type || 'CONTACT_IN_PLAY';
          const contactTypeKo = CONTACT_TYPE_MAP[contactRaw] || contactRaw;
          if (contactRaw === 'FOUL' && strikes < 2) {
            strikes++;
          }

          const vel = ev.hit_velocity ? `${Math.round(ev.hit_velocity)}km/h` : '';
          const angle = ev.launch_angle ? `${Math.round(ev.launch_angle)}°` : '';
          const detail = [vel, angle].filter(Boolean).join(', ');
          const contactText = `[${contactTypeKo}] ${detail ? `(${detail})` : ''}`;
          currentPA.textLogs.push({
            id: `contact_${Math.random()}`,
            labelTag: '타격',
            resultText: contactText,
            type: 'highlight',
          });
        }
      } else if (type === 'FIELDING_ACTION') {
        if (currentPA) {
          const actionType = ev.action_type;
          const actionKo = FIELDING_ACTION_MAP[actionType] || actionType;
          if (actionType === 'CATCH') {
            outs++;
            currentPA.summary = '플라이 아웃';
            currentPA.resultType = 'OUT';
            currentPA.textLogs.push({
              id: `field_${Math.random()}`,
              resultText: '야수 뜬공 포구 (플라이 아웃)',
              type: 'normal',
            });
          } else if (actionType === 'ERROR' || actionType === 'DROP') {
            currentPA.summary = '야수 실책/낙구';
            currentPA.textLogs.push({
              id: `field_err_${Math.random()}`,
              resultText: `야수 수비 ${actionKo}`,
              type: 'highlight',
            });
          }
        }
      } else if (type === 'THROW_ACTION') {
        if (currentPA && ev.target_base) {
          const baseName = ev.target_base === 4 ? '홈' : `${ev.target_base}루`;
          const throwerLabel = getPlayerLabel(ev.thrower_id, playersMap, '수비수', batterOrderMap);
          currentPA.textLogs.push({
            id: `throw_${Math.random()}`,
            resultText: `${throwerLabel} ${baseName} 송구`,
            type: 'normal',
          });
        }
      } else if (type === 'BASE_RUN_START') {
        if (currentPA && ev.reason) {
          if (ev.runner_id && ev.start_base !== undefined) {
            runnerStartBaseMap[Number(ev.runner_id)] = ev.start_base;
          }

          const reasonKo = BASE_RUN_REASON_MAP[ev.reason] || ev.reason;
          const isCurrentBatter = ev.runner_id && Number(ev.runner_id) === currentPA.batterId;
          const sBase = ev.start_base !== undefined ? ev.start_base : (ev.runner_id ? runnerStartBaseMap[Number(ev.runner_id)] : undefined);

          let runnerLabel = '';
          if (!isCurrentBatter && ev.runner_id) {
            const pId = Number(ev.runner_id);
            const player = playersMap?.[pId] || (playersMap ? Object.values(playersMap).find((p) => p.id === pId) : undefined);
            const pName = player ? player.name : `#${pId}`;
            const basePrefix = sBase === 1 ? '1루 주자' : sBase === 2 ? '2루 주자' : sBase === 3 ? '3루 주자' : '주자';
            runnerLabel = `${basePrefix} ${pName} `;
          }

          const targetName = ev.target_base === 4 ? '홈' : `${ev.target_base}루`;
          currentPA.textLogs.push({
            id: `run_start_${Math.random()}`,
            resultText: `${runnerLabel}${targetName} ${reasonKo}`.trim(),
            type: 'highlight',
          });
        }
      } else if (type === 'BASE_RUN_RESULT') {
        if (currentPA) {
          const res = ev.result;
          const baseName = ev.target_base === 4 ? '홈' : `${ev.target_base}루`;
          const isCurrentBatter = ev.runner_id && Number(ev.runner_id) === currentPA.batterId;
          const sBase = ev.runner_id ? runnerStartBaseMap[Number(ev.runner_id)] : undefined;

          let runnerLabel = '';
          if (!isCurrentBatter && ev.runner_id) {
            const pId = Number(ev.runner_id);
            const player = playersMap?.[pId] || (playersMap ? Object.values(playersMap).find((p) => p.id === pId) : undefined);
            const pName = player ? player.name : `#${pId}`;
            const basePrefix = sBase === 1 ? '1루 주자' : sBase === 2 ? '2루 주자' : sBase === 3 ? '3루 주자' : '주자';
            runnerLabel = `${basePrefix} ${pName}`;
          }

          const prefix = runnerLabel ? `${runnerLabel} ` : '';
          let resText = `${prefix}${baseName}에서 ${BASE_RUN_RESULT_MAP[res] || res}`;

          const isScoreEvent = res === 'SCORE' || (res === 'SAFE' && ev.target_base === 4);

          if (isScoreEvent) {
            const isBatterHomerun = ev.runner_id && Number(ev.runner_id) === currentPA.batterId;
            if (isBatterHomerun) {
              currentPA.summary = '홈런';
              currentPA.resultType = 'HOMERUN';
              resText = '솔로/대형 홈런 (득점)';
            } else {
              resText = `${prefix}${baseName} 홈인 (득점)`;
            }

            currentPA.runsScored = (currentPA.runsScored || 0) + 1;
            if (currentInning) {
              if (currentInning.isTop) {
                awayScore += 1;
                currentInning.awayScore = awayScore;
              } else {
                homeScore += 1;
                currentInning.homeScore = homeScore;
              }
            }
            currentPA.awayScore = awayScore;
            currentPA.homeScore = homeScore;
            currentPA.textLogs.push({
              id: `score_${Math.random()}`,
              resultText: resText,
              type: 'score',
            });
            if (currentPA.resultType === 'ETC') {
              currentPA.resultType = 'HIT';
            }
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
              resultText: resText,
              type: 'highlight',
            });
          } else if (res === 'OUT' || res === 'TAG_OUT' || res === 'FORCE_OUT') {
            outs++;
            if (currentPA.resultType === 'ETC') {
              currentPA.summary = `${baseName} ${BASE_RUN_RESULT_MAP[res] || '아웃'}`;
              currentPA.resultType = 'OUT';
            }
            currentPA.textLogs.push({
              id: `out_${Math.random()}`,
              resultText: resText,
              type: 'normal',
            });
          }
        }
      }

 else if (type === 'NOTICE') {
        if (currentPA && ev.message) {

          currentPA.textLogs.push({
            id: `notice_${Math.random()}`,
            resultText: ev.message,
            type: ev.message.includes('홈런') ? 'score' : ev.message.includes('안타') ? 'highlight' : 'normal',
          });

          if (ev.message.includes('홈런')) {
            currentPA.summary = '홈런';
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

    // 각 이닝의 누적 점수 보정 (뒤쪽 이닝 점수가 앞선 점수를 이어받도록 보장)
    let runningAway = 0;
    let runningHome = 0;
    for (const inn of innings) {
      if (inn.awayScore < runningAway) inn.awayScore = runningAway;
      else runningAway = inn.awayScore;

      if (inn.homeScore < runningHome) inn.homeScore = runningHome;
      else runningHome = inn.homeScore;
    }

    return innings;
  }, [matchLog, awayClub, homeClub]);

  // 2. 선택된 이닝 상태 관리
  const [selectedInningId, setSelectedInningId] = useState<string>('');

  // matchLog 데이터 변경 시(다른 경기로 이동 시) 선택 이닝 상태 초기화
  React.useEffect(() => {
    setSelectedInningId('');
  }, [matchLog]);

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

                const isScored = Boolean(pa.runsScored && pa.runsScored > 0);

                return (
                  <div key={idx} className={`match-broadcast__pa-card ${isScored ? 'match-broadcast__pa-card--scored' : ''}`}>
                    <div className="match-broadcast__pa-header">
                      <div className="match-broadcast__pa-title-group">
                        <span className="match-broadcast__pa-num">타석 #{pa.paIndex}</span>
                        <span className="match-broadcast__pa-player">
                          {getPlayerLabel(pa.batterId, playersMap, '타자', batterOrderMap)}
                        </span>
                        {pa.pitcherId && (
                          <span className="match-broadcast__pa-vs">
                            vs {getPlayerLabel(pa.pitcherId, playersMap, '투수')}
                          </span>
                        )}
                      </div>
                      <div className="match-broadcast__pa-status-group">
                        <span className={`match-broadcast__pa-badge ${badgeClass}`}>
                          {pa.summary}
                        </span>
                        {isScored && pa.awayScore !== undefined && pa.homeScore !== undefined && (
                          <span className="match-broadcast__pa-score-changed">
                            {pa.awayScore}:{pa.homeScore}
                          </span>
                        )}
                      </div>
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
                                {log.pitchNum !== undefined ? (
                                  <span className="match-broadcast__pitch-num">{log.pitchNum}구</span>
                                ) : log.labelTag ? (
                                  <span className="match-broadcast__pitch-num">{log.labelTag}</span>
                                ) : null}
                                <span className="match-broadcast__pitch-result">{log.resultText}</span>
                                {log.countText && (
                                  <span className="match-broadcast__pitch-count">{log.countText}</span>
                                )}
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
