import { BASE_YEAR } from '../constants/config';

/**
 * 백엔드 sim_day(1-indexed)를 BASE_YEAR(2026) 기준 정확한 Date 객체로 변환합니다.
 * 프론트엔드 연도 중복 합산 오차를 원천 방지합니다.
 */
export const simDayToDate = (simDay: number, baseYear: number = BASE_YEAR): Date => {
  return new Date(baseYear, 0, simDay);
};

/**
 * 백엔드 sim_day를 ISO YYYY-MM-DD 날짜 문자열로 변환합니다.
 */
export const simDayToDateStr = (simDay: number, baseYear: number = BASE_YEAR): string => {
  const d = simDayToDate(simDay, baseYear);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * 백엔드 sim_day를 yyyy.mm.dd 날짜 문자열로 변환합니다.
 */
export const formatSimDayDot = (simDay: number, baseYear: number = BASE_YEAR): string => {
  const d = simDayToDate(simDay, baseYear);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}.${month}.${day}`;
};

