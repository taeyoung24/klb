import { useEffect, useMemo, useState } from 'react'
import {
  FiChevronLeft,
  FiChevronRight,
  FiChevronsLeft,
  FiChevronsRight,
  FiMoreHorizontal,
} from 'react-icons/fi'
import { fetchInfoQueryPlayers, type PlayerInfo } from '../api/infoQuery'
import { getClubs, type Club } from '../api/clubs'
import { getLatestStandings, getStandingSeasons, type DailyClubStanding } from '../api/standings'
import { getMatches, getMatchPlaceholders, type Match, type MatchPlaceholder } from '../api/matches'
import { getSystemInfo } from '../api/system'
import TeamLogo from '../components/TeamLogo/TeamLogo'
import { formatPosition } from '../constants/positions'
import './InfoQuery.css'

const ITEMS_PER_PAGE = 20

const POSITION_OPTIONS = [
  'PITCHER',
  'CATCHER',
  'FIRST_BASE',
  'SECOND_BASE',
  'THIRD_BASE',
  'SHORT_STOP',
  'LEFT_FIELD',
  'CENTER_FIELD',
  'RIGHT_FIELD',
  'DESIGNATED_HITTER',
]

const LEAGUES = [
  { code: 'AL' as const, id: 1, name: '아젤리아 리그' },
  { code: 'CL' as const, id: 2, name: '카멜리아 리그' },
  { code: 'GL' as const, id: 3, name: '젠티아나 리그' },
  { code: 'ML' as const, id: 4, name: '매그놀리아 리그' },
]

type LeagueCode = 'AL' | 'CL' | 'GL' | 'ML'

function getPageNumbers(current: number, total: number): (number | '...')[] {
  const MAX_SLOTS = 10
  if (total <= MAX_SLOTS) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  if (current <= 6) {
    return [1, 2, 3, 4, 5, 6, 7, 8, '...', total]
  }

  if (current >= total - 5) {
    return [
      1,
      '...',
      total - 7,
      total - 6,
      total - 5,
      total - 4,
      total - 3,
      total - 2,
      total - 1,
      total,
    ]
  }

  const startMid = current - 2
  return [
    1,
    '...',
    startMid,
    startMid + 1,
    startMid + 2,
    startMid + 3,
    startMid + 4,
    startMid + 5,
    '...',
    total,
  ]
}

export default function InfoQuery() {
  // Sidebar tab state
  const [activeMenu, setActiveMenu] = useState<'players' | 'seasonStandings'>('players')

  // --- Players State ---
  const [players, setPlayers] = useState<PlayerInfo[]>([])
  const [clubs, setClubs] = useState<Club[]>([])
  const [selectedClubId, setSelectedClubId] = useState<string>('all')
  const [selectedPosition, setSelectedPosition] = useState<string>('all')
  const [searchInput, setSearchInput] = useState<string>('')
  const [appliedSearchName, setAppliedSearchName] = useState<string>('')
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [totalCount, setTotalCount] = useState<number>(0)
  const [totalPages, setTotalPages] = useState<number>(1)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // --- Season Standings State ---
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([])
  const [selectedSeasonYear, setSelectedSeasonYear] = useState<number | null>(null)
  const [selectedLeague, setSelectedLeague] = useState<LeagueCode>('AL')
  const [regularStandings, setRegularStandings] = useState<DailyClubStanding[]>([])
  const [eliteStandings, setEliteStandings] = useState<DailyClubStanding[]>([])
  const [placeholders, setPlaceholders] = useState<MatchPlaceholder[]>([])
  const [knockoutMatches, setKnockoutMatches] = useState<Match[]>([])
  const [seedMap, setSeedMap] = useState<Record<number, string>>({})
  const [isStandingsLoading, setIsStandingsLoading] = useState<boolean>(false)
  const [standingsError, setStandingsError] = useState<string | null>(null)

  // 1. Initial System Info, Clubs & Available Seasons load
  useEffect(() => {
    let isMounted = true
    Promise.all([getClubs(), getSystemInfo(), getStandingSeasons().catch(() => [])])
      .then(([clubsData, sysInfo, seasons]) => {
        if (isMounted) {
          setClubs(clubsData)
          const seasonList =
            seasons && seasons.length > 0
              ? seasons
              : sysInfo?.season_year
              ? [sysInfo.season_year]
              : []
          setAvailableSeasons(seasonList)
          if (seasonList.length > 0) {
            setSelectedSeasonYear(seasonList[0])
          }
        }
      })
      .catch((err) => {
        console.error('Failed to fetch initial info:', err)
      })
    return () => {
      isMounted = false
    }
  }, [])

  // 2. Fetch Players
  useEffect(() => {
    if (activeMenu !== 'players') return

    let isMounted = true
    const fetchPlayers = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const res = await fetchInfoQueryPlayers({
          club_id: selectedClubId !== 'all' ? Number(selectedClubId) : undefined,
          position: selectedPosition !== 'all' ? selectedPosition : undefined,
          name: appliedSearchName !== '' ? appliedSearchName : undefined,
          page: currentPage,
          limit: ITEMS_PER_PAGE,
        })
        if (isMounted) {
          setPlayers(res.items)
          setTotalCount(res.total)
          setTotalPages(res.total_pages)
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to search players:', err)
          setError('선수 정보를 불러오는 중 오류가 발생했습니다.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    fetchPlayers()
    return () => {
      isMounted = false
    }
  }, [activeMenu, selectedClubId, selectedPosition, appliedSearchName, currentPage])

  // Reset page when player filter criteria change
  useEffect(() => {
    setCurrentPage(1)
  }, [selectedClubId, selectedPosition, appliedSearchName])

  // 3. Fetch Season Standings & Knockout data
  useEffect(() => {
    if (activeMenu !== 'seasonStandings') return

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
  }, [activeMenu, selectedSeasonYear])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setAppliedSearchName(searchInput.trim())
  }

  // Club ID -> Club Object mapping
  const clubsMap = useMemo(() => {
    const map: Record<number, Club> = {}
    clubs.forEach((club) => {
      map[club.id] = club
    })
    return map
  }, [clubs])

  const validCurrentPage = Math.min(Math.max(currentPage, 1), totalPages)

  const handlePageChange = (page: number) => {
    const targetPage = Math.min(Math.max(page, 1), totalPages)
    setCurrentPage(targetPage)
  }

  const pageNumbers = useMemo(() => {
    return getPageNumbers(validCurrentPage, totalPages)
  }, [validCurrentPage, totalPages])

  // Filtered regular standings for selected league
  const filteredLeagueStandings = useMemo(() => {
    const targetLeague = LEAGUES.find((l) => l.code === selectedLeague)
    if (!targetLeague) return []
    return regularStandings
      .filter((s) => s.league_id === targetLeague.id)
      .sort((a, b) => a.rank - b.rank)
  }, [regularStandings, selectedLeague])

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
        const displayText = isAdvantageSlot ? '-' : (score !== undefined ? score : '-')
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

  const formatPct = (pct?: number) => {
    if (pct === undefined || pct === null) return '.000'
    return pct.toFixed(3).replace(/^0\./, '.')
  }

  const formatGb = (gb?: number) => {
    if (gb === undefined || gb === null || gb === 0) return '-'
    return gb % 1 === 0 ? gb.toFixed(0) : gb.toFixed(1)
  }

  const formatStreak = (streak?: number) => {
    if (!streak || streak === 0) return '-'
    return streak > 0 ? `${streak}연승` : `${Math.abs(streak)}연패`
  }

  const bracketData = getKnockoutResults()

  return (
    <div className="info-query">
      <div className="info-query__container">
        <div className="info-query__layout">
          {/* Sidebar */}
          <aside className="info-query__sidebar">
            <h2 className="info-query__sidebar-title">정보 조회</h2>
            <nav className="info-query__sidebar-nav">
              <ul className="info-query__sidebar-list">
                <li className="info-query__sidebar-item">
                  <span
                    className={`info-query__sidebar-link ${
                      activeMenu === 'players' ? 'info-query__sidebar-link--active' : ''
                    }`}
                    onClick={() => setActiveMenu('players')}
                  >
                    선수 조회
                  </span>
                </li>
                <li className="info-query__sidebar-item">
                  <span
                    className={`info-query__sidebar-link ${
                      activeMenu === 'seasonStandings' ? 'info-query__sidebar-link--active' : ''
                    }`}
                    onClick={() => setActiveMenu('seasonStandings')}
                  >
                    시즌 최종 순위
                  </span>
                </li>
              </ul>
            </nav>
          </aside>

          {/* Main Content Area */}
          <main className="info-query__main">
            {/* =========================================================
                Tab 1: 선수 조회 (Players Query)
               ========================================================= */}
            {activeMenu === 'players' && (
              <>
                {/* Filter & Search Controls */}
                <div className="info-query__filter-bar">
                  <div className="info-query__filter-group">
                    <div>
                      <label htmlFor="club-select" className="info-query__label">
                        구단:{' '}
                      </label>
                      <select
                        id="club-select"
                        className="info-query__select"
                        value={selectedClubId}
                        onChange={(e) => setSelectedClubId(e.target.value)}
                      >
                        <option value="all">전체 구단</option>
                        {clubs.map((club) => (
                          <option key={club.id} value={club.id}>
                            {club.name_ko || club.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="position-select" className="info-query__label">
                        포지션:{' '}
                      </label>
                      <select
                        id="position-select"
                        className="info-query__select"
                        value={selectedPosition}
                        onChange={(e) => setSelectedPosition(e.target.value)}
                      >
                        <option value="all">전체 포지션</option>
                        {POSITION_OPTIONS.map((pos) => (
                          <option key={pos} value={pos}>
                            {formatPosition(pos)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="info-query__filter-group">
                    <form className="info-query__search-form" onSubmit={handleSearchSubmit}>
                      <input
                        type="text"
                        className="info-query__input"
                        placeholder="선수 이름 검색"
                        value={searchInput}
                        onChange={(e) => setSearchInput(e.target.value)}
                      />
                      <button type="submit" className="info-query__button">
                        검색
                      </button>
                    </form>
                    <span className="info-query__count">총 {totalCount.toLocaleString()}명</span>
                  </div>
                </div>

                {/* Status Message / Table */}
                {isLoading ? (
                  <div className="info-query__status">선수 목록을 불러오는 중입니다...</div>
                ) : error ? (
                  <div className="info-query__status info-query__status--error">{error}</div>
                ) : players.length === 0 ? (
                  <div className="info-query__status">검색 결과가 없습니다.</div>
                ) : (
                  <div className="info-query__table-wrapper">
                    <table className="info-query__table">
                      <thead className="info-query__table-head">
                        <tr>
                          <th className="info-query__table-header info-query__table-header--center">
                            배번
                          </th>
                          <th className="info-query__table-header">이름</th>
                          <th className="info-query__table-header">소속 구단</th>
                          <th className="info-query__table-header info-query__table-header--center">
                            포지션
                          </th>
                          <th className="info-query__table-header info-query__table-header--center">
                            신체조건
                          </th>
                          <th className="info-query__table-header">연고지/출신교</th>
                        </tr>
                      </thead>
                      <tbody className="info-query__table-body">
                        {players.map((p) => {
                          const clubName = clubsMap[p.club_id]?.name_ko || clubsMap[p.club_id]?.name || '-'
                          const regionName = p.region?.name_ko || p.region?.name
                          const schoolName = p.high_school?.name_ko || p.high_school?.name
                          const originText = [regionName, schoolName].filter(Boolean).join(' · ') || '-'
                          const physicalText =
                            p.height && p.weight ? `${p.height}cm / ${p.weight}kg` : '-'

                          return (
                            <tr key={p.id} className="info-query__table-row">
                              <td className="info-query__table-cell info-query__table-cell--center info-query__table-cell--bold">
                                {p.uniform_number || '-'}
                              </td>
                              <td className="info-query__table-cell info-query__table-cell--bold">
                                {p.name}
                              </td>
                              <td className="info-query__table-cell">{clubName}</td>
                              <td className="info-query__table-cell info-query__table-cell--center">
                                <span className="info-query__badge">
                                  {formatPosition(p.position)}
                                </span>
                              </td>
                              <td className="info-query__table-cell info-query__table-cell--center">
                                {physicalText}
                              </td>
                              <td className="info-query__table-cell">{originText}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Pagination */}
                {!isLoading && !error && totalPages > 1 && (
                  <div className="info-query__pagination">
                    <button
                      type="button"
                      className="info-query__pagination-button"
                      title="10페이지 이전"
                      disabled={validCurrentPage <= 1}
                      onClick={() => handlePageChange(validCurrentPage - 10)}
                    >
                      <FiChevronsLeft size={16} />
                    </button>

                    <button
                      type="button"
                      className="info-query__pagination-button"
                      title="이전 페이지"
                      disabled={validCurrentPage <= 1}
                      onClick={() => handlePageChange(validCurrentPage - 1)}
                    >
                      <FiChevronLeft size={16} />
                    </button>

                    {pageNumbers.map((item, idx) => {
                      if (item === '...') {
                        return (
                          <span key={`ellipsis-${idx}`} className="info-query__pagination-ellipsis">
                            <FiMoreHorizontal size={14} />
                          </span>
                        )
                      }
                      return (
                        <button
                          key={item}
                          type="button"
                          className={`info-query__pagination-button ${
                            item === validCurrentPage
                              ? 'info-query__pagination-button--active'
                              : ''
                          }`}
                          onClick={() => handlePageChange(item)}
                        >
                          {item}
                        </button>
                      )
                    })}

                    <button
                      type="button"
                      className="info-query__pagination-button"
                      title="다음 페이지"
                      disabled={validCurrentPage >= totalPages}
                      onClick={() => handlePageChange(validCurrentPage + 1)}
                    >
                      <FiChevronRight size={16} />
                    </button>

                    <button
                      type="button"
                      className="info-query__pagination-button"
                      title="10페이지 다음"
                      disabled={validCurrentPage >= totalPages}
                      onClick={() => handlePageChange(validCurrentPage + 10)}
                    >
                      <FiChevronsRight size={16} />
                    </button>
                  </div>
                )}
              </>
            )}

            {/* =========================================================
                Tab 2: 시즌 최종 순위 (Season Final Standings)
               ========================================================= */}
            {activeMenu === 'seasonStandings' && (
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
                        <h3 className="info-query__sub-title">
                          {selectedSeasonYear} 정규리그 최종 순위
                        </h3>
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

                      {filteredLeagueStandings.length === 0 ? (
                        <div className="info-query__status">순위 데이터가 아직 등록되지 않았습니다.</div>
                      ) : (
                        <div className="info-query__table-wrapper">
                          <table className="info-query__table">
                            <thead className="info-query__table-head">
                              <tr>
                                <th className="info-query__table-header info-query__table-header--center">
                                  순위
                                </th>
                                <th className="info-query__table-header">구단</th>
                                <th className="info-query__table-header info-query__table-header--center">
                                  경기
                                </th>
                                <th className="info-query__table-header info-query__table-header--center">
                                  승
                                </th>
                                <th className="info-query__table-header info-query__table-header--center">
                                  무
                                </th>
                                <th className="info-query__table-header info-query__table-header--center">
                                  패
                                </th>
                                <th className="info-query__table-header info-query__table-header--center">
                                  승률
                                </th>
                                <th className="info-query__table-header info-query__table-header--center">
                                  게임차
                                </th>
                                <th className="info-query__table-header info-query__table-header--center">
                                  연속
                                </th>
                              </tr>
                            </thead>
                            <tbody className="info-query__table-body">
                              {filteredLeagueStandings.map((s) => {
                                const club = clubsMap[s.club_id]
                                const isPlayoffSeed = s.rank <= 4
                                return (
                                  <tr key={s.id || s.club_id} className="info-query__table-row">
                                    <td className="info-query__table-cell info-query__table-cell--center info-query__table-cell--bold">
                                      {s.rank}
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--bold">
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
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--center">
                                      {s.games_played}
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--center">
                                      {s.wins}
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--center">
                                      {s.draws}
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--center">
                                      {s.losses}
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--center info-query__table-cell--bold">
                                      {formatPct(s.win_rate)}
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--center">
                                      {formatGb(s.games_back)}
                                    </td>
                                    <td className="info-query__table-cell info-query__table-cell--center">
                                      {formatStreak(s.streak)}
                                    </td>
                                  </tr>
                                )
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
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
            )}
          </main>
        </div>
      </div>
    </div>
  )
}
