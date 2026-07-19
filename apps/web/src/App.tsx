import { useState, useEffect } from 'react'
import './App.css'
import Intro from './pages/Intro'
import LeagueShortcut from './pages/LeagueShortcut'
import AppSeasonStandingSection from './pages/AppSeasonStandingSection'
import AppNewsSection from './pages/AppNewsSection'
import AppScheduleSection from './pages/AppScheduleSection'
import { getSystemInfo } from './api/system'

function App() {
  const [currentHash, setCurrentHash] = useState(window.location.hash || '#home')
  const [matchDate, setMatchDate] = useState<Date>(new Date("2026-07-17"))

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [seasonYear, setSeasonYear] = useState<number | null>(null)
  const [isSeasonYearLoaded, setIsSeasonYearLoaded] = useState(false)

  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [currentHash])

  useEffect(() => {
    getSystemInfo()
      .then(info => {
        setSeasonYear(info.season_year)
        const [y, m, d] = info.current_date.split('-')
        setMatchDate(new Date(Number(y), Number(m) - 1, Number(d)))
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

  const handleDateChange = (days: number) => {
    const nextDate = new Date(matchDate)
    nextDate.setDate(nextDate.getDate() + days)
    setMatchDate(nextDate)
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
              <a className={`header__nav-link ${currentHash === '#community' ? 'header__nav-link--active' : ''}`} href="#community">커뮤니티</a>
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
      ) : ['#schedule', '#live', '#community', '#archive'].includes(currentHash) ? (
        <div className="empty-page" />
      ) : (
        <>
          <AppSeasonStandingSection
            matchDate={matchDate}
            seasonYear={seasonYear}
            isSeasonYearLoaded={isSeasonYearLoaded}
          />
          <AppNewsSection />
          <AppScheduleSection
            matchDate={matchDate}
            onDateChange={handleDateChange}
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
              Krown League Baseball은 대한민국 야구의 새로운 역사와 혁신을 만들어갑니다.
            </p>
          </div>
          <div className="footer__links-section">
            <div className="footer__link-group">
              <h4 className="footer__link-title">League</h4>
              <a href="#intro" className="footer__link">소개</a>
              <a href="#schedule" className="footer__link">일정 진행</a>
              <a href="#league-shortcut" className="footer__link">리그 및 구단</a>
            </div>
            <div className="footer__link-group">
              <h4 className="footer__link-title">Support</h4>
              <a href="#live" className="footer__link">LIVE</a>
              <a href="#community" className="footer__link">커뮤니티</a>
              <a href="#archive" className="footer__link">자료실</a>
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
