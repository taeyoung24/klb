import React, { useState } from 'react';
import './TeamLogo.css';

export interface TeamLogoProps {
  teamCode?: string;
  teamName?: string;
  logoUrl?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | number;
  className?: string;
  style?: React.CSSProperties;
}

export const TeamLogo: React.FC<TeamLogoProps> = ({
  teamCode = '',
  teamName = '',
  logoUrl,
  size = 'md',
  className = '',
  style = {},
}) => {
  const [imageError, setImageError] = useState(false);

  // 로고 이미지 우선순위: prop으로 전달된 logoUrl -> /teams/{teamCode}.png
  const src = logoUrl || (teamCode ? `/teams/${teamCode.toLowerCase()}.png` : '');

  // 심볼 텍스트 추출 (한글 팀명 첫 글자 > 영문 팀코드 첫 글자 > 기본값 '?')
  const symbol = teamName ? teamName.trim()[0] : teamCode ? teamCode.trim()[0] : '?';

  const getSizeStyle = (): React.CSSProperties => {
    if (typeof size === 'number') {
      return { width: `${size}px`, height: `${size}px`, fontSize: `${Math.max(10, size * 0.45)}px` };
    }
    return {};
  };

  const sizeClass = typeof size === 'string' ? `team-logo--${size}` : '';

  if (src && !imageError) {
    return (
      <img
        src={src}
        alt={teamName || teamCode || 'Team Logo'}
        className={`team-logo ${sizeClass} ${className}`}
        style={{ ...getSizeStyle(), ...style }}
        onError={() => setImageError(true)}
      />
    );
  }

  return (
    <div
      className={`team-logo team-logo--placeholder ${sizeClass} ${className}`}
      style={{ ...getSizeStyle(), ...style }}
      title={teamName || teamCode}
    >
      {symbol}
    </div>
  );
};

export default TeamLogo;
