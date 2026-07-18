import { useState, useRef, useEffect } from 'react';
import './Intro.css';
import mainBannerImg from '../assets/main_banner.jpeg';

export default function Intro() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [videoOpacity, setVideoOpacity] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);

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
          <span className="intro-hero__tag">The Infinity Stories</span>
          <h2 className="intro-hero__title">여기, 끝나지 않는 이야기.</h2>
          <p className="intro-hero__desc">
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

      <section className="intro-section intro-section--light">
        <div className="intro-section__container">
          <div className="intro-section__grid">
            <div className="intro-section__content">
              <h2 className="intro-section__title">우리의 비전 (Vision)</h2>
              <p className="intro-section__paragraph">
                우리는 단순한 야구 리그를 넘어, 선수들에게는 최고의 꿈의 무대를,
                팬들에게는 매 순간이 감동으로 기억되는 최고의 엔터테인먼트 플랫폼을
                지향합니다.
              </p>
            </div>
            <div className="intro-section__content">
              <h2 className="intro-section__title">핵심 가치 (Core Values)</h2>
              <ul className="intro-section__values">
                <li className="intro-section__value-item">
                  <strong>혁신 (Innovation):</strong> 전통적인 야구 방식에 기술과 새로운 트렌드를 결합합니다.
                </li>
                <li className="intro-section__value-item">
                  <strong>열정 (Passion):</strong> 필드 위에서의 모든 투구와 타격에 뜨거운 진심을 담습니다.
                </li>
                <li className="intro-section__value-item">
                  <strong>상생 (Synergy):</strong> 팬, 구단, 지역 사회가 함께 성장하는 에코시스템을 구축합니다.
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
