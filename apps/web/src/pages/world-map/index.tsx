import React from 'react';
import './world-map.css';

export default function WorldMap() {
  return (
    <div className="world-map">
      <header className="world-map__header">
        <a href="#intro" className="world-map__back-btn">
          ← 소개 페이지로 돌아가기
        </a>
        <h1 className="world-map__title">세계관 지도 (World Map)</h1>
      </header>
      
      <main className="world-map__body">
        <div className="world-map__placeholder">
          <div className="world-map__placeholder-content">
            <span className="world-map__badge">3D INTERACTIVE MAP</span>
            <h2>세계관 지도가 구현될 공간입니다.</h2>
            <p>Three.js 기반의 중세풍 3D 인터랙티브 지도가 이곳에 탑재될 예정입니다.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
