import axios from 'axios';
let BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';
const currentHost = window.location.hostname;

// 만약 접속한 주소가 내부망(192.168.x.x)이거나 로컬호스트인 경우
// 백엔드 요청 주소를 현재 접속한 내부 IP로 덮어씌움
if (
  currentHost === 'localhost' ||
  currentHost === '127.0.0.1' ||
  currentHost.startsWith('192.168.')
) {
  // (만약 Nginx가 80포트로 프론트와 API를 모두 처리 중이라면 포트번호 없이 `http://${currentHost}/api`로 변경)
  BASE_URL = `http://${currentHost}:3000/api`;
}

// Create a configured axios instance
// In a real app, baseURL would come from environment variables
const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default client;
