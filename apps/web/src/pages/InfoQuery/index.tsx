import { useEffect, useMemo, useState } from 'react'
import { getClubs, type Club } from '../../api/clubs'
import { getStandingSeasons } from '../../api/standings'
import { getSystemInfo } from '../../api/system'
import PlayersTab from './PlayersTab'
import SeasonStandingsTab from './SeasonStandingsTab'
import './index.css'

export type InfoQueryMenuType = 'players' | 'seasonStandings'

export default function InfoQuery() {
  // Sidebar tab state
  const [activeMenu, setActiveMenu] = useState<InfoQueryMenuType>('players')

  // Shared state: Clubs & Available Seasons
  const [clubs, setClubs] = useState<Club[]>([])
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([])
  const [initialSeasonYear, setInitialSeasonYear] = useState<number | null>(null)

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
            {activeMenu === 'players' && <PlayersTab clubs={clubs} clubsMap={clubsMap} />}

            {activeMenu === 'seasonStandings' && (
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
