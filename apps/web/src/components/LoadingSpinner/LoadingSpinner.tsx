import React from 'react';
import './LoadingSpinner.css';

export interface LoadingSpinnerProps {
  fullScreen?: boolean;
  message?: string;
  size?: number;
  dimmed?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  fullScreen = false,
  message = '데이터를 불러오는 중입니다...',
  size = 36,
  dimmed = true,
}) => {
  return (
    <div
      className={`loading-overlay ${fullScreen ? 'loading-overlay--fullscreen' : ''}`}
      style={{ backgroundColor: dimmed ? undefined : 'transparent', backdropFilter: dimmed ? undefined : 'none' }}
    >
      <div
        className="loading-spinner"
        style={{
          width: size,
          height: size,
        }}
      />
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;
