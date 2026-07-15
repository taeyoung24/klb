import { useState, useEffect } from 'react'
import './App.css'
import Intro from './pages/Intro'

function App() {
  const [currentHash, setCurrentHash] = useState(window.location.hash || '#home')

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentHash(window.location.hash || '#home')
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  return (
    <>
      <header className="header">
        <a href="#home" className="header__logo">
          <img className="header__logo-img" src="/klb-logo-256.svg" alt="KLB Logo" />
          <span className="header__logo-text">KLB</span>
        </a>
        <nav className="header__nav">
          <ul className="header__nav-list">
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#intro' ? 'header__nav-link--active' : ''}`} href="#intro">소개</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#schedule' ? 'header__nav-link--active' : ''}`} href="#schedule">통합 일정</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#teams' ? 'header__nav-link--active' : ''}`} href="#teams">리그 구성</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#live' ? 'header__nav-link--active' : ''}`} href="#live">LIVE</a>
            </li>
            <li className="header__nav-item">
              <a className={`header__nav-link ${currentHash === '#community' ? 'header__nav-link--active' : ''}`} href="#community">커뮤니티</a>
            </li>
          </ul>
        </nav>
      </header>

      {currentHash === '#intro' ? (
        <Intro />
      ) : ['#schedule', '#teams', '#live', '#community'].includes(currentHash) ? (
        <div className="empty-page" />
      ) : (
        <>
          <section className="hero-banner">
            <div className="hero-banner__content">
              <div className="hero-banner__quote">
                <h1 className="hero-banner__slogan">Dream Yours</h1>
                <p className="hero-banner__subtext">당신의 꿈으로 우리의 역사가 탄생합니다.</p>
              </div>
            </div>
          </section>

          <section className="section section--light">
            <div className="section__container">
              <h2 className="section__title">Krown League Overview</h2>
              <p className="section__paragraph">
                Welcome to the official home of Krown League Baseball. We are committed to
                delivering the most competitive and exciting baseball experience in the region.
                With historic rivalries and outstanding sportsmanship, the Krown League continues
                to push the boundaries of modern sports entertainment.
              </p>
            </div>
          </section>

          <section className="section section--dark">
            <div className="section__container">
              <h2 className="section__title">Upcoming Seasons & Events</h2>
              <p className="section__paragraph">
                The new season of Krown League Baseball is just around the corner. Get ready
                to support your favorite teams, track player achievements, and secure your tickets
                early. Detailed schedules and roster updates will be posted soon on our dedicated
                pages. Keep an eye out for official press releases.
              </p>
            </div>
          </section>
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
              <a href="#teams" className="footer__link">리그 및 구단</a>
            </div>
            <div className="footer__link-group">
              <h4 className="footer__link-title">Support</h4>
              <a href="#live" className="footer__link">LIVE</a>
              <a href="#community" className="footer__link">커뮤니티</a>
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

