import React from 'react';
import './LeagueShortcut.css';

interface LeagueInfo {
  name: string;
  koreanName: string;
  abbreviation: string;
  color: string;
  accentColor: string;
  videoSrc: string;
}

export default function LeagueShortcut() {
  const leagues: LeagueInfo[] = [
    {
      name: 'Magnolia League',
      koreanName: '매그놀리아 리그',
      abbreviation: 'ML',
      color: 'white',
      accentColor: '#ffffff',
      videoSrc: '/videos/flag_magnolia.mp4',
    },
    {
      name: 'Camellia League',
      koreanName: '카멜리아 리그',
      abbreviation: 'CL',
      color: 'red',
      accentColor: '#ff4757',
      videoSrc: '/videos/flag_camellia.mp4',
    },
    {
      name: 'Gentiana League',
      koreanName: '젠티아나 리그',
      abbreviation: 'GL',
      color: 'blue',
      accentColor: '#1e90ff',
      videoSrc: '/videos/flag_gentiana.mp4',
    },
    {
      name: 'Azalea League',
      koreanName: '아젤리아 리그',
      abbreviation: 'AL',
      color: 'pink',
      accentColor: '#ff6b8b',
      videoSrc: '/videos/flag_azalea.mp4',
    },
  ];

  return (
    <div className="league-shortcut">
      <div className="league-shortcut__container">
        {leagues.map((league) => (
          <div 
            key={league.abbreviation}
            className={`league-card league-card--${league.color}`}
            style={{ '--glow-color': league.accentColor } as React.CSSProperties}
          >
            {/* 펄럭이는 루프 동영상 배경 */}
            <video
              className="league-card__video"
              autoPlay
              loop
              muted
              playsInline
            >
              <source src={league.videoSrc} type="video/mp4" />
            </video>
            <div className="league-card__overlay"></div>

            <div className="league-card__content">
              <h2 className="league-card__title">{league.name}</h2>
              <span className="league-card__subtitle">{league.koreanName}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
