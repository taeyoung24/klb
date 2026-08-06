import React, { useEffect, useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FaFolder, FaFolderOpen, FaFileAlt, FaBookOpen, FaChevronRight, FaChevronDown, FaExternalLinkAlt } from 'react-icons/fa';
import './Wiki.css';

interface TreeItem {
  type: 'directory' | 'file';
  name: string;
  path: string;
  ext?: string;
  children?: TreeItem[];
}

interface ManifestData {
  tree: TreeItem[];
  syncedAt: string;
}

const CATEGORY_LABEL_MAP: Record<string, string> = {
  clubs: '클럽 정보',
  leagues: '리그 안내',
  rules: '규정집',
  worldview: '세계관 및 설정',
  '대문.md': '위키 메인',
  'README.md': '위키 메인',
};

export default function Wiki() {
  const [manifest, setManifest] = useState<ManifestData | null>(null);
  const [activeDocPath, setActiveDocPath] = useState<string>('대문.md');
  const [docContent, setDocContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    clubs: true,
    leagues: true,
    rules: true,
    worldview: true,
  });

  // 1. manifest 트리로부터 파일명 -> 풀 경로 맵 생성
  const fileMap = useMemo(() => {
    const map = new Map<string, string>();
    if (!manifest) return map;

    const traverse = (items: TreeItem[]) => {
      for (const item of items) {
        if (item.type === 'file') {
          // 풀 경로 저장 (e.g. "clubs/azalea/comets.md")
          map.set(item.path.toLowerCase(), item.path);
          
          // 파일명만 저장 (e.g. "comets.md")
          const fileName = item.name.toLowerCase();
          if (!map.has(fileName)) {
            map.set(fileName, item.path);
          }
          
          // 확장자 없는 파일명 저장 (e.g. "comets")
          const nameWithoutExt = item.name.replace(/\.[^/.]+$/, '').toLowerCase();
          if (!map.has(nameWithoutExt)) {
            map.set(nameWithoutExt, item.path);
          }
        } else if (item.children) {
          traverse(item.children);
        }
      }
    };

    traverse(manifest.tree);
    return map;
  }, [manifest]);

  // 경로 해결 함수
  const resolveDocPath = (target: string, currentPath: string): string => {
    if (!target) return currentPath;
    let cleanTarget = target.trim();

    // 쿼리나 해시 제거
    const hashIndex = cleanTarget.indexOf('#');
    if (hashIndex !== -1) cleanTarget = cleanTarget.substring(0, hashIndex);
    const queryIndex = cleanTarget.indexOf('?');
    if (queryIndex !== -1) cleanTarget = cleanTarget.substring(0, queryIndex);

    if (!cleanTarget) return currentPath;

    // 1) fileMap에서 파일명이나 풀 경로 그대로 매칭 확인
    const lowerTarget = cleanTarget.toLowerCase();
    if (fileMap.has(lowerTarget)) {
      return fileMap.get(lowerTarget)!;
    }
    if (!lowerTarget.endsWith('.md') && fileMap.has(`${lowerTarget}.md`)) {
      return fileMap.get(`${lowerTarget}.md`)!;
    }

    // 2) 상대 경로 상대 계산 (e.g. "./azalea/comets.md" 또는 "../leagues/overview.md")
    try {
      const currentDirParts = currentPath.split('/');
      currentDirParts.pop(); // 파일명 제외

      const targetParts = cleanTarget.split('/');
      const resultParts = [...currentDirParts];

      for (const part of targetParts) {
        if (part === '.' || part === '') continue;
        if (part === '..') {
          resultParts.pop();
        } else {
          resultParts.push(part);
        }
      }

      let computedPath = resultParts.join('/');
      if (!computedPath.endsWith('.md')) computedPath += '.md';

      if (fileMap.has(computedPath.toLowerCase())) {
        return fileMap.get(computedPath.toLowerCase())!;
      }
      return computedPath;
    } catch {
      return cleanTarget;
    }
  };

  // 2. URL Hash에서 현재 선택된 문서를 파싱
  useEffect(() => {
    const parseDocFromHash = () => {
      const hash = window.location.hash;
      if (hash.startsWith('#wiki')) {
        const queryIndex = hash.indexOf('?doc=');
        if (queryIndex !== -1) {
          const docPath = decodeURIComponent(hash.substring(queryIndex + 5));
          setActiveDocPath(docPath);
          return;
        }
        const slashIndex = hash.indexOf('/', 5);
        if (slashIndex !== -1) {
          const docPath = decodeURIComponent(hash.substring(slashIndex + 1));
          setActiveDocPath(docPath);
          return;
        }
      }
      setActiveDocPath('대문.md');
    };

    parseDocFromHash();
    window.addEventListener('hashchange', parseDocFromHash);
    return () => window.removeEventListener('hashchange', parseDocFromHash);
  }, []);

  // 3. activeDocPath 선택 시 해당 문서의 상위 폴더 자동 펼침
  useEffect(() => {
    if (!activeDocPath) return;
    const parts = activeDocPath.split('/');
    if (parts.length > 1) {
      let currentAcc = '';
      const newExpanded: Record<string, boolean> = {};
      for (let i = 0; i < parts.length - 1; i++) {
        currentAcc = currentAcc ? `${currentAcc}/${parts[i]}` : parts[i];
        newExpanded[currentAcc] = true;
      }
      setExpandedFolders((prev) => ({ ...prev, ...newExpanded }));
    }
  }, [activeDocPath]);

  // 4. manifest.json 로드
  useEffect(() => {
    fetch('/wiki/manifest.json')
      .then((res) => {
        if (!res.ok) throw new Error('Manifest fetch failed');
        return res.json();
      })
      .then((data: ManifestData) => {
        setManifest(data);
      })
      .catch((err) => {
        console.error('Failed to load wiki manifest:', err);
      });
  }, []);

  // 5. 현재 마크다운 파일 내용 fetch
  useEffect(() => {
    setIsLoading(true);
    setErrorMsg(null);

    const docUrl = `/wiki/${activeDocPath}`;
    fetch(docUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`문서를 불러올 수 없습니다. (${res.status})`);
        return res.text();
      })
      .then((text) => {
        setDocContent(text);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch markdown doc:', err);
        setErrorMsg('문서를 불러오는 중 오류가 발생했습니다.');
        setIsLoading(false);
      });
  }, [activeDocPath]);

  const toggleFolder = (folderPath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedFolders((prev) => ({
      ...prev,
      [folderPath]: !prev[folderPath],
    }));
  };

  const handleSelectDoc = (path: string) => {
    window.location.hash = `#wiki?doc=${encodeURIComponent(path)}`;
  };

  // 옵시디언 위키링크 [[문서명]] 전처리 파서
  const preprocessObsidianLinks = (content: string): string => {
    return content.replace(/\[\[(.*?)\]\]/g, (_, p1: string) => {
      const parts = p1.split('|');
      const target = parts[0].trim();
      const label = parts[1] ? parts[1].trim() : target;

      const resolvedPath = resolveDocPath(target, activeDocPath);
      return `[${label}](#wiki?doc=${encodeURIComponent(resolvedPath)})`;
    });
  };

  // 트리의 부모 폴더들을 상위부터 펼침 처리하기 위한 유틸
  const renderTreeNodes = (nodes: TreeItem[]) => {
    return nodes.map((node) => {
      const isDirectory = node.type === 'directory';
      const isExpanded = expandedFolders[node.path];
      const isActive = activeDocPath === node.path;
      const displayName = CATEGORY_LABEL_MAP[node.name] || node.name;

      if (isDirectory) {
        return (
          <li key={node.path} className="wiki__tree-item">
            <div
              className="wiki__tree-node wiki__tree-node--folder"
              onClick={(e) => toggleFolder(node.path, e)}
            >
              <span className="wiki__tree-icon">
                {isExpanded ? <FaChevronDown size={10} /> : <FaChevronRight size={10} />}
              </span>
              <span className="wiki__tree-icon" style={{ color: '#0284c7' }}>
                {isExpanded ? <FaFolderOpen /> : <FaFolder />}
              </span>
              <span>{displayName}</span>
            </div>
            {isExpanded && node.children && (
              <ul className="wiki__tree-children">{renderTreeNodes(node.children)}</ul>
            )}
          </li>
        );
      }

      return (
        <li key={node.path} className="wiki__tree-item">
          <div
            className={`wiki__tree-node ${isActive ? 'wiki__tree-node--active' : ''}`}
            onClick={() => handleSelectDoc(node.path)}
          >
            <span className="wiki__tree-icon">
              <FaFileAlt />
            </span>
            <span>{displayName}</span>
          </div>
        </li>
      );
    });
  };

  const breadcrumbs = activeDocPath.split('/');

  return (
    <div className="wiki">
      <div className="wiki__container">
        {/* 좌측 사이드바 (디렉토리 트리) */}
        <aside className="wiki__sidebar">
          <h2 className="wiki__sidebar-title">
            <FaBookOpen style={{ color: '#0284c7' }} />
            KLB 위키 목차
          </h2>
          {manifest ? (
            <ul className="wiki__tree">{renderTreeNodes(manifest.tree)}</ul>
          ) : (
            <div className="wiki__loading">목차를 불러오는 중...</div>
          )}
        </aside>

        {/* 우측 메인 마크다운 뷰어 */}
        <main className="wiki__main">
          <nav className="wiki__breadcrumb">
            <span className="wiki__breadcrumb-item" onClick={() => handleSelectDoc('대문.md')} style={{ cursor: 'pointer' }}>
              KLB 위키
            </span>
            {breadcrumbs.map((crumb, idx) => {
              const isLast = idx === breadcrumbs.length - 1;
              const label = CATEGORY_LABEL_MAP[crumb] || crumb;
              return (
                <React.Fragment key={idx}>
                  <span>/</span>
                  <span className={`wiki__breadcrumb-item ${isLast ? 'wiki__breadcrumb-item--active' : ''}`}>
                    {label}
                  </span>
                </React.Fragment>
              );
            })}
          </nav>

          {isLoading ? (
            <div className="wiki__loading">문서를 읽어오는 중입니다...</div>
          ) : errorMsg ? (
            <div className="wiki__error">{errorMsg}</div>
          ) : (
            <article className="wiki__article">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children, ...props }) => {
                    if (!href) return <a {...props}>{children}</a>;

                    // 외부 링크 (http://, https://)
                    if (href.startsWith('http://') || href.startsWith('https://')) {
                      return (
                        <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                          {children} <FaExternalLinkAlt size={10} style={{ marginLeft: 2 }} />
                        </a>
                      );
                    }

                    // 이미 #wiki?doc= 형태로 파싱된 링크인 경우
                    if (href.startsWith('#wiki?doc=')) {
                      return (
                        <a href={href} {...props}>
                          {children}
                        </a>
                      );
                    }

                    // 일반 상대경로 또는 마크다운 파일 링크인 경우
                    const resolvedPath = resolveDocPath(href, activeDocPath);
                    const targetHash = `#wiki?doc=${encodeURIComponent(resolvedPath)}`;
                    return (
                      <a
                        href={targetHash}
                        onClick={(e) => {
                          e.preventDefault();
                          handleSelectDoc(resolvedPath);
                        }}
                        {...props}
                      >
                        {children}
                      </a>
                    );
                  },
                  img: ({ src, alt, ...props }) => {
                    if (!src) return null;
                    // 상대경로 이미지 변환
                    let imgSrc = src;
                    if (!src.startsWith('http://') && !src.startsWith('https://') && !src.startsWith('/')) {
                      const resolvedImgPath = resolveDocPath(src, activeDocPath);
                      imgSrc = `/wiki/${resolvedImgPath}`;
                    }
                    return <img src={imgSrc} alt={alt || ''} {...props} />;
                  },
                }}
              >
                {preprocessObsidianLinks(docContent)}
              </ReactMarkdown>
            </article>
          )}
        </main>
      </div>
    </div>
  );
}
