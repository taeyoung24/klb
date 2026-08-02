import React from 'react';

interface SelectedRegionInfo {
  id: string;
  name: string;
  layer: string;
}

interface MapUIOverlayProps {
  selectedRegion: SelectedRegionInfo | null;
  onResetCamera: () => void;
}

export const MapUIOverlay: React.FC<MapUIOverlayProps> = ({
  selectedRegion,
  onResetCamera,
}) => {
  return (
    <div className="map-ui">
      {/* 앤틱 컨트롤 패널 */}
      <div className="map-ui__controls">
        <button
          className="map-ui__btn map-ui__btn--reset"
          onClick={onResetCamera}
          title="카메라 시점 초기화"
        >
          🌐 전체 지도 보기
        </button>
      </div>

      {/* 범례 (Legend) */}
      <div className="map-ui__legend">
        <h4 className="map-ui__legend-title">🗺️ 지도 범례</h4>
        <ul className="map-ui__legend-list">
          <li className="map-ui__legend-item">
            <span className="map-ui__badge map-ui__badge--continent"></span>
            <span>대륙 (Continents)</span>
          </li>
          <li className="map-ui__legend-item">
            <span className="map-ui__badge map-ui__badge--league"></span>
            <span>리그 권역 (Leagues)</span>
          </li>
          <li className="map-ui__legend-item">
            <span className="map-ui__badge map-ui__badge--region"></span>
            <span>세부 영토 (Regions)</span>
          </li>
        </ul>
      </div>

      {/* 선택된 영토 상세 팝업 패널 (중세 양피지 카드 스타일) */}
      {selectedRegion && (
        <div className="map-ui__panel">
          <div className="map-ui__panel-header">
            <span className="map-ui__panel-tag">{selectedRegion.layer}</span>
            <h3 className="map-ui__panel-title">{selectedRegion.name}</h3>
          </div>
          <div className="map-ui__panel-body">
            <div className="map-ui__info-row">
              <span className="map-ui__info-label">식별 ID</span>
              <span className="map-ui__info-value">{selectedRegion.id}</span>
            </div>
            <div className="map-ui__info-row">
              <span className="map-ui__info-label">지형 상태</span>
              <span className="map-ui__info-value">3D 입체 메시 활성화</span>
            </div>
            <p className="map-ui__panel-desc">
              이곳은 수많은 역사와 이야기가 시작된 거점입니다. 향후 세계관 세부 설정과 소속 구단 정보가 이곳에 상세히 매핑될 예정입니다.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
