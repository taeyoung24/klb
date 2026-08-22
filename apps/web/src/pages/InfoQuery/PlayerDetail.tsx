import React, { useEffect, useMemo, useState } from 'react'
import { FiArrowLeft } from 'react-icons/fi'
import {
  fetchInfoQueryPlayerDetail,
  type PlayerBattingRecord,
  type PlayerDetailInfo,
  type PlayerListItem,
  type PlayerPitchingRecord,
  type PlayerTransaction,
} from '../../api/infoQuery'
import type { Club } from '../../api/clubs'
import TeamLogo from '../../components/TeamLogo/TeamLogo'
import { formatPosition } from '../../constants/positions'
import { formatSimDayDot } from '../../utils/date'
import { useSystemContext } from '../../context/SystemContext'
import { InfoQueryTable, type TableColumn } from '../../components/InfoQuery'

export interface PlayerDetailProps {
  playerId: number
  initialPlayer?: PlayerListItem | null
  clubsMap: Record<number, Club>
  onBack: () => void
}

const MBTI_TITLES: Record<string, string> = {
  INTJ: '용의주도한 전략가',
  INTP: '논리적인 사색가',
  ENTJ: '대담한 통솔자',
  ENTP: '뜨거운 논쟁을 즐기는 변론가',
  INFJ: '통찰력 있는 선지자',
  INFP: '열정적인 중재자',
  ENFJ: '정의로운 지도자',
  ENFP: '재기발랄한 활동가',
  ISTJ: '청렴결백한 논리주의자',
  ISFJ: '용감한 수호자',
  ESTJ: '엄격한 관리자',
  ESFJ: '사교적인 외교관',
  ISTP: '만능 재주꾼',
  ISFP: '호기심 많은 예술가',
  ESTP: '모험을 즐기는 사업가',
  ESFP: '자유로운 영혼의 연예인',
}

/**
 * 성향 MBTI 분석 및 4대 척도 스펙트럼 인디케이터 컴포넌트
 */
const PersonalityMbtiView: React.FC<{ personality?: number[] }> = ({ personality }) => {
  const defaultValues = [500, 500, 500, 500]
  const p = personality && personality.length >= 4 ? personality : defaultValues

  // 1000 스케일을 100% 비율로 환산 (0 ~ 100%)
  const ePct = Math.min(100, Math.max(0, Math.round((p[0] / 1000) * 100)))
  const sPct = Math.min(100, Math.max(0, Math.round((p[1] / 1000) * 100)))
  const tPct = Math.min(100, Math.max(0, Math.round((p[2] / 1000) * 100)))
  const jPct = Math.min(100, Math.max(0, Math.round((p[3] / 1000) * 100)))

  const mbtiCode = `${ePct >= 50 ? 'E' : 'I'}${sPct >= 50 ? 'S' : 'N'}${tPct >= 50 ? 'T' : 'F'}${
    jPct >= 50 ? 'J' : 'P'
  }`
  const mbtiTitle = MBTI_TITLES[mbtiCode] || '균형잡힌 성향'

  const mbtiAxes = [
    {
      leftCode: 'E',
      rightCode: 'I',
      pct: ePct,
      badgeText: ePct >= 50 ? `E ${ePct}%` : `I ${100 - ePct}%`,
    },
    {
      leftCode: 'S',
      rightCode: 'N',
      pct: sPct,
      badgeText: sPct >= 50 ? `S ${sPct}%` : `N ${100 - sPct}%`,
    },
    {
      leftCode: 'T',
      rightCode: 'F',
      pct: tPct,
      badgeText: tPct >= 50 ? `T ${tPct}%` : `F ${100 - tPct}%`,
    },
    {
      leftCode: 'J',
      rightCode: 'P',
      pct: jPct,
      badgeText: jPct >= 50 ? `J ${jPct}%` : `P ${100 - jPct}%`,
    },
  ]

  return (
    <div className="player-detail__mbti-container">
      {/* MBTI Header */}
      <div className="player-detail__mbti-header">
        <span className="player-detail__mbti-code">{mbtiCode}</span>
        <span className="player-detail__mbti-title">{mbtiTitle}</span>
      </div>

      {/* 4대 스펙트럼 인디케이터 목록 */}
      <div className="player-detail__mbti-axes">
        {mbtiAxes.map((axis, idx) => (
          <div key={idx} className="player-detail__mbti-axis-row">
            {/* 1. 상단 말풍선 인디케이터 영역 */}
            <div className="player-detail__mbti-indicator-area">
              <div
                className="player-detail__mbti-tooltip"
                style={{ left: `${axis.pct}%` }}
              >
                <span className="player-detail__mbti-tooltip-text">{axis.badgeText}</span>
                <div className="player-detail__mbti-tooltip-arrow" />
              </div>
            </div>

            {/* 2. 트랙 및 양 끝 영문 시그니처 라벨 */}
            <div className="player-detail__mbti-track-row">
              <span className="player-detail__mbti-dimmed-label player-detail__mbti-dimmed-label--left">
                {axis.leftCode}
              </span>
              <div className="player-detail__mbti-spectrum-track">
                {/* 실제 성향 위치의 세로선 틱 */}
                <div
                  className="player-detail__mbti-position-tick"
                  style={{ left: `${axis.pct}%` }}
                />
              </div>
              <span className="player-detail__mbti-dimmed-label player-detail__mbti-dimmed-label--right">
                {axis.rightCode}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * 선수 스탯 등급 반환 (1000 스케일 기준)
 */
function getStatGrade(val: number): { grade: string; className: string } {
  if (val >= 850) return { grade: 'S', className: 'player-detail__grade--s' }
  if (val >= 700) return { grade: 'A', className: 'player-detail__grade--a' }
  if (val >= 550) return { grade: 'B', className: 'player-detail__grade--b' }
  if (val >= 400) return { grade: 'C', className: 'player-detail__grade--c' }
  return { grade: 'D', className: 'player-detail__grade--d' }
}

export const PlayerDetail: React.FC<PlayerDetailProps> = ({
  playerId,
  initialPlayer,
  clubsMap,
  onBack,
}) => {
  const [player, setPlayer] = useState<PlayerDetailInfo | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    const loadDetail = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const data = await fetchInfoQueryPlayerDetail(playerId)
        if (isMounted) {
          setPlayer(data)
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to fetch player detail:', err)
          setError('선수 세부 정보를 불러오는 중 오류가 발생했습니다.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadDetail()
    return () => {
      isMounted = false
    }
  }, [playerId])

  const { currentDate } = useSystemContext()

  // 현재 데이터 소스 (상세 데이터 우선, 로딩 중 fallback으로 initialPlayer 사용)
  const targetPlayer = player || initialPlayer
  const clubId = targetPlayer?.club_id ?? 0
  const club = clubsMap[clubId]

  // 연고지(지역명) + 구단명 풀네임 생성 (예: 로시 글리터스 | Rosy Glitters)
  const fullClubText = (() => {
    if (!club) return '소속 미정'
    let ko = club.name_ko || ''
    if (club.hometown_ko && !ko.includes(club.hometown_ko)) {
      ko = `${club.hometown_ko} ${ko}`
    }
    let en = club.name || ''
    if (club.hometown && !en.includes(club.hometown)) {
      en = `${club.hometown} ${en}`
    }
    return ko && en ? `${ko} | ${en}` : ko || en || '소속 미정'
  })()

  const regionName = targetPlayer?.region?.name_ko || targetPlayer?.region?.name
  const schoolName = targetPlayer?.high_school?.name_ko || targetPlayer?.high_school?.name
  const physicalText =
    targetPlayer?.height && targetPlayer?.weight
      ? `${targetPlayer.height}cm / ${targetPlayer.weight}kg`
      : '-'

  const formatBirthWithAge = (b?: string) => {
    if (!b) return '-'
    const birth = new Date(b)
    if (isNaN(birth.getTime())) return '-'

    const dateStr = `${birth.getFullYear()}년 ${birth.getMonth() + 1}월 ${birth.getDate()}일`
    const now = currentDate || new Date(1953, 0, 1)

    let age = now.getFullYear() - birth.getFullYear()
    const m = now.getMonth() - birth.getMonth()
    if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) {
      age--
    }

    const ageStr = age >= 0 ? ` (만 ${age}세)` : ''
    return `${dateStr}${ageStr}`
  }

  // 주요 능력치 스탯 목록
  const mainStats = [
    { label: '주력 (Speed)', value: player?.speed ?? 500, desc: '주루 속도 및 도루 능력' },
    { label: '제구 / 제어 (Control)', value: player?.control ?? 500, desc: '신체 제어 및 투구 제구력' },
    { label: '파워 (Power)', value: player?.power ?? 500, desc: '타구 비거리 및 장타력' },
    { label: '유연성 (Flexibility)', value: player?.flexibility ?? 500, desc: '부상 방지 및 수비 반경' },
    { label: '집중력 (Focus)', value: player?.focus ?? 500, desc: '경기 상황별 보정 능력' },
    { label: '지구력 (Stamina)', value: player?.stamina ?? 500, desc: '이닝 소화 및 체력 소진 억제' },
    { label: '잠재력 (Potential)', value: player?.potential ?? 500, desc: '연간 스탯 성장 및 에이징 커브 보정 계수' },
  ]

  // 에너지 퍼센티지
  const currentEnergy = player?.current_energy ?? 10000
  const maxEnergy = player?.max_energy ?? 10000
  const energyPercent =
    maxEnergy > 0 ? Math.min(100, Math.max(0, Math.round((currentEnergy / maxEnergy) * 100))) : 100

  const isPitcher = targetPlayer?.position === 'PITCHER'

  // 타격 기록 테이블 컬럼 정의
  const battingColumns: TableColumn<PlayerBattingRecord>[] = useMemo(
    () => [
      { key: 'season', header: '시즌', align: 'center', bold: true },
      { key: 'avg', header: '타율', align: 'center', bold: true },
      { key: 'games', header: '경기수', align: 'center' },
      { key: 'ab', header: '타수', align: 'center' },
      { key: 'hits', header: '안타', align: 'center' },
      { key: 'homeruns', header: '홈런', align: 'center' },
      { key: 'rbi', header: '타점', align: 'center' },
      { key: 'so', header: '삼진', align: 'center' },
      { key: 'obp', header: '출루율', align: 'center' },
      { key: 'ops', header: 'OPS', align: 'center', bold: true },
    ],
    []
  )

  // 투구 기록 테이블 컬럼 정의
  const pitchingColumns: TableColumn<PlayerPitchingRecord>[] = useMemo(
    () => [
      { key: 'season', header: '시즌', align: 'center', bold: true },
      { key: 'era', header: 'ERA', align: 'center', bold: true },
      { key: 'games', header: '경기수', align: 'center' },
      { key: 'innings', header: '이닝', align: 'center' },
      { key: 'wins', header: '승', align: 'center' },
      { key: 'losses', header: '패', align: 'center' },
      { key: 'saves', header: '세이브', align: 'center' },
      { key: 'holds', header: '홀드', align: 'center' },
      { key: 'so', header: 'K', align: 'center' },
      { key: 'hits', header: '피안타', align: 'center' },
      { key: 'homeruns', header: '피홈런', align: 'center' },
      { key: 'runs', header: '실점', align: 'center' },
      { key: 'bb', header: '볼넷', align: 'center' },
      { key: 'hbp', header: '사구', align: 'center' },
      { key: 'whip', header: 'WHIP', align: 'center', bold: true },
    ],
    []
  )

  // 소속 변경 및 계약 이력 테이블 컬럼 정의
  const transactionColumns: TableColumn<PlayerTransaction>[] = useMemo(
    () => [
      {
        key: 'sim_day',
        header: '일자',
        align: 'center',
        width: '110px',
        render: (row) => <span className="player-detail__history-day">{formatSimDayDot(row.sim_day)}</span>,
      },
      {
        key: 'transaction_type',
        header: '구분',
        align: 'center',
        width: '120px',
        render: (row) => {
          const typeNames: Record<string, string> = {
            DRAFT: '신인 드래프트',
            UNDRAFTED_SIGN: '육성선수 입단',
            TRADE: '트레이드',
            FA: 'FA 계약',
            RELEASE: '방출',
            WAIVER: '웨이버',
            RETIRE: '은퇴',
          }
          const label = typeNames[row.transaction_type] || row.transaction_type
          const isDark = row.transaction_type === 'DRAFT' || row.transaction_type === 'FA'
          return (
            <span className={isDark ? 'player-detail__tx-chip player-detail__tx-chip--dark' : 'player-detail__tx-chip'}>
              {label}
            </span>
          )
        },
      },
      {
        key: 'details',
        header: '상세 내용',
        align: 'left',
        render: (row) => row.details || '-',
      },
      {
        key: 'club_change',
        header: '소속 변화',
        align: 'center',
        width: '240px',
        render: (row) => {
          if (row.from_club_name && row.to_club_name) {
            return `${row.from_club_name} → ${row.to_club_name}`
          }
          return row.to_club_name || row.from_club_name || '-'
        },
      },
    ],
    []
  )

  return (
    <div className="player-detail">
      {/* Top Back Navigation Button */}
      <div className="player-detail__top-nav">
        <button type="button" className="player-detail__back-button" onClick={onBack}>
          <FiArrowLeft size={16} />
          <span>선수 목록으로 돌아가기</span>
        </button>
      </div>

      {isLoading && !player ? (
        <div className="info-query__status">선수 상세 정보를 불러오는 중입니다...</div>
      ) : error && !player ? (
        <div className="info-query__status info-query__status--error">{error}</div>
      ) : targetPlayer ? (
        <>
          {/* Header Info Block */}
          <div className="player-detail__header">
            <div className="player-detail__header-main">
              <div className="player-detail__uniform">#{targetPlayer.uniform_number || '-'}</div>
              <div className="player-detail__title-group">
                <div className="player-detail__name-wrap">
                  <h2 className="player-detail__name">{targetPlayer.name}</h2>
                  <span className="player-detail__position-badge">
                    {formatPosition(targetPlayer.position)}
                  </span>
                  {player?.roster_status && (
                    <span className="player-detail__status-badge">{player.roster_status}</span>
                  )}
                </div>
                <div className="player-detail__team-info">
                  <TeamLogo teamCode={club?.team_code} teamName={club?.name_ko || club?.name} size={22} />
                  <span className="player-detail__team-name">{fullClubText}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Profile & Physical Specs (Flat Grid Table) */}
          <div className="player-detail__section">
            <h3 className="player-detail__section-title">기본 신상 정보</h3>
            <div className="player-detail__profile-grid">
              <div className="player-detail__profile-item">
                <span className="player-detail__profile-label">생년월일</span>
                <span className="player-detail__profile-value">{formatBirthWithAge(player?.birthday)}</span>
              </div>
              <div className="player-detail__profile-item">
                <span className="player-detail__profile-label">신체조건</span>
                <span className="player-detail__profile-value">{physicalText}</span>
              </div>
              <div className="player-detail__profile-item">
                <span className="player-detail__profile-label">출생지</span>
                <span className="player-detail__profile-value">{regionName || '-'}</span>
              </div>
              <div className="player-detail__profile-item">
                <span className="player-detail__profile-label">출신교</span>
                <span className="player-detail__profile-value">{schoolName || '-'}</span>
              </div>
              <div className="player-detail__profile-item player-detail__profile-item--full">
                <span className="player-detail__profile-label">입단 구분 / 지명 순위</span>
                <span className="player-detail__profile-value">
                  {player?.draft_info || (player?.draft_round && player?.draft_overall_pick ? `${player.draft_round}라운드 (전체 ${player.draft_overall_pick}순위)` : '-')}
                </span>
              </div>
              <div className="player-detail__profile-item player-detail__profile-item--full">
                <span className="player-detail__profile-label">현재 체력 컨디션</span>
                <div className="player-detail__energy-wrap">
                  <div className="player-detail__energy-bar-track">
                    <div
                      className="player-detail__energy-bar-fill"
                      style={{ width: `${energyPercent}%` }}
                    />
                  </div>
                  <span className="player-detail__energy-text">
                    {currentEnergy.toLocaleString()} / {maxEnergy.toLocaleString()} HP ({energyPercent}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Visualizer Sections: Major Stats Bar + Personality MBTI */}
          <div className="player-detail__visual-layout">
            {/* Left: 6 Major Stats Bar Graph */}
            <div className="player-detail__stats-col">
              <h3 className="player-detail__section-title">주요 능력치 스탯 (게임 지표)</h3>
              <div className="player-detail__stats-list">
                {mainStats.map((st) => {
                  const pct = Math.min(100, Math.max(0, (st.value / 1000) * 100))
                  const { grade, className } = getStatGrade(st.value)
                  return (
                    <div key={st.label} className="player-detail__stat-row">
                      <div className="player-detail__stat-header">
                        <span className="player-detail__stat-label">{st.label}</span>
                        <div className="player-detail__stat-val-group">
                          <span className={`player-detail__grade-badge ${className}`}>{grade}</span>
                          <span className="player-detail__stat-number">{st.value}</span>
                        </div>
                      </div>
                      <div className="player-detail__stat-bar-track">
                        <div
                          className="player-detail__stat-bar-fill"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <div className="player-detail__stat-desc">{st.desc}</div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right: Personality MBTI Analysis */}
            <div className="player-detail__mbti-col">
              <h3 className="player-detail__section-title">성향 및 멘탈리티 (MBTI)</h3>
              <PersonalityMbtiView personality={player?.personality} />
            </div>
          </div>

          {/* Season & Career Records Section (Pitcher / Batter) */}
          <div className="player-detail__section">
            <h3 className="player-detail__section-title">
              {isPitcher ? '시즌별 투구 성적' : '시즌별 타격 성적'}
            </h3>
            {isPitcher ? (
              <InfoQueryTable
                columns={pitchingColumns}
                data={player?.pitching_records || []}
                rowKey={(r, idx) => `pitch-${r.season}-${idx}`}
                emptyMessage="기록된 투구 성적이 없습니다."
              />
            ) : (
              <InfoQueryTable
                columns={battingColumns}
                data={player?.batting_records || player?.records || []}
                rowKey={(r, idx) => `bat-${r.season}-${idx}`}
                emptyMessage="기록된 타격 성적이 없습니다."
              />
            )}
          </div>

          {/* Career & Transaction History Section */}
          <div className="player-detail__section">
            <h3 className="player-detail__section-title">소속 변경 및 계약 이력</h3>
            <InfoQueryTable
              columns={transactionColumns}
              data={player?.transactions || []}
              rowKey={(r, idx) => `tx-${r.id}-${idx}`}
              emptyMessage="기록된 계약 및 소속 변경 이력이 없습니다."
            />
          </div>
        </>
      ) : null}
    </div>
  )
}

export default PlayerDetail
