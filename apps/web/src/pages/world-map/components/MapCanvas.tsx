import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { SVGLoader } from 'three/examples/jsm/loaders/SVGLoader.js';

interface MapCanvasProps {
  onSelectRegion: (regionInfo: { id: string; name: string; layer: string } | null) => void;
  hoveredRegionId: string | null;
}

export const MapCanvas: React.FC<MapCanvasProps> = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 1. Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b101d);

    // 2. OrthographicCamera (1920x1080 픽셀 1:1 직교 매핑)
    const camera = new THREE.OrthographicCamera(
      -width / 2,
      width / 2,
      height / 2,
      -height / 2,
      1,
      2000
    );
    camera.position.set(0, 0, 500);
    camera.lookAt(0, 0, 0);

    // 3. Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 4. Ambient Light
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0);
    scene.add(ambientLight);

    // 5. SVG Map Group (1920x1080 1:1 픽셀 오프셋 매핑)
    const mapGroup = new THREE.Group();
    scene.add(mapGroup);

    const loader = new SVGLoader();
    loader.load(
      '/assets/map/world-map.svg',
      (data) => {
        const paths = data.paths;

        paths.forEach((path) => {
          const userData = path.userData as { elem?: SVGElement };
          const elem = userData.elem;
          const id = elem?.id || 'unknown';
          const isContinent = id.startsWith('continent');
          const isLeague = id.startsWith('league');

          let shapes: THREE.Shape[] = [];
          try {
            shapes = (path as any).toShapes(true);
            if (shapes.length === 0) shapes = (path as any).toShapes(false);
          } catch {
            shapes = SVGLoader.createShapes(path);
          }

          shapes.forEach((shape: THREE.Shape) => {
            const geometry = new THREE.ShapeGeometry(shape);

            let color = 0x38bdf8;
            if (isContinent) color = 0x1e293b;
            if (isLeague) color = 0x334155;
            if (id.startsWith('region')) color = 0xd4af37;

            const material = new THREE.MeshBasicMaterial({
              color,
              side: THREE.DoubleSide,
            });

            const mesh = new THREE.Mesh(geometry, material);

            const edgesGeo = new THREE.EdgesGeometry(geometry);
            const edgesMat = new THREE.LineBasicMaterial({
              color: isContinent ? 0x64748b : 0xfef08a,
            });
            const line = new THREE.LineSegments(edgesGeo, edgesMat);
            mesh.add(line);

            mapGroup.add(mesh);
          });
        });

        // 1) SVG Y축 상하 반전 보정
        mapGroup.scale.y = -1;

        // 2) SVG (0,0)을 직교 화면 좌상단(-960, 540)으로 1:1 피팅하여 정중앙 안착
        mapGroup.position.set(-960, 540, 0);

        // 3) 화면 크기에 맞게 지도가 시원하게 보이도록 스케일 맞춤 (1920x1080 뷰포트 비율 감안)
        const scaleFactor = Math.min(width / 1920, height / 1080) * 0.85;
        mapGroup.scale.set(scaleFactor, -scaleFactor, 1);
        mapGroup.position.set((-1920 * scaleFactor) / 2, (1080 * scaleFactor) / 2, 0);

        setLoading(false);
      },
      undefined,
      (error) => {
        console.error('Error loading SVG map:', error);
        setLoading(false);
      }
    );

    // 6. ResizeObserver (창 크기 조절 시 1:1 픽셀 비율 및 스케일 실시간 동기화)
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        const h = entry.contentRect.height;
        if (w > 0 && h > 0) {
          camera.left = -w / 2;
          camera.right = w / 2;
          camera.top = h / 2;
          camera.bottom = -h / 2;
          camera.updateProjectionMatrix();
          renderer.setSize(w, h);

          // 지도를 뷰포트에 맞게 1:1 중앙 피팅 스케일 재계산
          const scaleFactor = Math.min(w / 1920, h / 1080) * 0.85;
          mapGroup.scale.set(scaleFactor, -scaleFactor, 1);
          mapGroup.position.set((-1920 * scaleFactor) / 2, (1080 * scaleFactor) / 2, 0);
        }
      }
    });

    resizeObserver.observe(container);

    // 7. Render Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      resizeObserver.disconnect();
      cancelAnimationFrame(animationFrameId);
      renderer.dispose();
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, []);

  return (
    <div className="world-map__canvas-wrapper" ref={containerRef}>
      {loading && (
        <div className="world-map__loading">
          <div className="world-map__spinner"></div>
          <p>1920x1080 픽셀 규격으로 1:1 정면 지도를 매핑 중입니다...</p>
        </div>
      )}
    </div>
  );
};
