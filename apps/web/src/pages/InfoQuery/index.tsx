import { useEffect, useMemo, useState } from 'react'
import { getClubs, type Club } from '../../api/clubs'
import { getStandingSeasons } from '../../api/standings'
import { getSystemInfo } from '../../api/system'
import PlayersTab from './PlayersTab'
import SeasonStandingsTab from './SeasonStandingsTab'
import PlayerDetail from './PlayerDetail'
import './index.css'

export type InfoQueryMenuType = 'players' | 'seasonStandings'

export interface ParsedInfoRoute {
  menu: InfoQueryMenuType
  playerId: number | null
}

export function parseInfoRoute(): ParsedInfoRoute {
  const hash = window.location.hash || '#info'

  // 1. 경로 파라미터 매칭: #info/players/123 또는 #info/player/123
  const pathMatch = hash.match(/^#info\/players?\/(\d+)/i)
  if (pathMatch) {
    return { menu: 'players', playerId: Number(pathMatch[1]) }
  }

  // 2. 쿼리 파라미터 매칭: #info?playerId=123 등
  if (hash.includes('?')) {
    const q = hash.split('?')[1]
    const params = new URLSearchParams(q)
    const pId = params.get('playerId') || params.get('id')
    const tab = params.get('tab')
    const menu: InfoQueryMenuType =
      tab === 'seasonStandings' || tab === 'standings' ? 'seasonStandings' : 'players'
    return { menu, playerId: pId ? Number(pId) : null }
  }

  // 3. 시즌 순위 경로: #info/standings
  if (hash.startsWith('#info/standings') || hash.startsWith('#info/seasonStandings')) {
    return { menu: 'seasonStandings', playerId: null }
  }

  return { menu: 'players', playerId: null }
}

export default function InfoQuery() {
  // Hash 경로 기반 라우트 상태
  const [route, setRoute] = useState<ParsedInfoRoute>(() => parseInfoRoute())

  // Shared state: Clubs & Available Seasons
  const [clubs, setClubs] = useState<Club[]>([])
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([])
  const [initialSeasonYear, setInitialSeasonYear] = useState<number | null>(null)

  // 1. hashchange 이벤트 리스너로 브라우저 새로고침/앞/뒤로가기 동기화
  useEffect(() => {
    const handleHashChange = () => {
      setRoute(parseInfoRoute())
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  // 2. Initial System Info, Clubs & Available Seasons load
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
            setInitialSeasonYear(seasonList[0])
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

  // Club ID -> Club Object mapping
  const clubsMap = useMemo(() => {
    const map: Record<number, Club> = {}
    clubs.forEach((club) => {
      map[club.id] = club
    })
    return map
  }, [clubs])

  const handleNavigateMenu = (menu: InfoQueryMenuType) => {
    if (menu === 'players') {
      window.location.hash = '#info/players'
    } else {
      window.location.hash = '#info/standings'
    }
  }

  const handleBackToPlayerList = () => {
    if (window.history.length > 1) {
      window.history.back()
    } else {
      window.location.hash = '#info/players'
    }
  }

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
                      route.menu === 'players' ? 'info-query__sidebar-link--active' : ''
                    }`}
                    onClick={() => handleNavigateMenu('players')}
                  >
                    선수 조회
                  </span>
                </li>
                <li className="info-query__sidebar-item">
                  <span
                    className={`info-query__sidebar-link ${
                      route.menu === 'seasonStandings' ? 'info-query__sidebar-link--active' : ''
                    }`}
                    onClick={() => handleNavigateMenu('seasonStandings')}
                  >
                    시즌 최종 순위
                  </span>
                </li>
              </ul>
            </nav>
          </aside>

          {/* Main Content Area */}
          <main className="info-query__main">
            {route.menu === 'players' && (
              <>
                <div style={{ display: route.playerId ? 'none' : 'block' }}>
                  <PlayersTab
                    clubs={clubs}
                    clubsMap={clubsMap}
                    onSelectPlayer={(p) => {
                      window.location.hash = `#info/players/${p.id}`
                    }}
                  />
                </div>
                {route.playerId && (
                  <PlayerDetail
                    playerId={route.playerId}
                    clubsMap={clubsMap}
                    onBack={handleBackToPlayerList}
                  />
                )}
              </>
            )}

            {route.menu === 'seasonStandings' && (
              <SeasonStandingsTab
                clubsMap={clubsMap}
                availableSeasons={availableSeasons}
                initialSeasonYear={initialSeasonYear}
              />
            )}
          </main>
        </div>
      </div>
    </div>
  )
}
