import React, { useEffect, useState } from 'react'
import { FiArrowLeft } from 'react-icons/fi'
import { fetchInfoQueryPlayerDetail, type PlayerDetailInfo, type PlayerListItem } from '../../api/infoQuery'
import type { Club } from '../../api/clubs'
import TeamLogo from '../../components/TeamLogo/TeamLogo'
import { formatPosition } from '../../constants/positions'
import { useSystemContext } from '../../context/SystemContext'

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
 * 성향 MBTI 분석 및 4대 척도 시각화 컴포넌트
 */
const PersonalityMbtiView: React.FC<{ personality?: number[] }> = ({ personality }) => {
  const defaultValues = [500, 500, 500, 500]
  const p = personality && personality.length >= 4 ? personality : defaultValues

  // 1000 스케일을 100% 비율로 환산
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
      leftLabel: '외향 (E)',
      rightLabel: '내향 (I)',
      leftPct: ePct,
      rightPct: 100 - ePct,
      isLeftDominant: ePct >= 50,
    },
    {
      leftLabel: '감각 (S)',
      rightLabel: '직관 (N)',
      leftPct: sPct,
      rightPct: 100 - sPct,
      isLeftDominant: sPct >= 50,
    },
    {
      leftLabel: '사고 (T)',
      rightLabel: '감정 (F)',
      leftPct: tPct,
      rightPct: 100 - tPct,
      isLeftDominant: tPct >= 50,
    },
    {
      leftLabel: '판단 (J)',
      rightLabel: '인식 (P)',
      leftPct: jPct,
      rightPct: 100 - jPct,
      isLeftDominant: jPct >= 50,
    },
  ]

  return (
    <div className="player-detail__mbti-container">
      {/* MBTI Header */}
      <div className="player-detail__mbti-header">
        <span className="player-detail__mbti-code">{mbtiCode}</span>
        <span className="player-detail__mbti-title">{mbtiTitle}</span>
      </div>

      {/* 4대 척도 비율 바 목록 */}
      <div className="player-detail__mbti-axes">
        {mbtiAxes.map((axis, idx) => (
          <div key={idx} className="player-detail__mbti-axis-row">
            <div className="player-detail__mbti-axis-labels">
              <span
                className={`player-detail__mbti-axis-label ${
                  axis.isLeftDominant ? 'player-detail__mbti-axis-label--dominant' : ''
                }`}
              >
                {axis.leftLabel} {axis.leftPct}%
              </span>
              <span
                className={`player-detail__mbti-axis-label ${
                  !axis.isLeftDominant ? 'player-detail__mbti-axis-label--dominant' : ''
                }`}
              >
                {axis.rightPct}% {axis.rightLabel}
              </span>
            </div>
            <div className="player-detail__mbti-bar-track">
              <div
                className="player-detail__mbti-bar-fill"
                style={{ width: `${axis.leftPct}%` }}
              />
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
    const now = currentDate || new Date()

    let age = now.getFullYear() - birth.getFullYear()
    const m = now.getMonth() - birth.getMonth()
    if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) {
      age--
    }

    const ageStr = age >= 0 ? ` (만 ${age}세)` : ''
    return `${dateStr}${ageStr}`
  }

  // 주요 6대 스탯 목록
  const mainStats = [
    { label: '주력 (Speed)', value: player?.speed ?? 500, desc: '주루 속도 및 도루 능력' },
    { label: '제구 / 제어 (Control)', value: player?.control ?? 500, desc: '신체 제어 및 투구 제구력' },
    { label: '파워 (Power)', value: player?.power ?? 500, desc: '타구 비거리 및 장타력' },
    { label: '유연성 (Flexibility)', value: player?.flexibility ?? 500, desc: '부상 방지 및 수비 반경' },
    { label: '집중력 (Focus)', value: player?.focus ?? 500, desc: '경기 상황별 보정 능력' },
    { label: '지구력 (Stamina)', value: player?.stamina ?? 500, desc: '이닝 소화 및 체력 소진 억제' },
  ]

  // 에너지 퍼센티지
  const currentEnergy = player?.current_energy ?? 10000
  const maxEnergy = player?.max_energy ?? 10000
  const energyPercent =
    maxEnergy > 0 ? Math.min(100, Math.max(0, Math.round((currentEnergy / maxEnergy) * 100))) : 100

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
        </>
      ) : null}
    </div>
  )
}

export default PlayerDetail
