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
  'region-p14': {
    id: 'region-p14',
    type: 'region',
    name: '쥴톤 | Julton',
    leagueTag: 'CL JULTON',
    mainTeam: '쥴톤 다이노스 (J. Dinos)',
    minorTeams: '2군: - / 3군: -',
    stadium: '쥴톤파크',
    story: '-',
  },
  'region-p15': {
    id: 'region-p15',
    type: 'region',
    name: '리피넬 | Liphinel',
    leagueTag: 'CL LIPHINEL',
    mainTeam: '리피넬 퍼스터즈 (L. Firsters)',
    minorTeams: '2군: - / 3군: -',
    stadium: '퍼스터즈 볼파크',
    story: '-',
  },
  'region-p16': {
    id: 'region-p16',
    type: 'region',
    name: '언져 | Undger',
    leagueTag: 'CL UNDHER',
    mainTeam: '언져 트레져스 (U. Treasures)',
    minorTeams: '2군: - / 3군: -',
    stadium: '언져 스타디움',
    story: '-',
  },
  'region-p17': {
    id: 'region-p17',
    type: 'region',
    name: '헬렌빗 | Hellenvit',
    leagueTag: 'CL HELLENVIT',
    mainTeam: '헬렌빗 레드헌터즈 (H. Red Hunters)',
    minorTeams: '2군: - / 3군: -',
    stadium: '헬렌빗스 필드',
    story: '-',
  },
  'region-p18': {
    id: 'region-p18',
    type: 'region',
    name: '엔사이 | Ensai',
    leagueTag: 'CL ENSAI',
    mainTeam: '엔사이 블랙캣츠 (E. Black Cats)',
    minorTeams: '2군: - / 3군: -',
    stadium: '엔사이 캣츠 필드',
    story: '-',
  },
  'region-p19': {
    id: 'region-p19',
    type: 'region',
    name: '라틀렌 | Rotlen',
    leagueTag: 'CL ROTLEN',
    mainTeam: '라틀렌 아쳐스 (R. Archers)',
    minorTeams: '2군: - / 3군: -',
    stadium: '라틀렌 필드',
    story: '-',
  },
  'region-p20': {
    id: 'region-p20',
    type: 'region',
    name: '유림 | Ureme',
    leagueTag: 'CL UREME',
    mainTeam: '유림 히어로즈 (U. Heros)',
    minorTeams: '2군: - / 3군: -',
    stadium: '유림 히어로즈 필드',
    story: '-',
  },
  'region-p21': {
    id: 'region-p21',
    type: 'region',
    name: '엘리프릴 | Ellifril',
    leagueTag: 'CL ELLIFRIL',
    mainTeam: '엘리프릴 플레임즈 (Ellipril Park)',
    minorTeams: '2군: - / 3군: -',
    stadium: '엘리프릴 파크',
    story: '-',
  },
  'region-p22': {
    id: 'region-p22',
    type: 'region',
    name: '코스미어 | Cosmeer',
    leagueTag: 'CL COSMEER',
    mainTeam: '코스미어 솔라리안즈 (C. Solarians)',
    minorTeams: '2군: - / 3군: -',
    stadium: '코스미어 파크',
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
  'region-p25': {
    id: 'region-p25',
    type: 'region',
    name: '뉴악스 | Nuax',
    leagueTag: 'GL NUAX',
    mainTeam: '뉴악스 프리져스 (N. Freezers)',
    minorTeams: '2군: - / 3군: -',
    stadium: '프리져스 필드',
    story: '-',
  },
  'region-p26': {
    id: 'region-p26',
    type: 'region',
    name: '탈루스 | Talus',
    leagueTag: 'GL TALUS',
    mainTeam: '탈루스 나이츠 (T. Knights)',
    minorTeams: '2군: - / 3군: -',
    stadium: '탈루스 볼파크',
    story: '-',
  },
  'region-p27': {
    id: 'region-p27',
    type: 'region',
    name: '보키 | Voky',
    leagueTag: 'GL VOKY',
    mainTeam: '보키 페가수스 (V. Pegasus)',
    minorTeams: '2군: - / 3군: -',
    stadium: '보키 돔',
    story: '-',
  },
  'region-p28': {
    id: 'region-p28',
    type: 'region',
    name: '위져리 | Widgery',
    leagueTag: 'GL WIDGERY',
    mainTeam: '위져리 크리스탈즈 (W. Crystals)',
    minorTeams: '2군: - / 3군: -',
    stadium: '위져리 볼파크',
    story: '-',
  },
  'region-p29': {
    id: 'region-p29',
    type: 'region',
    name: '져스웨이 | Gersway',
    leagueTag: 'GL GERSWAY',
    mainTeam: '져스웨이 스완스 (G. Swans)',
    minorTeams: '2군: - / 3군: -',
    stadium: '져스웨이 래이크필드',
    story: '-',
  },
  'region-p30': {
    id: 'region-p30',
    type: 'region',
    name: '할리아 | Holia',
    leagueTag: 'GL HOLIA',
    mainTeam: '할리아 베어스 (H. Bears)',
    minorTeams: '2군: - / 3군: -',
    stadium: '할리아 돔',
    story: '-',
  },
  'region-p31': {
    id: 'region-p31',
    type: 'region',
    name: '오베스톤 | Ovestaln',
    leagueTag: 'GL OVESTALN',
    mainTeam: '오베스톤 팔콘스 (O. Falcons)',
    minorTeams: '2군: - / 3군: -',
    stadium: '오베스톤 볼파크',
    story: '-',
  },
  'region-p32': {
    id: 'region-p32',
    type: 'region',
    name: '솔 | Thorl',
    leagueTag: 'GL THORL',
    mainTeam: '솔 와이번스 (T. Wyverns)',
    minorTeams: '2군: - / 3군: -',
    stadium: '솔 스타디움',
    story: '-',
  },
  'region-p33': {
    id: 'region-p33',
    type: 'region',
    name: '이스타 | Istaa',
    leagueTag: 'GL ISTAA',
    mainTeam: '이스타 보이져스 (I. Voyagers)',
    minorTeams: '2군: - / 3군: -',
    stadium: '이스타 돔',
    story: '-',
  },
  'region-p34': {
    id: 'region-p34',
    type: 'region',
    name: '요시도 | Yoshido',
    leagueTag: 'AL YOSHIDO',
    mainTeam: '요시도 웨일스 (Y. Whales)',
    minorTeams: '2군: - / 3군: -',
    stadium: '요시도 필드',
    story: '-',
  },
  'region-p35': {
    id: 'region-p35',
    type: 'region',
    name: '바즈넬 | Barsnhel',
    leagueTag: 'AL BARSNHEL',
    mainTeam: '바즈넬 제니스 (B. Zeniths)',
    minorTeams: '2군: - / 3군: -',
    stadium: '바즈넬스 필드',
    story: '-',
  },
  'region-p36': {
    id: 'region-p36',
    type: 'region',
    name: '도르미르 | Dormir',
    leagueTag: 'AL DORMIR',
    mainTeam: '도르미르 코메츠 (D. Comets)',
    minorTeams: '2군: - / 3군: -',
    stadium: '도르미르 스타디움',
    story: '-',
  },
  'region-p37': {
    id: 'region-p37',
    type: 'region',
    name: '로트리반 | Rotreeban',
    leagueTag: 'AL ROTREEBAN',
    mainTeam: '로트리반 가디언즈 (R. Guardians)',
    minorTeams: '2군: - / 3군: -',
    stadium: '로트리반 스타디움',
    story: '-',
  },
  'region-p38': {
    id: 'region-p38',
    type: 'region',
    name: '힐셋 | Hillsett',
    leagueTag: 'AL HILLSETT',
    mainTeam: '힐셋 팬텀즈 (W. Phantoms)',
    minorTeams: '2군: - / 3군: -',
    stadium: '힐셋파크',
    story: '-',
  },
  'region-p39': {
    id: 'region-p39',
    type: 'region',
    name: '카즈닐 | Karsnil',
    leagueTag: 'AL KARSNIL',
    mainTeam: '카즈닐 밸리언츠 (K. Valiants)',
    minorTeams: '2군: - / 3군: -',
    stadium: '카즈닐 돔',
    story: '-',
  },
  'region-p40': {
    id: 'region-p40',
    type: 'region',
    name: '퍼스톨로 | Paustalo',
    leagueTag: 'AL PAUSTALO',
    mainTeam: '퍼스톨로 엔더스 (P. Enders)',
    minorTeams: '2군: - / 3군: -',
    stadium: '퍼스톨로 스타디움',
    story: '-',
  },
  'region-p41': {
    id: 'region-p41',
    type: 'region',
    name: '던틀 | Duntle',
    leagueTag: 'AL DUNTLE',
    mainTeam: '던틀 새턴즈 (D. Saturns)',
    minorTeams: '2군: - / 3군: -',
    stadium: '던틀 파크',
    story: '-',
  },
  'region-p42': {
    id: 'region-p42',
    type: 'region',
    name: '할투스 | Haltous',
    leagueTag: 'AL HALTOUS',
    mainTeam: '할투스 센티넬즈 (H. Sentinels)',
    minorTeams: '2군: - / 3군: -',
    stadium: '할투스 파크',
    story: '-',
  },
  'region-p43': {
    id: 'region-p43',
    type: 'region',
    name: '포드 | Phord',
    leagueTag: 'AL PHORD',
    mainTeam: '포드 펌킨스 (P. Pumpkins)',
    minorTeams: '2군: - / 3군: -',
    stadium: '펌킨랜드',
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

// ==========================================================================
// 세부 지역(region-p4 ~ region-p43) 유도선 시작점 및 방향 설정 구조체
// (점 좌표 cx, cy 및 방향 dirX, dirY를 수정하여 유도선과 라벨 위치 편집 가능)
// ==========================================================================
export interface RegionCalloutConfig {
  cx: number;
  cy: number;
  dirX: number; // 1: 오른쪽, -1: 왼쪽
  dirY: number; // 1: 아래쪽, -1: 위쪽
}

export const REGION_CALLOUT_CONFIGS: Record<string, RegionCalloutConfig> = {
  // 매그놀리아 리그 (ML) 세부 지역 (4 ~ 13)
  'region-p4': { cx: 600, cy: 860, dirX: -1, dirY: 1 },
  'region-p5': { cx: 545, cy: 780, dirX: -1, dirY: 1 },
  'region-p6': { cx: 586, cy: 676, dirX: -1, dirY: -1 },
  'region-p7': { cx: 500, cy: 655, dirX: -1, dirY: -1 },
  'region-p8': { cx: 550, cy: 580, dirX: -1, dirY: -1 },
  'region-p9': { cx: 720, cy: 770, dirX: 1, dirY: 1 },
  'region-p10': { cx: 650, cy: 610, dirX: -1, dirY: -1 },
  'region-p11': { cx: 746, cy: 550, dirX: -1, dirY: -1 },
  'region-p12': { cx: 830, cy: 690, dirX: 1, dirY: 1 },
  'region-p13': { cx: 730, cy: 680, dirX: 1, dirY: 1 },

  // 카멜리아 리그 (CL) 세부 지역 (14 ~ 23)
  'region-p14': { cx: 1050, cy: 630, dirX: 1, dirY: 1 },
  'region-p15': { cx: 990, cy: 650, dirX: 1, dirY: 1 },
  'region-p16': { cx: 930, cy: 650, dirX: 1, dirY: 1 },
  'region-p17': { cx: 860, cy: 630, dirX: 1, dirY: 1 },
  'region-p18': { cx: 790, cy: 610, dirX: -1, dirY: -1 },
  'region-p19': { cx: 996, cy: 600, dirX: 1, dirY: 1 },
  'region-p20': { cx: 960, cy: 586, dirX: 1, dirY: 1 },
  'region-p21': { cx: 900, cy: 570, dirX: -1, dirY: -1 },
  'region-p22': { cx: 826, cy: 565, dirX: -1, dirY: -1 },
  'region-p23': { cx: 1003, cy: 523, dirX: -1, dirY: -1 },

  // 젠티아나 리그 (GL) 세부 지역 (24 ~ 33)
  'region-p24': { cx: 1017, cy: 510, dirX: 1, dirY: 1 },
  'region-p25': { cx: 960, cy: 420, dirX: -1, dirY: -1 },
  'region-p26': { cx: 1350, cy: 300, dirX: 1, dirY: 1 },
  'region-p27': { cx: 1106, cy: 500, dirX: 1, dirY: 1 },
  'region-p28': { cx: 1075, cy: 465, dirX: -1, dirY: -1 },
  'region-p29': { cx: 1140, cy: 450, dirX: -1, dirY: -1 },
  'region-p30': { cx: 1180, cy: 390, dirX: -1, dirY: -1 },
  'region-p31': { cx: 1215, cy: 390, dirX: 1, dirY: 1 },
  'region-p32': { cx: 1240, cy: 320, dirX: -1, dirY: -1 },
  'region-p33': { cx: 1305, cy: 330, dirX: -1, dirY: -1 },

  // 아젤리아 리그 (AL) 세부 지역 (34 ~ 43)
  'region-p34': { cx: 1410, cy: 205, dirX: 1, dirY: -1 },
  'region-p35': { cx: 1222, cy: 290, dirX: -1, dirY: -1 },
  'region-p36': { cx: 1235, cy: 245, dirX: -1, dirY: -1 },
  'region-p37': { cx: 1280, cy: 290, dirX: 1, dirY: 1 },
  'region-p38': { cx: 1310, cy: 264, dirX: -1, dirY: -1 },
  'region-p39': { cx: 1376, cy: 272, dirX: 1, dirY: 1 },
  'region-p40': { cx: 1388, cy: 248, dirX: 1, dirY: -1 },
  'region-p41': { cx: 1340, cy: 204, dirX: -1, dirY: -1 },
  'region-p42': { cx: 1362, cy: 256, dirX: 1, dirY: 1 },
  'region-p43': { cx: 1368, cy: 210, dirX: 1, dirY: -1 },
};
