import React, { useEffect, useMemo, useState } from 'react'
import { fetchInfoQueryPlayers, type PlayerListItem } from '../../api/infoQuery'
import type { Club } from '../../api/clubs'
import { formatPosition } from '../../constants/positions'
import { InfoQueryTable, type TableColumn } from '../../components/InfoQuery'
import { useSystemContext } from '../../context/SystemContext'

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

const SORT_OPTIONS = [
  { value: 'id', label: '기본 등록순' },
  { value: 'name', label: '이름순' },
  { value: 'age', label: '나이순' },
  { value: 'uniform_number', label: '배번순' },
  { value: 'height', label: '신장순' },
  { value: 'weight', label: '체중순' },
  { value: 'potential', label: '잠재력순' },
]

export interface PlayersTabProps {
  clubs: Club[]
  clubsMap: Record<number, Club>
  onSelectPlayer?: (player: PlayerListItem) => void
}

export const PlayersTab: React.FC<PlayersTabProps> = ({ clubs, clubsMap, onSelectPlayer }) => {
  const { currentDate } = useSystemContext()
  const [players, setPlayers] = useState<PlayerListItem[]>([])
  const [selectedClubId, setSelectedClubId] = useState<string>('all')
  const [selectedPosition, setSelectedPosition] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('id')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [searchInput, setSearchInput] = useState<string>('')
  const [appliedSearchName, setAppliedSearchName] = useState<string>('')
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [totalCount, setTotalCount] = useState<number>(0)
  const [totalPages, setTotalPages] = useState<number>(1)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

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
          sort_by: sortBy,
          order: sortOrder,
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
  }, [selectedClubId, selectedPosition, appliedSearchName, sortBy, sortOrder, currentPage])

  // 필터나 정렬 조건 변경 시 1페이지로 리셋
  useEffect(() => {
    setCurrentPage(1)
  }, [selectedClubId, selectedPosition, appliedSearchName, sortBy, sortOrder])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setAppliedSearchName(searchInput.trim())
  }

  const handlePlayerClick = (p: PlayerListItem) => {
    if (onSelectPlayer) {
      onSelectPlayer(p)
    } else {
      window.location.hash = `#info/players/${p.id}`
    }
  }

  const formatAge = (birthday?: string) => {
    if (!birthday) return '-'
    const birth = new Date(birthday)
    if (isNaN(birth.getTime())) return '-'
    const now = currentDate || new Date(1953, 0, 1)
    let age = now.getFullYear() - birth.getFullYear()
    const m = now.getMonth() - birth.getMonth()
    if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) {
      age--
    }
    return age >= 0 ? `만 ${age}세` : '-'
  }

  // 컬럼 정의
  const columns: TableColumn<PlayerListItem>[] = useMemo(
    () => [
      {
        key: 'uniform_number',
        header: '배번',
        align: 'center',
        bold: true,
        render: (p) => p.uniform_number || '-',
      },
      {
        key: 'name',
        header: '이름',
        bold: true,
        render: (p) => (
          <a
            href={`#info/players/${p.id}`}
            className="info-query__name-link"
            title={`${p.name} 선수 상세정보 조회`}
            onClick={(e) => {
              if (e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) {
                e.preventDefault()
                handlePlayerClick(p)
              }
            }}
          >
            {p.name}
          </a>
        ),
      },
      {
        key: 'club',
        header: '소속 구단',
        render: (p) => clubsMap[p.club_id]?.name_ko || clubsMap[p.club_id]?.name || '-',
      },
      {
        key: 'position',
        header: '포지션',
        align: 'center',
        render: (p) => <span className="info-query__badge">{formatPosition(p.position)}</span>,
      },
      {
        key: 'age',
        header: '나이',
        align: 'center',
        render: (p) => formatAge(p.birthday),
      },
      {
        key: 'physical',
        header: '신체조건',
        align: 'center',
        render: (p) => (p.height && p.weight ? `${p.height}cm / ${p.weight}kg` : '-'),
      },
      {
        key: 'origin',
        header: '연고지/출신교',
        render: (p) => {
          const regionName = p.region?.name_ko || p.region?.name
          const schoolName = p.high_school?.name_ko || p.high_school?.name
          return [regionName, schoolName].filter(Boolean).join(' · ') || '-'
        },
      },
    ],
    [clubsMap]
  )

  return (
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

          <div>
            <label htmlFor="sort-select" className="info-query__label">
              정렬:{' '}
            </label>
            <select
              id="sort-select"
              className="info-query__select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <select
              id="order-select"
              className="info-query__select"
              style={{ marginLeft: '4px' }}
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
            >
              <option value="asc">
                {sortBy === 'name'
                  ? '가나다순 (▲)'
                  : sortBy === 'age'
                    ? '어린순 (▲)'
                    : '오름차순 (▲)'}
              </option>
              <option value="desc">
                {sortBy === 'name'
                  ? '역순 (▼)'
                  : sortBy === 'age'
                    ? '많은순 (▼)'
                    : '내림차순 (▼)'}
              </option>
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
      ) : (
        <InfoQueryTable
          columns={columns}
          data={players}
          rowKey={(p) => p.id}
          emptyMessage="검색 결과가 없습니다."
          pagination={{
            currentPage,
            totalPages,
            onPageChange: setCurrentPage,
          }}
        />
      )}
    </>
  )
}

export default PlayersTab
