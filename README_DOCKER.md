# Docker 환경에서 실행하기

## 🚀 빠른 시작

### 방법 1: Docker Host 네트워크 모드 (권장)

모든 컨테이너가 호스트의 네트워크를 공유합니다. 가장 간단한 방법입니다.

```bash
# TTS 서버 실행
docker run -d --network host \
  --gpus all \
  --name tts-server \
  tts-image:latest

# Video Generation 서버 실행
docker run -d --network host \
  --gpus all \
  --name video-server \
  video-gen-image:latest

# Web Demo 실행
docker run -d --network host \
  --name web-demo \
  -v $(pwd)/outputs:/app/outputs \
  web-demo:latest
```

### 방법 2: host.docker.internal 사용 (Windows/Mac/WSL)

TTS/Video 서버가 호스트에서 실행 중이고, Web Demo만 Docker로 실행할 때:

```bash
# Web Demo 빌드
docker build -t web-demo .

# Web Demo 실행 (WSL에서)
docker run -d \
  --name web-demo \
  -p 8000:8000 \
  -e TTS_API_URL="http://host.docker.internal:7009/tts" \
  -e VIDEO_API_URL="http://host.docker.internal:8001/synthesize" \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/outputs:/app/outputs \
  web-demo:latest
```

### 방법 3: Docker Compose 사용

```bash
# docker-compose.yml 사용
docker-compose up -d

# 로그 확인
docker-compose logs -f web-demo

# 중지
docker-compose down
```

### 방법 4: Docker 네트워크 생성 (모든 서비스 Docker로 실행)

```bash
# 네트워크 생성
docker network create virtual-human-network

# TTS 서버 실행
docker run -d \
  --network virtual-human-network \
  --name tts-server \
  --gpus all \
  -p 7009:7009 \
  tts-image:latest

# Video Generation 서버 실행
docker run -d \
  --network virtual-human-network \
  --name video-server \
  --gpus all \
  -p 8001:8001 \
  video-gen-image:latest

# Web Demo 실행
docker run -d \
  --network virtual-human-network \
  --name web-demo \
  -p 8000:8000 \
  -e TTS_API_URL="http://tts-server:7009/tts" \
  -e VIDEO_API_URL="http://video-server:8001/synthesize" \
  -v $(pwd)/outputs:/app/outputs \
  web-demo:latest
```

## 🔍 트러블슈팅

### 1. "Connection refused" 에러

**원인**: Web Demo 컨테이너가 다른 서버에 접근할 수 없음

**해결책**:
- `localhost` 대신 `host.docker.internal` 사용 (Windows/Mac/WSL)
- Linux에서는 `--add-host=host.docker.internal:host-gateway` 추가
- 또는 모든 서비스를 같은 Docker 네트워크에 연결

### 2. 비디오가 생성되지만 웹에서 표시되지 않음

**원인**: 볼륨 마운트가 제대로 되지 않았거나, 파일 권한 문제

**해결책**:
```bash
# outputs 디렉토리 권한 확인
ls -la outputs/

# 컨테이너 로그 확인
docker logs web-demo

# 컨테이너 내부 확인
docker exec -it web-demo ls -la /app/outputs/
```

### 3. 환경 변수가 적용되지 않음

**원인**: .env 파일이 제대로 로드되지 않음

**해결책**:
```bash
# 환경 변수 직접 전달
docker run -d \
  -e TTS_API_URL="http://your-tts-url:7009/tts" \
  -e VIDEO_API_URL="http://your-video-url:8001/synthesize" \
  ...
```

## 📝 현재 구성 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 네트워크 확인
docker network ls

# 특정 컨테이너의 환경 변수 확인
docker exec web-demo env | grep API_URL

# 컨테이너 내부에서 다른 서버 연결 테스트
docker exec -it web-demo curl http://host.docker.internal:7009/
docker exec -it web-demo curl http://host.docker.internal:8001/health
```

## 🎯 권장 구성

**개발 환경**: 
- TTS/Video 서버: 호스트에서 직접 실행 (GPU 사용 편리)
- Web Demo: Docker 또는 호스트에서 실행

**프로덕션 환경**:
- 모든 서비스: Docker 네트워크로 연결하여 실행
- docker-compose를 사용한 오케스트레이션

