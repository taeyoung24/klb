import { useState } from 'react';
import { FaFilePdf, FaFileWord, FaFileExcel, FaDownload, FaSearch } from 'react-icons/fa';
import './AppArchiveSection.css';

interface ArchiveItem {
  id: number;
  title: string;
  category: 'rules' | 'forms' | 'guides' | 'reports';
  categoryLabel: string;
  fileType: 'pdf' | 'docx' | 'xlsx';
  fileSize: string;
  date: string;
  downloads: number;
}

export default function AppArchiveSection() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const archiveItems: ArchiveItem[] = [
    {
      id: 1,
      title: '2026 시즌 KLB 공식 대회 규정집 및 경기 세칙',
      category: 'rules',
      categoryLabel: '규정/세칙',
      fileType: 'pdf',
      fileSize: '4.2 MB',
      date: '2026-03-01',
      downloads: 1420,
    },
    {
      id: 2,
      title: '리그 구단 선수 등록 및 이적 신청서 표준 양식',
      category: 'forms',
      categoryLabel: '리그 서식',
      fileType: 'docx',
      fileSize: '245 KB',
      date: '2026-03-05',
      downloads: 850,
    },
    {
      id: 3,
      title: '2026 공식 경기 기록지 표기법 및 기록원 가이드북',
      category: 'guides',
      categoryLabel: '미디어 가이드',
      fileType: 'pdf',
      fileSize: '8.7 MB',
      date: '2026-03-10',
      downloads: 630,
    },
    {
      id: 4,
      title: 'KLB 미디어 취재진 출입 및 취재 가이드라인',
      category: 'guides',
      categoryLabel: '미디어 가이드',
      fileType: 'pdf',
      fileSize: '2.1 MB',
      date: '2026-03-12',
      downloads: 410,
    },
    {
      id: 5,
      title: '2025 상반기 크라운 정예리그 구단별 전력분석 종합보고서',
      category: 'reports',
      categoryLabel: '시즌 보고서',
      fileType: 'xlsx',
      fileSize: '1.5 MB',
      date: '2025-11-20',
      downloads: 1190,
    },
    {
      id: 6,
      title: '선수단 부상 이력 신고서 및 엔트리 변경 신청 서식',
      category: 'forms',
      categoryLabel: '리그 서식',
      fileType: 'docx',
      fileSize: '180 KB',
      date: '2026-03-15',
      downloads: 520,
    },
    {
      id: 7,
      title: '2026 시즌 개막 미디어북 & 리그 소속 구단 로스터 종합',
      category: 'guides',
      categoryLabel: '미디어 가이드',
      fileType: 'pdf',
      fileSize: '12.4 MB',
      date: '2026-03-20',
      downloads: 2300,
    },
    {
      id: 8,
      title: '포스트 파이널 챔피언십 특별 경기 진행 세칙',
      category: 'rules',
      categoryLabel: '규정/세칙',
      fileType: 'pdf',
      fileSize: '3.1 MB',
      date: '2025-10-15',
      downloads: 980,
    },
  ];

  const filteredItems = archiveItems.filter((item) => {
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'pdf':
        return <FaFilePdf className="archive-section__icon archive-section__icon--pdf" />;
      case 'docx':
        return <FaFileWord className="archive-section__icon archive-section__icon--docx" />;
      case 'xlsx':
        return <FaFileExcel className="archive-section__icon archive-section__icon--xlsx" />;
      default:
        return <FaFilePdf className="archive-section__icon" />;
    }
  };

  const handleDownload = (title: string) => {
    alert(`'${title}' 파일 다운로드가 시작되었습니다.`);
  };

  return (
    <div className="archive-section">
      <div className="archive-section__container">
        {/* 상단 타이틀 */}
        <header className="archive-section__header">
          <h1 className="archive-section__title">자료실</h1>
          <p className="archive-section__subtitle">
            Krown League Baseball의 공식 대회 규정, 양식, 미디어 가이드 및 기록 보고서를 다운로드하실 수 있습니다.
          </p>
        </header>

        {/* 검색 및 필터 컨트롤 바 */}
        <div className="archive-section__controls">
          <div className="archive-section__search-box">
            <FaSearch className="archive-section__search-icon" />
            <input
              type="text"
              className="archive-section__search-input"
              placeholder="문서 제목으로 검색하세요..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="archive-section__categories">
            <button
              className={`archive-section__category-btn ${selectedCategory === 'all' ? 'archive-section__category-btn--active' : ''}`}
              onClick={() => setSelectedCategory('all')}
            >
              전체
            </button>
            <button
              className={`archive-section__category-btn ${selectedCategory === 'rules' ? 'archive-section__category-btn--active' : ''}`}
              onClick={() => setSelectedCategory('rules')}
            >
              규정/세칙
            </button>
            <button
              className={`archive-section__category-btn ${selectedCategory === 'forms' ? 'archive-section__category-btn--active' : ''}`}
              onClick={() => setSelectedCategory('forms')}
            >
              리그 서식
            </button>
            <button
              className={`archive-section__category-btn ${selectedCategory === 'guides' ? 'archive-section__category-btn--active' : ''}`}
              onClick={() => setSelectedCategory('guides')}
            >
              미디어 가이드
            </button>
            <button
              className={`archive-section__category-btn ${selectedCategory === 'reports' ? 'archive-section__category-btn--active' : ''}`}
              onClick={() => setSelectedCategory('reports')}
            >
              시즌 보고서
            </button>
          </div>
        </div>

        {/* 자료 목록 */}
        <div className="archive-section__list">
          {filteredItems.length > 0 ? (
            filteredItems.map((item) => (
              <div key={item.id} className="archive-section__item">
                <div className="archive-section__item-icon">
                  {getFileIcon(item.fileType)}
                </div>
                <div className="archive-section__item-content">
                  <div className="archive-section__item-header">
                    <span className={`archive-section__item-tag archive-section__item-tag--${item.category}`}>
                      {item.categoryLabel}
                    </span>
                    <span className="archive-section__item-date">{item.date}</span>
                  </div>
                  <h3 className="archive-section__item-title">{item.title}</h3>
                  <div className="archive-section__item-meta">
                    <span className="archive-section__item-info">포맷: {item.fileType.toUpperCase()}</span>
                    <span className="archive-section__item-divider">•</span>
                    <span className="archive-section__item-info">용량: {item.fileSize}</span>
                    <span className="archive-section__item-divider">•</span>
                    <span className="archive-section__item-info">다운로드: {item.downloads.toLocaleString()}회</span>
                  </div>
                </div>
                <button
                  className="archive-section__download-btn"
                  onClick={() => handleDownload(item.title)}
                  aria-label={`${item.title} 다운로드`}
                >
                  <FaDownload className="archive-section__download-icon" />
                  다운로드
                </button>
              </div>
            ))
          ) : (
            <div className="archive-section__empty">
              검색 조건에 해당되는 자료가 없습니다.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
