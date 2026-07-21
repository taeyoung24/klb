# Krown League Baseball (KLB)

![KLB Banner](docs/assets/banner.png)

## 1. 프로젝트 소개

본 프로젝트는 가상의 야구 리그인 'Krown League Baseball(KLB)'을 소재로 하여, 기술과 콘텐츠가 결합된 거대한 '자동화 IP(지식재산권) 유니버스'를 구축하는 메타미디어콘텐츠(Meta-Media Content) 제작 프로젝트이다. 단순한 시뮬레이션 프로그램 개발을 넘어, 텍스트, 웹, 영상(애니메이션), 그리고 향후 게임과 VR까지 모든 매체를 넘나들며 확장하는 데이터 기반의 융합 미디어 생태계를 조성하는 것을 목표로 한다.

> 📌 **상세 기획 안내**  
> 상세한 기획 내용 및 구체적인 사양은 [KLB 프로젝트 기획 문서 노션](https://app.notion.com/p/KLB-34d2030c521680adbe4dca459eb492e4?source=copy_link)에서 확인하실 수 있습니다.  
> *(※ 해당 문서는 비공개로 설정되어 있으므로 접근 권한 요청이 필요할 수 있습니다.)*

---

## 2. 개발 환경 세팅 (Development Setup)

본 프로젝트는 서비스별 디렉터리로 분리되어 있으며, 각 프로젝트 위치로 이동하여 의존성을 설치하고 실행합니다.

### 📋 사전 요구사항 (Prerequisites)
- **Docker** & **Docker Compose**
- **Python** (패키지 관리자: [uv](https://docs.astral.sh/uv/))
- **Node.js** (패키지 관리자: [pnpm](https://pnpm.io/))

---

### 🐍 백엔드 세팅 (`apps/backend`)

백엔드가 데이터베이스(DB)에 연결할 수 있도록 백엔드를 실행하기 전에 **프로젝트 루트 디렉터리**에서 Docker 컨테이너를 먼저 실행해야 합니다.

```bash
# 1. (프로젝트 루트 위치에서) 로컬 DB 등 인프라 컨테이너 실행
docker compose up -d

# 2. 백엔드 디렉터리로 이동
cd apps/backend

# 3. 환경변수 파일 설정 (env.example 참고하여 .env 생성)
# Linux / macOS / PowerShell / Git Bash:
cp env.example .env
# Windows CMD: copy env.example .env

# 4. 의존성 설치 및 가상환경 동기화
uv sync

# 5. 개발 서버 실행 (필요 시)
uv run main.py

# 💡 참고: 서비스 종료 후 컨테이너 내리기 (프로젝트 루트 위치)
# docker compose down
```

---

### 💻 프론트엔드 세팅 (`apps/web`)

프론트엔드는 `pnpm`을 활용하여 의존성을 관리합니다.

```bash
# 1. 프론트엔드 디렉터리로 이동
cd apps/web

# 2. 환경변수 파일 설정 (.env.*.example 참고하여 .env 파일 생성)
# Linux / macOS / PowerShell / Git Bash:
cp .env.development.example .env.development
# Windows CMD: copy .env.development.example .env.development

# 3. 의존성 설치
pnpm install

# 4. 개발 서버 실행
pnpm dev
```

---

## 3. 배포 방법 및 서버 세팅 (Deployment & Server Setup)

본 프로젝트는 온프레미스(On-Premise) 서버 환경에서 배포 및 운영됩니다. Git 레포지토리 클론 완료 후 `scripts/` 디렉터리의 쉘 스크립트를 활용하여 간편하게 최신 코드 동기화, DB 인프라 관리 및 PM2 서비스를 실행할 수 있습니다.

> 📌 **사전 준수사항**: 서버 환경에 **Docker**, **PM2**, **Python (uv)**, **Node.js (pnpm)**가 설치되어 있어야 합니다.

---

### 1️⃣ 최신 코드 업데이트 (`fetch.sh`)

원격 레포지토리의 최신 소스코드를 강제로 가져와 서버 코드를 덮어씁니다.

```bash
sh scripts/fetch.sh
# 실행 후 적용할 브랜치 명 입력 (예: main)
```

---

### 2️⃣ 데이터베이스 인프라 및 시딩 관리 (`db.sh`)

Docker 컨테이너 기반으로 DB를 인스턴스화하고 시드 데이터를 구축합니다.

```bash
# DB 컨테이너 백그라운드 실행
sh scripts/db.sh start

# DB 상태 확인
sh scripts/db.sh status

# DB 테이블 생성 및 초기 데이터 시딩 (필요 시)
sh scripts/db.sh seed

# DB 컨테이너 중지
sh scripts/db.sh stop
```

---

### 3️⃣ 서비스 빌드 및 PM2 실행 (`run_app.sh`)

백엔드(FastAPI/Uvicorn) 및 프론트엔드(Vite Build & Preview)를 PM2 백그라운드 프로세스로 통합 실행합니다.

```bash
sh scripts/run_app.sh
```

- **백엔드 (klb-backend)**: `http://0.0.0.0:3000`
- **프론트엔드 (klb-web)**: `http://0.0.0.0:5500`

#### 🔍 PM2 모니터링 & 로그 확인
```bash
# 전체 PM2 프로세스 상태 확인
pm2 status

# 로그 실시간 확인
pm2 logs klb-backend
pm2 logs klb-web
```

---

### 4️⃣ 서비스 전체 종료 (`stop_all.sh`)

PM2에 등록되어 실행 중인 백엔드 및 프론트엔드 프로세스를 일괄 삭제 및 정지합니다.

```bash
sh scripts/stop_all.sh
```
