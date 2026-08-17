import React, { useEffect, useMemo, useState } from 'react'
import type { Club } from '../../api/clubs'
import { getLatestStandings, type DailyClubStanding } from '../../api/standings'
import { getMatches, getMatchPlaceholders, type Match, type MatchPlaceholder } from '../../api/matches'
import TeamLogo from '../../components/TeamLogo/TeamLogo'
import { InfoQueryTable, type TableColumn } from '../../components/InfoQuery'

const LEAGUES = [
  { code: 'AL' as const, id: 1, name: '아젤리아 리그' },
  { code: 'CL' as const, id: 2, name: '카멜리아 리그' },
  { code: 'GL' as const, id: 3, name: '젠티아나 리그' },
  { code: 'ML' as const, id: 4, name: '매그놀리아 리그' },
]

type LeagueCode = 'AL' | 'CL' | 'GL' | 'ML'

export interface SeasonStandingsTabProps {
  clubsMap: Record<number, Club>
  availableSeasons: number[]
  initialSeasonYear: number | null
}

export const SeasonStandingsTab: React.FC<SeasonStandingsTabProps> = ({
  clubsMap,
  availableSeasons,
  initialSeasonYear,
}) => {
  const [selectedSeasonYear, setSelectedSeasonYear] = useState<number | null>(initialSeasonYear)
  const [selectedLeague, setSelectedLeague] = useState<LeagueCode>('AL')
  const [regularStandings, setRegularStandings] = useState<DailyClubStanding[]>([])
  const [eliteStandings, setEliteStandings] = useState<DailyClubStanding[]>([])
  const [placeholders, setPlaceholders] = useState<MatchPlaceholder[]>([])
  const [knockoutMatches, setKnockoutMatches] = useState<Match[]>([])
  const [seedMap, setSeedMap] = useState<Record<number, string>>({})
  const [isStandingsLoading, setIsStandingsLoading] = useState<boolean>(false)
  const [standingsError, setStandingsError] = useState<string | null>(null)

  // initialSeasonYear가 나중에 로드될 경우 동기화
  useEffect(() => {
    if (selectedSeasonYear === null && initialSeasonYear !== null) {
      setSelectedSeasonYear(initialSeasonYear)
    }
  }, [initialSeasonYear, selectedSeasonYear])

  useEffect(() => {
    let isMounted = true
    const fetchSeasonData = async () => {
      setIsStandingsLoading(true)
      setStandingsError(null)
      try {
        const targetYear = selectedSeasonYear || undefined
        const [regStandings, postStandings, phList, koMatches] = await Promise.all([
          getLatestStandings({ year: targetYear, isPostseason: false }),
          getLatestStandings({ year: targetYear, isPostseason: true }),
          getMatchPlaceholders(targetYear).catch(() => []),
          getMatches({ year: targetYear, stage: 'KNOCKOUT' }).catch(() => []),
        ])

        if (isMounted) {
          setRegularStandings(regStandings)
          setEliteStandings(postStandings)
          setPlaceholders(phList)
          setKnockoutMatches(koMatches)

          // Build Seed Map for Top 4 clubs of each league
          const map: Record<number, string> = {}
          const leagueMapById: Record<number, string> = { 1: 'AL', 2: 'CL', 3: 'GL', 4: 'ML' }
          regStandings.forEach((row) => {
            if (row.rank <= 4) {
              const code = leagueMapById[row.league_id] || 'AL'
              map[row.club_id] = `${code}#${row.rank}`
            }
          })
          setSeedMap(map)
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to fetch season standings:', err)
          setStandingsError('시즌 최종 순위 및 대진표 정보를 불러오는 중 오류가 발생했습니다.')
        }
      } finally {
        if (isMounted) {
          setIsStandingsLoading(false)
        }
      }
    }

    fetchSeasonData()
    return () => {
      isMounted = false
    }
  }, [selectedSeasonYear])

  // Filtered regular standings for selected league
  const filteredLeagueStandings = useMemo(() => {
    const targetLeague = LEAGUES.find((l) => l.code === selectedLeague)
    if (!targetLeague) return []
    return regularStandings
      .filter((s) => s.league_id === targetLeague.id)
      .sort((a, b) => a.rank - b.rank)
  }, [regularStandings, selectedLeague])

  const formatPct = (pct?: number) => {
    if (pct === undefined || pct === null) return '.000'
    return pct.toFixed(3).replace(/^0\./, '.')
  }

  const formatGb = (gb?: number) => {
    if (gb === undefined || gb === null || gb === 0) return '-'
    const val = gb / 10
    if (val === 0) return '-'
    return val % 1 === 0 ? val.toFixed(0) : val.toFixed(1)
  }

  const formatStreak = (streak?: number) => {
    if (!streak || streak === 0) return '-'
    return streak > 0 ? `${streak}연승` : `${Math.abs(streak)}연패`
  }

  // 순위표 컬럼 정의
  const standingsColumns: TableColumn<DailyClubStanding>[] = useMemo(
    () => [
      {
        key: 'rank',
        header: '순위',
        align: 'center',
        bold: true,
        render: (s) => s.rank,
      },
      {
        key: 'club',
        header: '구단',
        bold: true,
        render: (s) => {
          const club = clubsMap[s.club_id]
          const isPlayoffSeed = s.rank <= 4
          return (
            <div className="info-query__team-cell">
              <TeamLogo
                teamCode={club?.team_code}
                teamName={club?.name_ko || club?.name}
                size={20}
              />
              <span>{club?.name_ko || club?.name || `구단 #${s.club_id}`}</span>
              {isPlayoffSeed && (
                <span className="info-query__seed-badge">
                  {selectedLeague}#{s.rank}
                </span>
              )}
            </div>
          )
        },
      },
      {
        key: 'games_played',
        header: '경기',
        align: 'center',
        render: (s) => s.games_played,
      },
      {
        key: 'wins',
        header: '승',
        align: 'center',
        render: (s) => s.wins,
      },
      {
        key: 'draws',
        header: '무',
        align: 'center',
        render: (s) => s.draws,
      },
      {
        key: 'losses',
        header: '패',
        align: 'center',
        render: (s) => s.losses,
      },
      {
        key: 'win_rate',
        header: '승률',
        align: 'center',
        bold: true,
        render: (s) => formatPct(s.win_rate),
      },
      {
        key: 'games_back',
        header: '게임차',
        align: 'center',
        render: (s) => formatGb(s.games_back),
      },
      {
        key: 'streak',
        header: '연속',
        align: 'center',
        render: (s) => formatStreak(s.streak),
      },
    ],
    [clubsMap, selectedLeague]
  )

  // --- Knockout Bracket Logic ---
  const getKnockoutResults = () => {
    const top8 = eliteStandings.slice(0, 8).map((r) => r.club_id)
    const fallbackClubs = Object.keys(clubsMap).map(Number).slice(0, 8)
    const t8 = top8.length === 8 ? top8 : fallbackClubs

    const getWinsCount = (c1: number | null, c2: number | null, isBo3Advantage = false) => {
      if (!c1 || !c2) return { c1_wins: isBo3Advantage ? 1 : 0, c2_wins: 0 }
      let c1_wins = isBo3Advantage ? 1 : 0
      let c2_wins = 0
      knockoutMatches.forEach((m) => {
        const h = m.home_club_id
        const a = m.away_club_id
        if (m.status === 'COMPLETED' && ((h === c1 && a === c2) || (h === c2 && a === c1))) {
          const winner = (m.home_score ?? 0) > (m.away_score ?? 0) ? h : a
          if (winner === c1) c1_wins += 1
          else c2_wins += 1
        }
      })
      return { c1_wins, c2_wins }
    }

    const qList = placeholders.filter((p) => p.round === 'ROUND_OF_8').sort((a, b) => a.id - b.id)
    const sList = placeholders.filter((p) => p.round === 'SEMI_FINAL').sort((a, b) => a.id - b.id)
    const fList = placeholders.filter((p) => p.round === 'FINAL')

    const q_nodes = qList.map((p, idx) => {
      const home = p.home_club_id ?? t8[idx] ?? null
      const away = p.away_club_id ?? t8[7 - idx] ?? null
      const wins = getWinsCount(home, away, true)
      const winner = wins.c1_wins >= 2 ? home : wins.c2_wins >= 2 ? away : null
      return { id: `q${idx + 1}`, home, away, wins, winner, pId: p.id }
    })

    const qMap = new Map(q_nodes.map((n) => [n.pId, n]))

    const s_nodes = sList.map((p, idx) => {
      const homeParent = p.home_parent_id ? qMap.get(p.home_parent_id) : null
      const awayParent = p.away_parent_id ? qMap.get(p.away_parent_id) : null

      const home = p.home_club_id ?? homeParent?.winner ?? null
      const away = p.away_club_id ?? awayParent?.winner ?? null

      const wins = getWinsCount(home, away, false)
      const winner = wins.c1_wins >= 3 ? home : wins.c2_wins >= 3 ? away : null
      return { id: `s${idx + 1}`, home, away, wins, winner, pId: p.id }
    })

    const sMap = new Map(s_nodes.map((n) => [n.pId, n]))

    const fP = fList[0]
    const fHomeParent = fP?.home_parent_id ? sMap.get(fP.home_parent_id) : null
    const fAwayParent = fP?.away_parent_id ? sMap.get(fP.away_parent_id) : null

    const fHome = fP?.home_club_id ?? fHomeParent?.winner ?? null
    const fAway = fP?.away_club_id ?? fAwayParent?.winner ?? null

    const fWins = getWinsCount(fHome, fAway, false)
    const fWinner = fWins.c1_wins >= 4 ? fHome : fWins.c2_wins >= 4 ? fAway : null

    return {
      q1: q_nodes[0] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      q2: q_nodes[1] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      q3: q_nodes[2] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      q4: q_nodes[3] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      s1: s_nodes[0] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      s2: s_nodes[1] || { home: null, away: null, wins: { c1_wins: 0, c2_wins: 0 }, winner: null },
      f: { home: fHome, away: fAway, wins: fWins, winner: fWinner },
    }
  }

  const renderSeriesNode = (
    title: string,
    homeId: number | null,
    awayId: number | null,
    isBo3Advantage = false,
    seriesLimit = 3
  ) => {
    const homeClub = homeId ? clubsMap[homeId] : null
    const awayClub = awayId ? clubsMap[awayId] : null

    const homeName = homeClub ? homeClub.name_ko || homeClub.name : '미정 (TBD)'
    const awayName = awayClub ? awayClub.name_ko || awayClub.name : '미정 (TBD)'

    const homeSeed = homeId ? seedMap[homeId] || '' : ''
    const awaySeed = awayId ? seedMap[awayId] || '' : ''

    const homeCode = homeClub?.team_code
    const awayCode = awayClub?.team_code

    // Extract match scores
    const upperScores: number[] = []
    const lowerScores: number[] = []

    if (isBo3Advantage) {
      upperScores.push(1)
      lowerScores.push(0)
    }

    if (homeId && awayId) {
      const matches = knockoutMatches
        .filter(
          (m) =>
            m.status === 'COMPLETED' &&
            ((m.home_club_id === homeId && m.away_club_id === awayId) ||
              (m.home_club_id === awayId && m.away_club_id === homeId))
        )
        .sort((a, b) => a.sim_day - b.sim_day)

      matches.forEach((m) => {
        const isC1Home = m.home_club_id === homeId
        upperScores.push(isC1Home ? m.home_score ?? 0 : m.away_score ?? 0)
        lowerScores.push(isC1Home ? m.away_score ?? 0 : m.home_score ?? 0)
      })
    }

    let upperWins = 0
    let lowerWins = 0
    const maxLen = Math.max(upperScores.length, lowerScores.length)
    for (let i = 0; i < maxLen; i++) {
      if (upperScores[i] !== undefined && lowerScores[i] !== undefined) {
        if (upperScores[i] > lowerScores[i]) upperWins++
        else if (lowerScores[i] > upperScores[i]) lowerWins++
      }
    }

    const winsNeeded = Math.floor(seriesLimit / 2) + 1
    const homeIsWinner = upperWins >= winsNeeded
    const awayIsWinner = lowerWins >= winsNeeded

    const renderScoreSlots = (scores: number[], oppScores: number[]) => {
      const slots = []
      for (let i = 0; i < seriesLimit; i++) {
        const score = scores[i]
        const oppScore = oppScores[i]
        const isWinnerScore = score !== undefined && oppScore !== undefined && score > oppScore
        const isAdvantageSlot = isBo3Advantage && i === 0
        const displayText = isAdvantageSlot ? '-' : score !== undefined ? score : '-'
        slots.push(
          <span
            key={i}
            className={`info-query__bracket-score-slot ${
              score === undefined ? 'info-query__bracket-score-slot--empty' : ''
            } ${isWinnerScore ? 'info-query__bracket-score-slot--winner' : ''}`}
          >
            {displayText}
          </span>
        )
      }
      return slots
    }

    return (
      <div className="info-query__bracket-node">
        <div className="info-query__bracket-node-title">{title}</div>
        <div className="info-query__bracket-node-teams">
          {/* Upper / Home Team */}
          <div
            className={`info-query__bracket-team ${
              homeIsWinner ? 'info-query__bracket-team--winner' : ''
            }`}
          >
            <div className="info-query__bracket-team-info">
              <TeamLogo teamCode={homeCode} teamName={homeName} size={18} />
              <span className="info-query__bracket-team-name">{homeName}</span>
              {homeSeed && <span className="info-query__bracket-seed">{homeSeed}</span>}
            </div>
            <div className="info-query__bracket-scores">
              {renderScoreSlots(upperScores, lowerScores)}
            </div>
          </div>

          {/* Lower / Away Team */}
          <div
            className={`info-query__bracket-team ${
              awayIsWinner ? 'info-query__bracket-team--winner' : ''
            }`}
          >
            <div className="info-query__bracket-team-info">
              <TeamLogo teamCode={awayCode} teamName={awayName} size={18} />
              <span className="info-query__bracket-team-name">{awayName}</span>
              {awaySeed && <span className="info-query__bracket-seed">{awaySeed}</span>}
            </div>
            <div className="info-query__bracket-scores">
              {renderScoreSlots(lowerScores, upperScores)}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const bracketData = getKnockoutResults()

  return (
    <div className="info-query__season-section">
      {/* Season Year Filter Bar */}
      <div className="info-query__filter-bar">
        <div className="info-query__filter-group">
          <label htmlFor="season-year-select" className="info-query__label">
            시즌 선택:{' '}
          </label>
          <select
            id="season-year-select"
            className="info-query__select"
            value={selectedSeasonYear || (availableSeasons.length > 0 ? availableSeasons[0] : '')}
            onChange={(e) => setSelectedSeasonYear(Number(e.target.value))}
          >
            {availableSeasons.map((year) => (
              <option key={year} value={year}>
                {year} 시즌
              </option>
            ))}
          </select>
        </div>
      </div>

      {isStandingsLoading ? (
        <div className="info-query__status">시즌 순위 및 대진표 데이터를 불러오는 중입니다...</div>
      ) : standingsError ? (
        <div className="info-query__status info-query__status--error">{standingsError}</div>
      ) : (
        <>
          {/* Section 1: 4대 리그 정규시즌 최종 순위표 */}
          <div className="info-query__sub-block">
            <div className="info-query__sub-header">
              <h3 className="info-query__sub-title">{selectedSeasonYear} 정규리그 최종 순위</h3>
              <div className="info-query__league-tabs">
                {LEAGUES.map((lg) => (
                  <button
                    key={lg.code}
                    type="button"
                    className={`info-query__league-tab ${
                      selectedLeague === lg.code ? 'info-query__league-tab--active' : ''
                    }`}
                    onClick={() => setSelectedLeague(lg.code)}
                  >
                    {lg.code} ({lg.name.split(' ')[0]})
                  </button>
                ))}
              </div>
            </div>

            <InfoQueryTable
              columns={standingsColumns}
              data={filteredLeagueStandings}
              rowKey={(s) => s.id || s.club_id}
              emptyMessage="순위 데이터가 아직 등록되지 않았습니다."
            />
          </div>

          {/* Section 2: 포스트시즌 KROWN SERIES 녹아웃 토너먼트 대진표 */}
          <div className="info-query__sub-block">
            <div className="info-query__sub-header">
              <h3 className="info-query__sub-title">
                {selectedSeasonYear} 포스트시즌 KROWN SERIES 대진표
              </h3>
            </div>

            <div className="info-query__bracket-view">
              {/* Column 1: 8강전 */}
              <div className="info-query__bracket-col info-query__bracket-col--qf">
                <div className="info-query__bracket-header">8강전 (Bo3, 1승선취)</div>
                <div className="info-query__bracket-nodes">
                  {renderSeriesNode('8강 1경기', bracketData.q1.home, bracketData.q1.away, true, 3)}
                  {renderSeriesNode('8강 2경기', bracketData.q2.home, bracketData.q2.away, true, 3)}
                  {renderSeriesNode('8강 3경기', bracketData.q3.home, bracketData.q3.away, true, 3)}
                  {renderSeriesNode('8강 4경기', bracketData.q4.home, bracketData.q4.away, true, 3)}
                </div>
              </div>

              {/* Column 2: 준결승전 */}
              <div className="info-query__bracket-col info-query__bracket-col--sf">
                <div className="info-query__bracket-header">준결승전 (Bo5)</div>
                <div className="info-query__bracket-nodes">
                  {renderSeriesNode('준결승 1경기', bracketData.s1.home, bracketData.s1.away, false, 5)}
                  {renderSeriesNode('준결승 2경기', bracketData.s2.home, bracketData.s2.away, false, 5)}
                </div>
              </div>

              {/* Column 3: 결승전 */}
              <div className="info-query__bracket-col info-query__bracket-col--f">
                <div className="info-query__bracket-header">KROWN SERIES (Bo7)</div>
                <div className="info-query__bracket-nodes info-query__bracket-nodes--center">
                  {renderSeriesNode('KROWN SERIES', bracketData.f.home, bracketData.f.away, false, 7)}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default SeasonStandingsTab
