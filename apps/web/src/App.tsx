import { useEffect, useState } from 'react'
import './App.css'
import AppNewsSection from './pages/AppNewsSection'
import AppScheduleSection from './pages/AppScheduleSection'
import AppSeasonStandingSection from './pages/AppSeasonStandingSection'
import Intro from './pages/Intro'
import LeagueShortcut from './pages/LeagueShortcut'
import Live from './pages/Live'
import MatchDetail from './pages/MatchDetail'
import Schedule from './pages/Schedule'
import Wiki from './pages/Wiki'
import InfoQuery from './pages/InfoQuery'
import AzaleaLeagueApp from './pages/league-al/App'
import CamelliaLeagueApp from './pages/league-cl/App'
import GentianaLeagueApp from './pages/league-gl/App'
import MagnoliaLeagueApp from './pages/league-ml/App'

import WorldMap from './pages/world-map'

import { useSystemContext } from './context/SystemContext'

function App() {
  const {
    seasonYear,
    currentDate: latestDate,
    scheduleDate,
    isLoaded: isSeasonYearLoaded,
    handleScheduleDateChange,
  } = useSystemContext()

  const [currentHash, setCurrentHash] = useState(window.location.hash || '#home')
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  useEffect(() => {
    setIsMobileMenuOpen(false)
    window.scrollTo(0, 0)
  }, [currentHash])

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentHash(window.location.hash || '#home')
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  if (currentHash === '#world-map') {
    return <WorldMap />
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
        <a
          href="#home"
          className="header__logo"
          onClick={(e) => {
            if (window.location.hash === '#home' || window.location.hash === '') {
              e.preventDefault()
              window.location.reload()
            } else {
              window.location.hash = '#home'
            }
          }}
        >
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
              <a className={`header__nav-link ${currentHash.startsWith('#wiki') ? 'header__nav-link--active' : ''}`} href="#wiki">위키</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash.startsWith('#info') ? 'header__nav-link--active' : ''}`} href="#info">정보 조회</a>
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
      ) : currentHash.startsWith('#match-detail') ? (
        <MatchDetail />
      ) : currentHash.startsWith('#wiki') ? (
        <Wiki />
      ) : currentHash.startsWith('#info') ? (
        <InfoQuery />
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
            <a
              href="#home"
              className="footer__logo"
              onClick={(e) => {
                if (window.location.hash === '#home' || window.location.hash === '') {
                  e.preventDefault()
                  window.location.reload()
                } else {
                  window.location.hash = '#home'
                }
              }}
            >
              <img className="footer__logo-img" src="/klb-logo-256.svg" alt="KLB Logo" />
              <span className="footer__logo-text">KLB</span>
            </a>
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
              <a href="#wiki" className="footer__link">위키</a>
              <a href="#info" className="footer__link">정보 조회</a>
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
