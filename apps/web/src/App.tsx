import './App.css'

function App() {
  return (
    <>
      <header className="header">
        <div className="header__logo">KROWN LEAGUE</div>
        <nav className="header__nav">
          <ul className="header__nav-list">
            <li className="header__nav-item">
              <a className="header__nav-link" href="#home">Home</a>
            </li>
            <li className="header__nav-item">
              <a className="header__nav-link" href="#schedule">Schedule</a>
            </li>
            <li className="header__nav-item">
              <a className="header__nav-link" href="#teams">Teams</a>
            </li>
            <li className="header__nav-item">
              <a className="header__nav-link" href="#stats">Stats</a>
            </li>
            <li className="header__nav-item">
              <a className="header__nav-link" href="#news">News</a>
            </li>
          </ul>
        </nav>
      </header>

      <section className="hero-banner">
        <div className="hero-banner__content">
          <h1 className="hero-banner__title">Krown League Baseball</h1>
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
  )
}

export default App

