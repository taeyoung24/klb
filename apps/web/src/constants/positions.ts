export const POSITION_CODE_MAP: Record<string, string> = {
  PITCHER: 'P',
  CATCHER: 'C',
  FIRST_BASE: '1B',
  FIRST_BASEMAN: '1B',
  SECOND_BASE: '2B',
  SECOND_BASEMAN: '2B',
  THIRD_BASE: '3B',
  THIRD_BASEMAN: '3B',
  SHORT_STOP: 'SS',
  SHORTSTOP: 'SS',
  LEFT_FIELD: 'LF',
  LEFT_FIELDER: 'LF',
  CENTER_FIELD: 'CF',
  CENTER_FIELDER: 'CF',
  RIGHT_FIELD: 'RF',
  RIGHT_FIELDER: 'RF',
  DESIGNATED_HITTER: 'DH',
  PINCH_HITTER: 'PH',
  PINCH_RUNNER: 'PR',
}

export const POSITION_KO_MAP: Record<string, string> = {
  // Enum Keys
  PITCHER: '투수',
  CATCHER: '포수',
  FIRST_BASE: '1루수',
  FIRST_BASEMAN: '1루수',
  SECOND_BASE: '2루수',
  SECOND_BASEMAN: '2루수',
  THIRD_BASE: '3루수',
  THIRD_BASEMAN: '3루수',
  SHORT_STOP: '유격수',
  SHORTSTOP: '유격수',
  LEFT_FIELD: '좌익수',
  LEFT_FIELDER: '좌익수',
  CENTER_FIELD: '중견수',
  CENTER_FIELDER: '중견수',
  RIGHT_FIELD: '우익수',
  RIGHT_FIELDER: '우익수',
  DESIGNATED_HITTER: '지명타자',
  PINCH_HITTER: '대타',
  PINCH_RUNNER: '대주자',
  OUTFIELDER: '외야수',
  INFIELDER: '내야수',

  // Short Codes
  P: '투수',
  C: '포수',
  '1B': '1루수',
  '2B': '2루수',
  '3B': '3루수',
  SS: '유격수',
  LF: '좌익수',
  CF: '중견수',
  RF: '우익수',
  DH: '지명타자',
  PH: '대타',
  PR: '대주자',
  OF: '외야수',
  IF: '내야수',
}

export function formatPosition(pos?: string | null): string {
  if (!pos) return '-'
  const upper = pos.toUpperCase()
  return POSITION_KO_MAP[upper] || POSITION_KO_MAP[pos] || pos
}

export function formatPositionCode(pos?: string | null): string {
  if (!pos) return '-'
  const upper = pos.toUpperCase()
  return POSITION_CODE_MAP[upper] || POSITION_CODE_MAP[pos] || pos
}
