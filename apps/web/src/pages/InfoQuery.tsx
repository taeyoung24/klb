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

  // 1. Fetch Clubs once for dropdown filter
  useEffect(() => {
    let isMounted = true
    getClubs()
      .then((clubsData) => {
        if (isMounted) {
          setClubs(clubsData)
        }
      })
      .catch((err) => {
        console.error('Failed to fetch clubs:', err)
      })
    return () => {
      isMounted = false
    }
  }, [])

  // 2. Fetch Players with DB querying and pagination via info-query API
  useEffect(() => {
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
  }, [selectedClubId, selectedPosition, appliedSearchName, currentPage])

  // Reset page when filter criteria change
  useEffect(() => {
    setCurrentPage(1)
  }, [selectedClubId, selectedPosition, appliedSearchName])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setAppliedSearchName(searchInput.trim())
  }

  // Club ID -> Club Name mapping
  const clubMap = useMemo(() => {
    const map = new Map<number, string>()
    clubs.forEach((club) => {
      map.set(club.id, club.name_ko || club.name)
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

  return (
    <div className="info-query">
      <div className="info-query__container">
        <header className="info-query__header">
          <h1 className="info-query__title">정보 조회</h1>
          <p className="info-query__description">
            KLB 리그의 등록 선수 기본 정보 및 관련 주요 데이터를 목록으로 조회합니다.
          </p>
        </header>

        {/* Filter & Search Controls */}
        <div className="info-query__filter-bar">
          <div className="info-query__filter-group">
            <div>
              <label htmlFor="club-select" className="info-query__label">구단: </label>
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
              <label htmlFor="position-select" className="info-query__label">포지션: </label>
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

            <form className="info-query__search-form" onSubmit={handleSearchSubmit}>
              <label htmlFor="player-search" className="info-query__label">선수명: </label>
              <input
                id="player-search"
                type="text"
                className="info-query__input"
                placeholder="이름 검색..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
              <button type="submit" className="info-query__button">
                검색
              </button>
            </form>
          </div>

          <div className="info-query__count">
            총 {totalCount}명 검색됨 ({validCurrentPage} / {totalPages} 페이지)
          </div>
        </div>

        {/* Content State Handling */}
        {isLoading ? (
          <div className="info-query__status">선수 목록을 불러오는 중입니다...</div>
        ) : error ? (
          <div className="info-query__status info-query__status--error">{error}</div>
        ) : players.length === 0 ? (
          <div className="info-query__status">조건에 일치하는 선수가 없습니다.</div>
        ) : (
          <>
            <div className="info-query__table-wrapper">
              <table className="info-query__table">
                <thead className="info-query__table-head">
                  <tr>
                    <th className="info-query__table-header info-query__table-header--center">ID</th>
                    <th className="info-query__table-header">이름</th>
                    <th className="info-query__table-header">구단</th>
                    <th className="info-query__table-header info-query__table-header--center">등번호</th>
                    <th className="info-query__table-header">포지션</th>
                    <th className="info-query__table-header">신장 / 체중</th>
                    <th className="info-query__table-header">출신 지역</th>
                    <th className="info-query__table-header">출신 고교</th>
                  </tr>
                </thead>
                <tbody className="info-query__table-body">
                  {players.map((player) => (
                    <tr key={player.id} className="info-query__table-row">
                      <td className="info-query__table-cell info-query__table-cell--center">
                        {player.id}
                      </td>
                      <td className="info-query__table-cell info-query__table-cell--bold">
                        {player.name}
                      </td>
                      <td className="info-query__table-cell">
                        {clubMap.get(player.club_id) || `구단 #${player.club_id}`}
                      </td>
                      <td className="info-query__table-cell info-query__table-cell--center">
                        {player.uniform_number ? `#${player.uniform_number}` : '-'}
                      </td>
                      <td className="info-query__table-cell">
                        {player.position ? (
                          <span className="info-query__badge">{formatPosition(player.position)}</span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="info-query__table-cell">
                        {player.height || player.weight
                          ? `${player.height ? `${player.height}cm` : '-'} / ${player.weight ? `${player.weight}kg` : '-'}`
                          : '-'}
                      </td>
                      <td className="info-query__table-cell">
                        {player.region?.name_ko || player.region?.name || '-'}
                      </td>
                      <td className="info-query__table-cell">
                        {player.high_school?.name_ko || player.high_school?.name || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="info-query__pagination">
                {/*더미 이전 (10페이지 이동)*/}
                <button
                  type="button"
                  className="info-query__pagination-button"
                  title="10페이지 이전"
                  disabled={validCurrentPage <= 1}
                  onClick={() => handlePageChange(validCurrentPage - 10)}
                >
                  <FiChevronsLeft size={16} />
                </button>

                {/*이전 1페이지*/}
                <button
                  type="button"
                  className="info-query__pagination-button"
                  title="이전 페이지"
                  disabled={validCurrentPage <= 1}
                  onClick={() => handlePageChange(validCurrentPage - 1)}
                >
                  <FiChevronLeft size={16} />
                </button>

                {/*페이지 번호 & 생략 표시 (10 슬롯 고정)*/}
                {pageNumbers.map((item, index) => {
                  if (item === '...') {
                    return (
                      <span
                        key={`ellipsis-${index}`}
                        className="info-query__pagination-ellipsis"
                      >
                        <FiMoreHorizontal size={16} />
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

                {/*다음 1페이지*/}
                <button
                  type="button"
                  className="info-query__pagination-button"
                  title="다음 페이지"
                  disabled={validCurrentPage >= totalPages}
                  onClick={() => handlePageChange(validCurrentPage + 1)}
                >
                  <FiChevronRight size={16} />
                </button>

                {/*더미 다음 (10페이지 이동)*/}
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
      </div>
    </div>
  )
}
