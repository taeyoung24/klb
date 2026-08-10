import React, { useEffect, useRef } from 'react';
import worldMapSvgText from '/assets/map/world-map.svg?raw';

interface WorldMapProps {
  isMapHovered: boolean;
  hoveredRegion: string | null;
  selectedRegion?: string | null;
  onMapMouseEnter: () => void;
  onMapMouseLeave: () => void;
  onRegionHover: (regionId: string) => void;
  onRegionLeave: () => void;
  onRegionClick?: (regionId: string) => void;
  onSeaClick?: () => void;
}

export const WorldMap: React.FC<WorldMapProps> = ({
  isMapHovered,
  hoveredRegion,
  selectedRegion = null,
  onMapMouseEnter,
  onMapMouseLeave,
  onRegionHover,
  onRegionLeave,
  onRegionClick,
  onSeaClick,
}) => {
  const wrapperRef = useRef<HTMLDivElement>(null);

  // 활성화된 지역 (마우스 호버 지역이 1순위, 호버가 없으면 선택된 지역 유지)
  const activeRegion = hoveredRegion || selectedRegion;

  // 3가지 지도 인터랙티브 상태 계산
  // 1. state-default: 맵 영역 외부 & 선택된 지역 없음
  // 2. state-sea-hover: 맵 진입/선택 활성화 + 활성화된 지형 없음 (바다 위치)
  // 3. state-region-hover: 특정 지형 호버 중이거나 클릭되어 선택 고정된 상태
  let mapStateClass = 'state-default';
  if (isMapHovered || selectedRegion) {
    mapStateClass = activeRegion ? 'state-region-hover' : 'state-sea-hover';
  }

  // SVG 주입 후 개별 패스에 4대 리그/대륙 클래스 부착 및 선택/호버 상태 고정
  useEffect(() => {
    const container = wrapperRef.current;
    if (!container) return;

    // SVG 태그 규격 보정 (고정 1920x1080 픽셀 제거 -> 100% 비율 맞춤)
    const svgEl = container.querySelector('svg');
    if (svgEl) {
      svgEl.removeAttribute('width');
      svgEl.removeAttribute('height');
      svgEl.setAttribute('preserveAspectRatio', 'xMidYMid meet');
      svgEl.style.width = '100%';
      svgEl.style.height = 'auto';
    }

    const AZALEA_IDS = [34, 35, 36, 37, 38, 39, 40, 41, 42, 43];
    const CAMELLIA_IDS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23];
    const GENTIANA_IDS = [24, 25, 26, 27, 28, 29, 30, 31, 32, 33];
    const MAGNOLIA_IDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13];
    const paths = container.querySelectorAll<SVGPathElement>('.map-path, path[id]');
    paths.forEach((path) => {
      const id = path.id;
      if (!id) return;

      // 4대 리그 세부 지역(region-p) 외 미사용 통 레이어(continent, league) 숨김
      if (id.startsWith('continent-') || id.startsWith('league-')) {
        path.style.display = 'none';
      } else if (id.startsWith('region-p')) {
        const num = parseInt(id.replace('region-p', ''), 10);
        if (AZALEA_IDS.includes(num)) path.classList.add('league-azalea');
        else if (CAMELLIA_IDS.includes(num)) path.classList.add('league-camellia');
        else if (GENTIANA_IDS.includes(num)) path.classList.add('league-gentiana');
        else if (MAGNOLIA_IDS.includes(num)) path.classList.add('league-magnolia');
        else {
          // 4대 리그에 속하지 않는 미사용 지역(1, 2, 3번 등) 완전 제거
          path.style.display = 'none';
        }
      }

      // active 상태 감지 (호버 중이거나 클릭되어 선택 고정된 지형 하이라이트 유지)
      if (activeRegion && id === activeRegion) {
        path.classList.add('is-active');
      } else {
        path.classList.remove('is-active');
      }
    });
  }, [hoveredRegion, selectedRegion, isMapHovered]);

  return (
    <div
      className={`intro-legacy__map-container ${mapStateClass}`}
      onMouseEnter={onMapMouseEnter}
      onMouseLeave={onMapMouseLeave}
    >
      <div
        ref={wrapperRef}
        className="intro-legacy__map-svg-wrapper"
        onMouseOver={(e) => {
          const target = e.target as HTMLElement;
          if (target && target.tagName === 'path' && target.id) {
            onRegionHover(target.id);
          } else {
            onRegionLeave();
          }
        }}
        onClick={(e) => {
          const target = e.target as HTMLElement;
          if (target && target.tagName === 'path' && target.id) {
            if (onRegionClick) {
              onRegionClick(target.id);
            }
          } else {
            // 바다 클릭 시 선택 해제
            if (onSeaClick) {
              onSeaClick();
            }
          }
        }}
        dangerouslySetInnerHTML={{ __html: worldMapSvgText }}
      />

      {/* 4대 리그 오버레이 유도선 (시작점 cx, cy 기준 유도선/텍스트 위치 자동 계산) */}
      <svg
        className="map-callout-svg"
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
      >
        {CALLOUT_DATA.map((item) => {
          const { id, title, sub, cx, cy, dirX, dirY } = item;
          const diagLen = 70; // 45도 대각선 길이
          const horizLen = 160; // 수평선 길이

          const cornerX = cx + dirX * diagLen;
          const cornerY = cy + dirY * diagLen;
          const endX = cornerX + dirX * horizLen;

          const points = `${cx},${cy} ${cornerX},${cornerY} ${endX},${cornerY}`;
          const textX = endX + dirX * 15;
          const titleY = cornerY - 10;
          const subY = cornerY + 18;
          const textAnchor = dirX > 0 ? 'start' : 'end';

          return (
            <g key={id} className={`map-callout map-callout--${id}`}>
              <circle cx={cx} cy={cy} r="5" className="map-callout__dot" />
              <polyline points={points} className="map-callout__line" />
              <text x={textX} y={titleY} textAnchor={textAnchor} className="map-callout__title">
                {title}
              </text>
              <text x={textX} y={subY} textAnchor={textAnchor} className="map-callout__sub">
                {sub}
              </text>
            </g>
          );
        })}
      </svg>

      {/* 지도 우측 하단 척도 표시 (100 km Scale Bar) */}
      <div className="map-scale">
        <div className="map-scale__bar"></div>
        <span className="map-scale__label">100 km</span>
      </div>
    </div>
  );
};

// ==========================================================================
// 4대 리그 유도선 시작점(cx, cy) 및 자동 계산용 데이터 구조
// (점 좌표 cx, cy만 바꾸면 유도선, 꺾임선, 텍스트 위치가 자동으로 계산됨)
// ==========================================================================
const CALLOUT_DATA = [
  {
    id: 'camellia',
    title: 'CL, Camellia League',
    sub: '카멜리아 리그',
    cx: 940, // 카멜리아 리그 시작점 X
    cy: 620,  // 카멜리아 리그 시작점 Y
    dirX: 1,  // 1: 오른쪽 방향, -1: 왼쪽 방향
    dirY: 1,  // 1: 아래쪽 방향, -1: 위쪽 방향
  },
  {
    id: 'azalea',
    title: 'AL, Azalea League',
    sub: '아젤레아 리그',
    cx: 1320, // 아젤레아 리그 시작점 X
    cy: 250,  // 아젤레아 리그 시작점 Y
    dirX: 1,
    dirY: -1,
  },
  {
    id: 'magnolia',
    title: 'ML, Magnolia League',
    sub: '매그놀리아 리그',
    cx: 660,  // 매그놀리아 리그 시작점 X
    cy: 680,  // 매그놀리아 리그 시작점 Y
    dirX: -1,
    dirY: 1,
  },
  {
    id: 'gentiana',
    title: 'GL, Gentiana League',
    sub: '젠티아나 리그',
    cx: 1160, // 젠티아나 리그 시작점 X
    cy: 410,  // 젠티아나 리그 시작점 Y
    dirX: -1,
    dirY: -1,
  },
];

export default WorldMap;
