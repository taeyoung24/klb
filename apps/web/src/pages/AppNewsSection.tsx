import newsThumbnail from '../assets/news_baseball_thumbnail.png'
import './AppNewsSection.css'

interface NewsItem {
  id: number;
  title: string;
  excerpt: string;
  date: string;
  press: string;
  thumbnailUrl?: string;
}

const mockNews: NewsItem[] = [
  {
    id: 1,
    title: "Krown League Baseball 2026 시즌 공식 일정 확정",
    excerpt: "대한민국 야구 독립 리그의 새 바람, KLB의 2026 정규 시즌 공식 일정이 발표되었습니다. 개막전은 오는 4월 7일 제니스 구장을 비롯한 전국 5개 구장에서 동시에 열리며, 팀당 144경기의 대장정이 시작됩니다...",
    date: "2026.07.17",
    press: "스포츠크라운",
    thumbnailUrl: newsThumbnail
  },
  {
    id: 2,
    title: "새턴즈, 도미니카 출신 불펜 투수 영입 발표",
    excerpt: "새턴즈 구단은 마운드 보강을 위해 도미니카 공화국 출신의 강속구 우완 불펜 투수 카를로스 산체스와 계약을 맺었다고 공식 발표했습니다. 계약 금액은 옵션을 포함하여...",
    date: "2026.07.15",
    press: "KLB Daily"
  },
  {
    id: 3,
    title: "Krown Star Weekend 올스타전 팬 투표 시작",
    excerpt: "시즌 80경기 시점에 개최되는 초대형 연합 이벤트 'Krown Star Weekend'의 올스타 투표가 오늘 오전 10시부터 공식 앱을 통해 개시되었습니다. 선발 명단은 100% 팬 투표로...",
    date: "2026.07.12",
    press: "네오베이스볼",
    thumbnailUrl: newsThumbnail
  },
  {
    id: 4,
    title: "가디언즈, 유소년 야구단 초청 재능 기부 클리닉",
    excerpt: "가디언즈 선수단은 비시즌을 맞아 연고지 지역 아동 센터 소속의 유소년 야구 선수 50명을 구단 훈련장으로 초청하여 1일 멘토링 프로그램 및 야구 기술 교육을 성황리에 진행했습니다...",
    date: "2026.07.08",
    press: "구단 소식지"
  },
  {
    id: 5,
    title: "KLB 하부 디비전 육성 리그 통합 시스템 개편안 발표",
    excerpt: "리그 사무국은 2군 및 3군 디비전 활성화와 유기적인 콜업/강등 체계를 확립하기 위한 통합 육성 시스템 개편안을 의결했습니다. 이번 개편으로 유망주들의 출전 기회가 더욱...",
    date: "2026.07.05",
    press: "리그 리포트",
    thumbnailUrl: newsThumbnail
  }
];

export default function AppNewsSection() {
  return (
    <section className="section section--light">
      <div className="section__container">
        <div className="section__header">
          <h2 className="section__title">통합 소식</h2>
          <a href="#news" className="section__more-link">뉴스 더보기</a>
        </div>
        <div className="news-list">
          {mockNews.map((news) => (
            <div key={news.id} className="news-card">
              {news.thumbnailUrl && (
                <div className="news-card__thumbnail-wrapper">
                  <img className="news-card__thumbnail" src={news.thumbnailUrl} alt={news.title} />
                </div>
              )}
              <div className="news-card__content">
                <div className="news-card__meta">
                  <span className="news-card__press">{news.press}</span>
                  <span className="news-card__date">{news.date}</span>
                </div>
                <h3 className="news-card__title">
                  <a href={`#news-${news.id}`} className="news-card__link">{news.title}</a>
                </h3>
                <p className="news-card__excerpt">{news.excerpt}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
