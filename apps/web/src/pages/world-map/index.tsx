import { useState } from 'react';
import { MapCanvas } from './components/MapCanvas';
import { MapUIOverlay } from './components/MapUIOverlay';
import './world-map.css';

interface RegionInfo {
  id: string;
  name: string;
  layer: string;
}

export default function WorldMap() {
  const [selectedRegion, setSelectedRegion] = useState<RegionInfo | null>(null);
  const [resetTrigger, setResetTrigger] = useState(0);

  const handleResetCamera = () => {
    setSelectedRegion(null);
    setResetTrigger((prev) => prev + 1);
  };

  return (
    <div className="world-map">
      <header className="world-map__header">
        <a href="#intro" className="world-map__back-btn">
          ← 소개 페이지로 돌아가기
        </a>
        <div className="world-map__header-title-group">
          <h1 className="world-map__title">3D INTERACTIVE WORLD MAP</h1>
          <span className="world-map__subtitle">역사가 깃든 대륙과 리그 영토 지도</span>
        </div>
      </header>

      <main className="world-map__body">
        <MapCanvas
          key={resetTrigger}
          onSelectRegion={setSelectedRegion}
          hoveredRegionId={null}
        />
        <MapUIOverlay
          selectedRegion={selectedRegion}
          onResetCamera={handleResetCamera}
        />
      </main>
    </div>
  );
}
