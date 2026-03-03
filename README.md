# 하나금융융합기술원 AI 아바타

텍스트를 입력하면 AI 아바타가 말하는 영상을 생성하는 시스템입니다.

## ⚠️ 폐쇄망 배포

**폐쇄망(인터넷 없는 환경)에 배포하시나요?**

폐쇄망 환경에서는 외부 CDN 접근이 불가능하므로 사전 준비가 필요합니다:

1. **인터넷 연결된 환경에서** Tailwind CSS를 다운로드:
   ```bash
   python download_tailwind.py
   ```

2. 폐쇄망으로 전체 폴더 복사

자세한 내용은 다음 문서를 참고하세요:
- **빠른 시작**: `빠른_시작_가이드.txt`
- **상세 가이드**: `OFFLINE_SETUP.md`
- **체크리스트**: `폐쇄망_이관_체크리스트.md`
- **테스트**: `TESTING.md`

## 📋 시스템 구조

```
┌─────────────┐      ┌─────────────┐      ┌──────────────────┐
│  Web Demo   │─────▶│  TTS Server │      │ Video Generation │
│  (포트 8000)  │      │  (포트 7009)  │      │   Server         │
│             │      │             │      │   (포트 8001)      │
└─────────────┘      └─────────────┘      └──────────────────┘
                            │                       ▲
                            └───────────────────────┘
                                  오디오 전달
```

## 🚀 빠른 시작

### 1. 한 번에 실행 (권장)

```bash
cd /home/dev/AvatarGenWebUI
./start_all_servers.sh
```

서버 종료: `./stop_all_servers.sh`  
상태 확인: `./check_servers.sh`

### 2. 개별 실행 (수동)

```bash
# 1. TTS 서버 실행 (별도 터미널)
cd /home/dev/MeloTTS-server
source .venv/bin/activate
uvicorn tts_server:app --host 0.0.0.0 --port 7009

# 2. Video Generation 서버 실행 (별도 터미널)
cd /home/dev/VideoGenerationServer
source /home/dev/livehuman-kr/.venv/bin/activate
python video_server.py

# 3. Web Demo 실행 (현재 터미널)
cd /home/dev/AvatarGenWebUI
source .venv/bin/activate
python app.py
```

브라우저에서 http://localhost:8000 접속

### 3. Docker 환경에서 실행

#### 옵션 A: Host 네트워크 모드 (가장 간단)

```bash
docker run -d --network host \
  --name web-demo \
  -v $(pwd)/outputs:/app/outputs \
  web-demo:latest
```

#### 옵션 B: 환경 변수 사용

```bash
# 환경 변수 설정
export TTS_API_URL="http://host.docker.internal:7009/tts"
export VIDEO_API_URL="http://host.docker.internal:8001/synthesize"

# 실행
bash start.sh

# 또는 Docker로
docker run -d \
  -p 8000:8000 \
  -e TTS_API_URL="http://host.docker.internal:7009/tts" \
  -e VIDEO_API_URL="http://host.docker.internal:8001/synthesize" \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/outputs:/app/outputs \
  web-demo:latest
```

자세한 내용은 [README_DOCKER.md](./README_DOCKER.md) 참고

## 🔧 환경 설정

### 환경 변수

- `TTS_API_URL`: TTS 서버 URL (기본값: `http://localhost:7009/tts`)
- `VIDEO_API_URL`: 비디오 생성 서버 URL (기본값: `http://localhost:8001/synthesize`)

### 설정 방법

```bash
# Bash
export TTS_API_URL="http://your-tts-server:7009/tts"
export VIDEO_API_URL="http://your-video-server:8001/synthesize"
bash start.sh

# PowerShell (Windows)
$env:TTS_API_URL="http://your-tts-server:7009/tts"
$env:VIDEO_API_URL="http://your-video-server:8001/synthesize"
bash start.sh
```

## 📁 디렉토리 구조

```
web_demo/
├── app.py                 # FastAPI 애플리케이션
├── start.sh              # 시작 스크립트
├── requirements.txt      # Python 패키지
├── Dockerfile           # Docker 이미지 빌드
├── docker-compose.yml   # Docker Compose 설정
├── README.md            # 이 파일
├── README_DOCKER.md     # Docker 가이드
├── templates/           # HTML 템플릿
│   └── index.html
├── static/              # 정적 파일
├── outputs/             # 생성된 비디오 저장
└── temp/                # 임시 파일
```

## 🎨 기능

### 음성 모델
- **pds_natural**: 자연스러운 목소리
- **pds_announcer**: 아나운서 목소리

### 고급 설정
- **Audio 전환 프레임**: 입 열림/닫힘 전환 부드러움 (권장: 4-5)
- **Frame 전환 프레임**: 영상 블렌딩 부드러움 (권장: 3)
- **보간 방법**: Cosine, Linear, Sigmoid, Ease-in-out

## 🔍 트러블슈팅

### 1. "Connection refused" 에러

**문제**: Web Demo가 다른 서버에 연결할 수 없음

**해결**:
```bash
# 서버 상태 확인
curl http://localhost:7009/
curl http://localhost:8001/health

# Docker 환경인 경우
export TTS_API_URL="http://host.docker.internal:7009/tts"
export VIDEO_API_URL="http://host.docker.internal:8001/synthesize"
```

### 2. 비디오가 생성되지만 웹에서 표시되지 않음

**문제**: 파일이 생성되었지만 브라우저에서 재생되지 않음

**해결**:
```bash
# 파일 확인
ls -la outputs/

# 파일 크기 확인 (0KB가 아닌지)
du -h outputs/*.mp4

# 브라우저 콘솔 확인 (F12)
# 네트워크 탭에서 비디오 파일 요청 확인
```

### 3. "비디오 파일이 오디오만 포함"

**문제**: MP4 파일이 생성되었지만 비디오 트랙이 없음

**원인**: 
- Video Generation 서버가 제대로 작동하지 않음
- ffmpeg가 오디오만 합성했을 수 있음

**해결**:
```bash
# Video Generation 서버 로그 확인
# 비디오 inference가 제대로 실행되었는지 확인

# 파일 정보 확인
ffprobe outputs/video_xxx.mp4

# 비디오 스트림이 있는지 확인
# Stream #0:0: Video 가 있어야 함
```

### 4. 환경 변수가 적용되지 않음

**문제**: API URL을 변경했지만 여전히 localhost에 연결

**해결**:
```bash
# 환경 변수 확인
echo $TTS_API_URL
echo $VIDEO_API_URL

# 확실히 설정
export TTS_API_URL="http://host.docker.internal:7009/tts"
export VIDEO_API_URL="http://host.docker.internal:8001/synthesize"

# 서버 재시작
```

## 📊 헬스 체크

서버 상태 확인:

```bash
# Web Demo
curl http://localhost:8000/health

# TTS 서버
curl http://localhost:7009/

# Video Generation 서버
curl http://localhost:8001/health
```

## 🛠️ 개발

### 로컬 개발 환경 설정

```bash
# Python 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### API 엔드포인트

- `GET /`: 메인 페이지
- `POST /api/tts`: TTS 생성 (개별 테스트용)
- `POST /api/generate_video`: 비디오 생성 (TTS + 비디오)
- `GET /health`: 헬스 체크
- `GET /outputs/{filename}`: 생성된 비디오 파일

## 📝 라이센스

내부 프로젝트용

## 🤝 기여

이슈나 개선 사항은 팀에 문의하세요.
