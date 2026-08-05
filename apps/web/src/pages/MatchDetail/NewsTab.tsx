import React from 'react';

export interface NewsItem {
  title: string;
  time: string;
  category: string;
}

export interface NewsTabProps {
  newsList: NewsItem[];
}

export const NewsTab: React.FC<NewsTabProps> = ({ newsList }) => {
  return (
    <div className="match-detail__panel">
      <h3 className="match-detail__panel-title">매치 관련 뉴스 및 하이라이트</h3>
      <div className="match-detail__news-list">
        {newsList.map((n, i) => (
          <div key={i} className="match-detail__news-item">
            <span className="match-detail__news-category">{n.category}</span>
            <h5 className="match-detail__news-headline">{n.title}</h5>
            <span className="match-detail__news-time">{n.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NewsTab;
