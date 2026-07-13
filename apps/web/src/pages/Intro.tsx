import './Intro.css';

export default function Intro() {
  return (
    <div className="intro">
      <section className="intro-hero">
        <div className="intro-hero__container">
          <span className="intro-hero__tag">ABOUT KROWN LEAGUE</span>
          <h1 className="intro-hero__title">대한민국 야구의 새로운 장을 열다</h1>
          <p className="intro-hero__desc">
            Krown League Baseball(KLB)은 프로 야구의 뜨거운 경쟁과 혁신적인 팬 경험을 결합하여
            스포츠 엔터테인먼트의 새로운 기준을 제시합니다.
          </p>
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
