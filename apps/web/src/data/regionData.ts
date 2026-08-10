export type InfoType = 'league' | 'region';

export interface RegionData {
  id: string;
  type?: InfoType; // 'league' | 'region'
  name: string;
  leagueTag: string;

  // [리그(league) 전용 필드]
  includedRegions?: string; // 포함 지역 목록 나열
  description?: string;     // 리그 전체 개요

  // [지역(region) 전용 필드]
  mainTeam?: string;        // 주 구단 (마스코트)
  minorTeams?: string;      // 2, 3군 구단
  stadium?: string;         // 홈 구장
  story?: string;           // 개별 지역 서사
}

export const REGION_DATA_MAP: Record<string, RegionData> = {
  // ==========================================================================
  // 1. 4대 리그 전체 데이터 (type: 'league') -> 포함 지역 목록 나열 위주
  // ==========================================================================
  azalea: {
    id: 'azalea',
    type: 'league',
    name: '아젤리아 리그 (Azalea League)',
    leagueTag: 'AZALEA LEAGUE',
    includedRegions: '도르미르, 퍼스톨로, 휠로 스트리트, 포드, 로트리반, 던틀, 할토스, 카즈닐, 요시도, 바즈넬 (북부 대륙 해안 구역)',
    description: '북부의 서늘한 기후와 광활한 북해와 맞닿은 10개 정예 관할 지역으로 구성된 메이저 리그로, 정교한 전략 시스템과 탄탄한 거점 네트워크를 형성하고 있습니다.',
  },
  camellia: {
    id: 'camellia',
    type: 'league',
    name: '카멜리아 리그 (Camellia League)',
    leagueTag: 'CAMELLIA LEAGUE',
    includedRegions: '라틀렌, 엔사이, 쥴톤, 엘리프릴, 리피넬, 유림, 헬렌빗, 코스트리아, 메디할스, 언져 (남부 대륙 해안 구역)',
    description: '남부 해안 지대의 10개 관할 구역으로 조성된 리그로, 전통과 열정의 역사를 자랑합니다.',
  },
  gentiana: {
    id: 'gentiana',
    type: 'league',
    name: '젠티아나 리그 (Gentiana League)',
    leagueTag: 'GENTIANA LEAGUE',
    includedRegions: '위져리, 오베스톤, 뉴악스, 로시, 탈루스, 보키, 져스웨이, 이스타, 솔, 할리아 (동부 고원 산악 구역)',
    description: '동부 고원 산악 구역의 10개 세부 관할 지역으로 묶여 있으며, 지형적 특성과 자율적인 클러스터로 운영됩니다.',
  },
  magnolia: {
    id: 'magnolia',
    type: 'league',
    name: '매그놀리아 리그 (Magnolia League)',
    leagueTag: 'MAGNOLIA LEAGUE',
    includedRegions: '할로지힐, 페델로, 칼루피아, 젠필, 피아모어, 아이원, 파플힐, 라즈웰, 뉴아크, 바스타운 (서부 대평원 숲 구역)',
    description: '서부 대평원과 숲 지대를 관통하는 10개 주요 정예 지역의 연합체로 구성되어 있습니다.',
  },

  // ==========================================================================
  // 2. 세부 지역 데이터 예시 (type: 'region') -> 구단, 구장, 개별 서사 노출
  // ==========================================================================
  'region-p4': {
    id: 'region-p4',
    type: 'region',
    name: '피아모어 | Fiamor',
    leagueTag: 'ML FIAMOR',
    mainTeam: '피아모어 자이언츠 (F. Giants)',
    minorTeams: '2군: - / 3군: -',
    stadium: '피아모어 돔',
    story: '-',
  },
  'region-p5': {
    id: 'region-p5',
    type: 'region',
    name: '젠필 | Genpill',
    leagueTag: 'ML GENPILL',
    mainTeam: '젠필 이터널스 (G. Eternals)',
    minorTeams: '2군: - / 3군: -',
    stadium: '젠필 돔',
    story: '-',
  },
  'region-p6': {
    id: 'region-p6',
    type: 'region',
    name: '라즈웰 | Raswell',
    leagueTag: 'ML RASWELL',
    mainTeam: '라즈웰 팬서스 (R. Panthers)',
    minorTeams: '2군: - / 3군: -',
    stadium: '라즈웰 돔',
    story: '-',
  },
  'region-p7': {
    id: 'region-p7',
    type: 'region',
    name: '아이원 | Aione',
    leagueTag: 'ML AIONE',
    mainTeam: '아이원 루나리안즈 (A. Lunarians)',
    minorTeams: '2군: - / 3군: -',
    stadium: '아이원 루나필드',
    story: '-',
  },
  'region-p8': {
    id: 'region-p8',
    type: 'region',
    name: '뉴아크 | Nuarque',
    leagueTag: 'ML NUARQUE',
    mainTeam: '뉴아크 유니콘즈 (N. Unicorns)',
    minorTeams: '2군: - / 3군: -',
    stadium: '엔월드파크',
    story: '-',
  },
  'region-p9': {
    id: 'region-p9',
    type: 'region',
    name: '파플힐 | Popplehill',
    leagueTag: 'ML POPPLEHILL',
    mainTeam: '파플힐 스텔라즈 (P. Stellars)',
    minorTeams: '2군: - / 3군: -',
    stadium: '파플힐 볼파크',
    story: '-',
  },
  'region-p10': {
    id: 'region-p10',
    type: 'region',
    name: '페델로 | Pedelo',
    leagueTag: 'ML PEDELO',
    mainTeam: '페델로 드래곤즈 (P. Dragons)',
    minorTeams: '2군: - / 3군: -',
    stadium: '페델로 돔',
    story: '-',
  },
  'region-p11': {
    id: 'region-p11',
    type: 'region',
    name: '칼루피아 | Calupia',
    leagueTag: 'ML CALUPIA',
    mainTeam: '칼루피아 이글스 (C. Eagles)',
    minorTeams: '2군: - / 3군: -',
    stadium: '칼루피아 스타디움',
    story: '-',
  },
  'region-p12': {
    id: 'region-p12',
    type: 'region',
    name: '할로지힐 | Halosy Hill',
    leagueTag: 'ML HALOSY HILL',
    mainTeam: '할로지힐 블루버즈 (H. Blue Birds)',
    minorTeams: '2군: - / 3군: -',
    stadium: '할로지 필드',
    story: '-',
  },
  'region-p13': {
    id: 'region-p13',
    type: 'region',
    name: '바스타운 | Vastown',
    leagueTag: 'ML VASTOWN',
    mainTeam: '바스타운 블랙크라운즈 (V. Black Crowns)',
    minorTeams: '2군: - / 3군: -',
    stadium: '바스타운 스타디움',
    story: '-',
  },
  'region-p23': {
    id: 'region-p23',
    type: 'region',
    name: '메디할스 | Medihals',
    leagueTag: 'CL MEDIHALS',
    mainTeam: '메디할스 테일즈 (M. Tales)',
    minorTeams: '2군: - / 3군: -',
    stadium: '테일 스타디움',
    story: '-',
  },
  'region-p24': {
    id: 'region-p24',
    type: 'region',
    name: '로시 | Rocy',
    leagueTag: 'GL ROCY',
    mainTeam: '로시 글리터즈 (R. Glitters)',
    minorTeams: '2군: - / 3군: -',
    stadium: '글리터랜드',
    story: '-',
  },
};

// ID로부터 정보 데이터를 얻는 헬퍼 함수
export function getRegionDataById(regionId: string | null): RegionData | null {
  if (!regionId) return null;

  // 1. REGION_DATA_MAP에 직접 등록된 키(예: 'region-p35', 'azalea')가 우선 매칭
  if (REGION_DATA_MAP[regionId]) {
    return REGION_DATA_MAP[regionId];
  }

  const lower = regionId.toLowerCase();

  // 2. 리그 이름(azalea, camellia 등) 직접 매칭 시 리그 전용 데이터 반환
  if (lower === 'azalea') return REGION_DATA_MAP.azalea;
  if (lower === 'camellia') return REGION_DATA_MAP.camellia;
  if (lower === 'gentiana') return REGION_DATA_MAP.gentiana;
  if (lower === 'magnolia') return REGION_DATA_MAP.magnolia;

  // 3. region-pXX 세부 지역 ID일 때 개별 데이터가 없으면 속한 리그의 기본 데이터로 폴백
  if (regionId.startsWith('region-p')) {
    const num = parseInt(regionId.replace('region-p', ''), 10);
    const AZALEA_IDS = [34, 35, 36, 37, 38, 39, 40, 41, 42, 43];
    const CAMELLIA_IDS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23];
    const GENTIANA_IDS = [24, 25, 26, 27, 28, 29, 30, 31, 32, 33];
    const MAGNOLIA_IDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13];

    if (AZALEA_IDS.includes(num)) return REGION_DATA_MAP.azalea;
    if (CAMELLIA_IDS.includes(num)) return REGION_DATA_MAP.camellia;
    if (GENTIANA_IDS.includes(num)) return REGION_DATA_MAP.gentiana;
    if (MAGNOLIA_IDS.includes(num)) return REGION_DATA_MAP.magnolia;
  }

  return null;
}
