import { useEffect, useState } from 'react'
import './App.css'
import { getSystemInfo } from './api/system'
import AppNewsSection from './pages/AppNewsSection'
import AppScheduleSection from './pages/AppScheduleSection'
import AppSeasonStandingSection from './pages/AppSeasonStandingSection'
import Archive from './pages/Archive'
import Records from './pages/Records'
import Schedule from './pages/Schedule'
import Live from './pages/Live'
import Intro from './pages/Intro'
import LeagueShortcut from './pages/LeagueShortcut'
import MatchDetail from './pages/MatchDetail'
import AzaleaLeagueApp from './pages/league-al/App'
import CamelliaLeagueApp from './pages/league-cl/App'
import GentianaLeagueApp from './pages/league-gl/App'
import MagnoliaLeagueApp from './pages/league-ml/App'

function App() {
  const [currentHash, setCurrentHash] = useState(window.location.hash || '#home')
  const [latestDate, setLatestDate] = useState<Date>(new Date("2026-07-17"))
  const [scheduleDate, setScheduleDate] = useState<Date>(new Date("2026-07-17"))

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [seasonYear, setSeasonYear] = useState<number | null>(null)
  const [isSeasonYearLoaded, setIsSeasonYearLoaded] = useState(false)

  useEffect(() => {
    setIsMobileMenuOpen(false)
    window.scrollTo(0, 0)
  }, [currentHash])

  useEffect(() => {
    getSystemInfo()
      .then(info => {
        setSeasonYear(info.season_year)
        const [y, m, d] = info.current_date.split('-')
        const systemDate = new Date(Number(y), Number(m) - 1, Number(d))
        setLatestDate(systemDate)
        setScheduleDate(systemDate)
        setIsSeasonYearLoaded(true)
      })
      .catch(e => {
        console.error("Failed to fetch system info", e)
        setSeasonYear(2026)
        setIsSeasonYearLoaded(true)
      })
  }, [])

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentHash(window.location.hash || '#home')
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  const handleScheduleDateChange = (days: number) => {
    const nextDate = new Date(scheduleDate)
    nextDate.setDate(nextDate.getDate() + days)
    setScheduleDate(nextDate)
  }

  if (currentHash === '#league-al') {
    return <AzaleaLeagueApp />
  }
  if (currentHash === '#league-cl') {
    return <CamelliaLeagueApp />
  }
  if (currentHash === '#league-gl') {
    return <GentianaLeagueApp />
  }
  if (currentHash === '#league-ml') {
    return <MagnoliaLeagueApp />
  }

  return (
    <>
      <header className="header">
        <a href="#home" className="header__logo">
          <img className="header__logo-img" src="/klb-logo-256.svg" alt="KLB Logo" />
          <span className="header__logo-text">KLB</span>
        </a>
        {/* 모바일 메뉴바 버튼 */}
        <button
          className={`header__menu-btn ${isMobileMenuOpen ? 'header__menu-btn--open' : ''}`}
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle menu"
        >
          <span className="header__menu-icon"></span>
        </button>

        <nav className={`header__nav ${isMobileMenuOpen ? 'header__nav--open' : ''}`}>
          <ul className="header__nav-list">
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#intro' ? 'header__nav-link--active' : ''}`} href="#intro">소개</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#schedule' ? 'header__nav-link--active' : ''}`} href="#schedule">통합 일정</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#league-shortcut' ? 'header__nav-link--active' : ''}`} href="#league-shortcut">리그 바로가기</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#records' ? 'header__nav-link--active' : ''}`} href="#records">기록실</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#archive' ? 'header__nav-link--active' : ''}`} href="#archive">자료실</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link header__nav-link--live ${currentHash === '#live' ? 'header__nav-link--active' : ''}`} href="#live">LIVE</a>
            </li>
          </ul>
        </nav>
      </header>

      {currentHash === '#intro' ? (
        <Intro />
      ) : currentHash === '#league-shortcut' ? (
        <LeagueShortcut />
      ) : currentHash === '#match-detail' ? (
        <MatchDetail />
      ) : currentHash === '#archive' ? (
        <Archive />
      ) : currentHash === '#records' ? (
        <Records />
      ) : currentHash === '#schedule' ? (
        <Schedule />
      ) : currentHash === '#live' ? (
        <Live />
      ) : (
        <>
          <AppSeasonStandingSection
            matchDate={latestDate}
            seasonYear={seasonYear}
            isSeasonYearLoaded={isSeasonYearLoaded}
          />
          <AppNewsSection />
          <AppScheduleSection
            matchDate={scheduleDate}
            onDateChange={handleScheduleDateChange}
          />
        </>
      )}

      <footer className="footer">
        <div className="footer__container">
          <div className="footer__info">
            <div className="footer__logo">
              <img className="footer__logo-img" src="/klb-logo-256.svg" alt="KLB Logo" />
              <span className="footer__logo-text">KLB</span>
            </div>
            <p className="footer__desc">
              Krown League Baseball은 여러분의 역사를 간직합니다.
            </p>
          </div>
          <div className="footer__links-section">
            <div className="footer__link-group">
              <h4 className="footer__link-title">League</h4>
              <a href="#intro" className="footer__link">소개</a>
              <a href="#schedule" className="footer__link">통합 일정</a>
              <a href="#league-shortcut" className="footer__link">리그 바로가기</a>
            </div>
            <div className="footer__link-group">
              <h4 className="footer__link-title">Support</h4>
              <a href="#records" className="footer__link">기록실</a>
              <a href="#archive" className="footer__link">자료실</a>
              <a href="#live" className="footer__link">LIVE</a>
              <a href="#terms" className="footer__link">이용약관</a>
            </div>
          </div>
        </div>
        <div className="footer__bottom">
          <p className="footer__copyright">
            © 2026 Krown League Baseball. All rights reserved.
          </p>
        </div>
      </footer>
    </>
  )
}

export default App
