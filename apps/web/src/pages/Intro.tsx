import { useState, useRef, useEffect } from 'react';
import './Intro.css';
import mainBannerImg from '../assets/main_banner.jpeg';

export default function Intro() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [videoOpacity, setVideoOpacity] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isTextVisible, setIsTextVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const viewportHeight = window.innerHeight;

      // 부모 컨테이너(.intro-hero)의 총 높이에서 뷰포트 높이를 뺀 것이 스크롤 가능한 최대 고정 범위입니다.
      const totalHeight = rect.height;
      const maxScroll = totalHeight - viewportHeight;

      // rect.top이 0 이하가 되어 화면 상단에 달라붙는 순간부터 고정이 시작됩니다.
      const scrollDist = -rect.top;

      let progress = 0;
      if (rect.top <= 0 && maxScroll > 0) {
        progress = scrollDist / maxScroll;
      }

      progress = Math.max(0, Math.min(1, progress));
      setScrollProgress(progress);

      // 섹션이 뷰포트 내부로 100px 진입하는 시점에 일회성으로 텍스트 페이드인 활성화
      if (rect.top < viewportHeight - 100) {
        setIsTextVisible(true);
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (!video) return;

    const currentTime = video.currentTime;
    const duration = video.duration;

    if (!duration || isNaN(duration)) return;

    const fadeDuration = 1.0; // 페이드 아웃/인 시간 (1초)

    if (currentTime < fadeDuration) {
      // 시작 시 페이드 인
      setVideoOpacity(currentTime / fadeDuration);
    } else if (currentTime > duration - fadeDuration) {
      // 끝날 때 페이드 아웃
      setVideoOpacity((duration - currentTime) / fadeDuration);
    } else {
      setVideoOpacity(1);
    }
  };

  const handleLoadedMetadata = () => {
    setVideoOpacity(0);
  };

  // 스크롤 진행에 따른 스케일 (0.01에서 가속되어 존 크기인 6.5배까지 극대화)
  const ballScale = 0.01 + Math.pow(scrollProgress, 1.5) * 6.5;

  // 시작(0~15%)과 끝(80~100%) 구간의 페이드인 / 페이드아웃 처리
  let ballOpacity = 1;
  if (scrollProgress < 0.15) {
    ballOpacity = scrollProgress / 0.15; // 0 -> 1 페이드인
  } else if (scrollProgress > 0.8) {
    ballOpacity = (1 - scrollProgress) / 0.2; // 1 -> 0 페이드아웃
  }
  ballOpacity = Math.max(0, Math.min(1, ballOpacity));

  // 변화구 궤적 수식 계산 (시작점 상향 및 백도어 슬라이더 연출)
  // 시작 위치: 중앙 최상단 (50%, 15%) -> 우측 존 바깥 (약 88%)까지 휘어나갔다가 -> 급격히 꺾여 좌측 하단 보더라인 (15%)을 통과하는 마구 궤적
  const ballLeft = 50 - scrollProgress * 35 + Math.sin(scrollProgress * Math.PI) * 55;
  const ballTop = 15 + scrollProgress * 53 + Math.sin(scrollProgress * Math.PI) * -8;

  // 스크롤 진행률에 기반한 4단계 야구공 이미지 회전 프레임 인덱스 (1 ~ 4)
  const ballImageIndex = Math.floor(scrollProgress * 20) % 4;
  const ballSrc = `/assets/ball_${ballImageIndex + 1}.png`;

  // 100마일 스트라이크 판정 마커 페이드인 & 축소 연착륙 계산
  // 공이 우측 보더라인(84%)을 관통하여 지나가는 시점인 스크롤 50% ~ 70% 구간에서 등장하도록 변경
  const markerProgress = scrollProgress < 0.5
    ? 0
    : Math.min(1, (scrollProgress - 0.5) / 0.2);
  const markerOpacity = markerProgress;
  const markerScale = 1.4 - markerProgress * 0.4; // 1.4배 크기에서 1.0배 크기로 서서히 축소하며 등장

  return (
    <div className="intro">
      <section className="hero-banner">
        <video
          ref={videoRef}
          className="hero-banner__video"
          autoPlay
          loop
          muted
          playsInline
          poster={mainBannerImg}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          style={{ opacity: videoOpacity }}
        >
          <source src="/videos/main_banner.mp4" type="video/mp4" />
          <img
            src={mainBannerImg}
            alt="Krown League Main Banner"
            className="hero-banner__fallback-img"
          />
        </video>
        <div className="hero-banner__overlay"></div>
        <div className="hero-banner__content">
          <div className="hero-banner__quote">
            <h1 className="hero-banner__slogan">Dream Yours</h1>
            <p className="hero-banner__subtext">당신의 꿈으로 우리의 역사가 탄생합니다.</p>
          </div>
        </div>
      </section>

      <section ref={containerRef} className="intro-hero">
        <div className="intro-hero__container">
          <span className={`intro-hero__tag ${isTextVisible ? 'intro-hero__tag--visible' : ''}`}>The Infinity Stories</span>
          <h2 className={`intro-hero__title ${isTextVisible ? 'intro-hero__title--visible' : ''}`}>여기, 끝나지 않는 이야기.</h2>
          <p className={`intro-hero__desc ${isTextVisible ? 'intro-hero__desc--visible' : ''}`}>
            우리 모두를 몰입시킬 압도적 세계가 이곳에서 펼쳐집니다.
          </p>

          <div className="strike-zone">
            <div className="strike-zone__connector"></div>

            <div className="strike-zone__display">
              <div className="strike-zone__board">
                {/* 격자 뒤에서 움직이는 야구공 */}
                <div
                  className="strike-zone__ball-scroll"
                  style={{
                    top: `${ballTop}%`,
                    left: `${ballLeft}%`,
                    transform: `translate(-50%, -50%) scale(${ballScale})`,
                    opacity: ballOpacity,
                  }}
                >
                  <img
                    src={ballSrc}
                    alt="Baseball Pitch"
                    className="strike-zone__ball-scroll-img"
                    onError={(e) => {
                      // 에셋 이미지가 아직 업로드되지 않았을 때 깨진 이미지 마크 노출을 방지하기 위함
                      (e.target as HTMLImageElement).style.opacity = '0';
                    }}
                  />
                </div>

                <div className="strike-zone__grid">
                  <div className="strike-zone__cell">1</div>
                  <div className="strike-zone__cell">2</div>
                  <div className="strike-zone__cell">3</div>
                  <div className="strike-zone__cell">4</div>
                  <div className="strike-zone__cell">5</div>
                  <div className="strike-zone__cell">6</div>
                  <div className="strike-zone__cell">7</div>
                  <div className="strike-zone__cell">8</div>
                  <div className="strike-zone__cell">9</div>
                </div>

                <div className="strike-zone__plate"></div>

                {/* 100마일 스트라이크 판정 표시 마커 (우측 보더라인 통과점인 top: 36%, left: 84% 지점) */}
                <div
                  className="strike-zone__marker"
                  style={{
                    top: '36%',
                    left: '84%',
                    transform: `translate(-50%, -50%) scale(${markerScale})`,
                    opacity: markerOpacity,
                  }}
                >
                  <div className="strike-zone__marker-circle">
                    <span className="strike-zone__marker-text">100</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="intro-legacy">
        <div className="intro-legacy__container">
          <span className="intro-legacy__tag">The Historical Legacy</span>
          <h2 className="intro-legacy__title">역사가 깃든 4대리그</h2>
          <p className="intro-legacy__desc">
            수많은 지역, 대륙 간 얽히고 얽힌 이야기가 있습니다.
          </p>
          <div className="intro-legacy__map-placeholder">
            <span className="intro-legacy__map-placeholder-text">MAP AREA (준비 중)</span>
          </div>
        </div>
      </section>

      <section className="intro-journey">
        <div className="intro-journey__container">
          <span className="intro-journey__tag">The Journey</span>
          <h2 className="intro-journey__title">최후의 영광까지.</h2>
          <p className="intro-journey__desc">
            Krown Series 최후의 영광까지 여정을 함께하세요.
          </p>

          <div className="journey-flow">
            <div className="journey-flow__line"></div>

            {/* STEP 1 */}
            <div className="journey-step">
              <div className="journey-step__badge">1</div>
              <div className="journey-step__content">
                <h3 className="journey-step__title">정규 시즌 & 진출 자격</h3>
                <p className="journey-step__description">
                  Azalea, Camellia, Gentiana, Magnolia 메이저 4대 리그에서 혹독한 144경기 레이스를 치릅니다. 각 리그의 최상위 1위부터 4위 구단만이 포스트시즌 진입 티켓을 거머쥡니다.
                </p>
                <div className="journey-step__visual">
                  <div className="journey-step__league-grid">
                    <div className="journey-step__league-row">
                      <span className="journey-step__league-label">AZALEA (AL)</span>
                      <div className="journey-step__team-blocks">
                        <div className="journey-step__team-block">#1</div>
                        <div className="journey-step__team-block">#2</div>
                        <div className="journey-step__team-block">#3</div>
                        <div className="journey-step__team-block">#4</div>
                      </div>
                    </div>
                    <div className="journey-step__league-row">
                      <span className="journey-step__league-label">CAMELLIA (CL)</span>
                      <div className="journey-step__team-blocks">
                        <div className="journey-step__team-block">#1</div>
                        <div className="journey-step__team-block">#2</div>
                        <div className="journey-step__team-block">#3</div>
                        <div className="journey-step__team-block">#4</div>
                      </div>
                    </div>
                    <div className="journey-step__league-row">
                      <span className="journey-step__league-label">GENTIANA (GL)</span>
                      <div className="journey-step__team-blocks">
                        <div className="journey-step__team-block">#1</div>
                        <div className="journey-step__team-block">#2</div>
                        <div className="journey-step__team-block">#3</div>
                        <div className="journey-step__team-block">#4</div>
                      </div>
                    </div>
                    <div className="journey-step__league-row">
                      <span className="journey-step__league-label">MAGNOLIA (ML)</span>
                      <div className="journey-step__team-blocks">
                        <div className="journey-step__team-block">#1</div>
                        <div className="journey-step__team-block">#2</div>
                        <div className="journey-step__team-block">#3</div>
                        <div className="journey-step__team-block">#4</div>
                      </div>
                    </div>
                  </div>
                  <div className="journey-step__total-badge" style={{ marginTop: '16px' }}>총 16개 정예 구단 포스트시즌 진출</div>
                </div>
              </div>
            </div>

            {/* STEP 2 */}
            <div className="journey-step">
              <div className="journey-step__badge">2</div>
              <div className="journey-step__content">
                <h3 className="journey-step__title">크라운 정예리그 (Krown Elite League)</h3>
                <p className="journey-step__description">
                  이전 순위의 혜택을 지우고, 완전히 동등한 출발선에서 시작되는 풀리그 관문입니다. 모든 진출 구단이 홈/원정 1경기씩 치르는 더블 라운드 로빈(팀당 30경기)으로 기계적 공정성을 시험합니다.
                </p>
                <div className="journey-step__venue-info">
                  <span className="journey-step__venue-title">개최 리그 지역 선정 규정 (이동거리 완화)</span>
                  <ul className="journey-step__venue-list">
                    <li>1. 디펜딩 챔피언이 정예리그에 진출했을 경우 디펜딩 챔피언이 속한 리그 구장을 사용</li>
                    <li>2. 디펜딩 챔피언이 없거나(초대 시즌) 정예리그 미진출 시, 당해 정예리그 진출팀 4개 팀의 정규시즌 승률 합(평균)이 가장 높은 리그</li>
                    <li>3. 승률 합 동률 발생 시, 해당 동률 리그들의 1시드부터 시작하여 순차적으로 더 높은 승률인 팀의 리그</li>
                    <li>4. 4시드까지 모두 승률이 동일할 경우에는 무작위(Random) 선정</li>
                  </ul>
                </div>
                <div className="journey-step__visual">
                  <div className="journey-step__survival-grid">
                    <div className="journey-step__survival-row journey-step__survival-row--survived">
                      <span className="journey-step__survival-status">SURVIVED (상위 8개 팀 녹아웃 진출)</span>
                      <div className="journey-step__survival-blocks">
                        <div className="journey-step__survival-block">#1</div>
                        <div className="journey-step__survival-block">#2</div>
                        <div className="journey-step__survival-block">#3</div>
                        <div className="journey-step__survival-block">#4</div>
                        <div className="journey-step__survival-block">#5</div>
                        <div className="journey-step__survival-block">#6</div>
                        <div className="journey-step__survival-block">#7</div>
                        <div className="journey-step__survival-block">#8</div>
                      </div>
                    </div>
                    <div className="journey-step__survival-row journey-step__survival-row--eliminated">
                      <span className="journey-step__survival-status">ELIMINATED (하위 8개 팀 즉시 탈락)</span>
                      <div className="journey-step__survival-blocks">
                        <div className="journey-step__survival-block">#9</div>
                        <div className="journey-step__survival-block">#10</div>
                        <div className="journey-step__survival-block">#11</div>
                        <div className="journey-step__survival-block">#12</div>
                        <div className="journey-step__survival-block">#13</div>
                        <div className="journey-step__survival-block">#14</div>
                        <div className="journey-step__survival-block">#15</div>
                        <div className="journey-step__survival-block">#16</div>
                      </div>
                    </div>
                  </div>
                  <div className="journey-step__survival-box" style={{ marginTop: '16px' }}>
                    <div className="journey-step__survival-indicator">
                      <span className="journey-step__survival-teams">크라운 정예리그 성적 기준 50% 생존</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* STEP 3 */}
            <div className="journey-step">
              <div className="journey-step__badge">3</div>
              <div className="journey-step__content">
                <h3 className="journey-step__title">녹아웃 스테이지 (Knockout Stage)</h3>
                <p className="journey-step__description">
                  정예리그 순위에 따라 부여받은 시드(#1~#8)를 바탕으로 물러설 수 없는 토너먼트에 돌입합니다. 상위 시드에게 홈구장 연전과 Bo3 와일드카드전의 1승 자동 선취 등 압도적인 혜택이 주어집니다. 본 단계부터는 통합 개최 구역에서 벗어나 다시 각 구단의 개별 홈구장으로 복귀하여 경기를 진행합니다.
                </p>
                <div className="journey-step__visual">
                  <div className="journey-step__bracket">
                    {/* 8강 컬럼 */}
                    <div className="journey-step__bracket-column">
                      <div className="journey-step__bracket-title">8강 (Bo3)</div>
                      <div className="journey-step__bracket-group">
                        <div className="journey-step__bracket-match">#1 vs #8</div>
                        <div className="journey-step__bracket-match">#4 vs #5</div>
                      </div>
                      <div className="journey-step__bracket-group">
                        <div className="journey-step__bracket-match">#3 vs #6</div>
                        <div className="journey-step__bracket-match">#2 vs #7</div>
                      </div>
                    </div>

                    {/* 4강 컬럼 */}
                    <div className="journey-step__bracket-column">
                      <div className="journey-step__bracket-title">4강 (Bo5)</div>
                      <div className="journey-step__bracket-semi-group">
                        <div className="journey-step__bracket-match journey-step__bracket-match--semi">SF 1</div>
                        <div className="journey-step__bracket-match journey-step__bracket-match--semi">SF 2</div>
                      </div>
                    </div>

                    {/* 결승 컬럼 */}
                    <div className="journey-step__bracket-column">
                      <div className="journey-step__bracket-title">결승전</div>
                      <div className="journey-step__bracket-final-group">
                        <div className="journey-step__bracket-match journey-step__bracket-match--semi" style={{ fontWeight: 'bold', borderColor: '#ffffff' }}>FINALISTS</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* STEP 4 */}
            <div className="journey-step">
              <div className="journey-step__badge journey-step__badge--final">F</div>
              <div className="journey-step__content">
                <h3 className="journey-step__title">더 크라운 시리즈 (The Krown Series)</h3>
                <p className="journey-step__description">
                  포스트시즌의 대미를 장식하며 그해의 유일무이한 황제 'The Krown'의 주인을 결정짓는 최후의 결전입니다.
                </p>
                <div className="journey-step__visual">
                  <div className="journey-step__final-box">
                    <span className="journey-step__final-format">7전 4선승제 (Bo7)</span>
                    <span className="journey-step__final-detail">경기 배정: [홈-홈-홈-원정-원정-원정-홈] (상위 시드 3연전 홈 이점 극대화)</span>
                    <div className="journey-step__crown-graphic">THE KROWN CHAMPION</div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>
    </div>
  );
}
