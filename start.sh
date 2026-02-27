#!/bin/bash

echo "======================================"
echo "하나금융융합기술원 AI 아바타 시작"
echo "======================================"

# 컬러 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# TTS 서버 확인
echo ""
echo "🔍 TTS 서버 상태 확인 중..."
if curl -s http://localhost:7009/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TTS 서버가 실행 중입니다 (포트 7009)${NC}"
else
    echo -e "${RED}⚠️  TTS 서버가 실행되지 않았습니다!${NC}"
    echo ""
    echo "TTS 서버를 먼저 실행해주세요:"
    echo "  cd ../TTS_server_only"
    echo "  source /database/venv/melotts/bin/activate"
    echo "  uvicorn tts_server:app --host 0.0.0.0 --port 7009"
    echo ""
    read -p "그래도 계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# GPU 확인
echo ""
echo "🎮 GPU 상태 확인 중..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader | while read line; do
        echo "  GPU: $line"
    done
else
    echo -e "${YELLOW}⚠️  nvidia-smi를 찾을 수 없습니다. GPU가 없거나 CUDA가 설치되지 않았을 수 있습니다.${NC}"
fi

# python3 및 의존성 확인
echo ""
echo "🐍 python3 환경 확인 중..."
python3 --version

# 필요한 디렉토리 생성
echo ""
echo "📁 디렉토리 구조 확인 중..."
mkdir -p outputs
mkdir -p temp
mkdir -p static
mkdir -p templates
echo -e "${GREEN}✅ 디렉토리 준비 완료${NC}"

# 환경 변수 확인 및 설정
echo ""
echo "⚙️  API 서버 설정 확인 중..."
if [ -z "$TTS_API_URL" ]; then
    export TTS_API_URL="http://localhost:7009/tts"
    echo "  TTS API: $TTS_API_URL (기본값)"
else
    echo "  TTS API: $TTS_API_URL (환경 변수)"
fi

if [ -z "$VIDEO_API_URL" ]; then
    export VIDEO_API_URL="http://localhost:8001/synthesize"
    echo "  Video API: $VIDEO_API_URL (기본값)"
else
    echo "  Video API: $VIDEO_API_URL (환경 변수)"
fi

echo ""
echo -e "${YELLOW}💡 Docker 환경에서 실행하는 경우:${NC}"
echo "   export TTS_API_URL='http://host.docker.internal:7009/tts'"
echo "   export VIDEO_API_URL='http://host.docker.internal:8001/synthesize'"
echo "   또는 README_DOCKER.md를 참고하세요"

# 서버 시작
echo ""
echo "======================================"
echo "🚀 웹 서버 시작 중..."
echo "======================================"
echo ""
echo -e "${GREEN}📍 웹 인터페이스: http://localhost:8000${NC}"
echo -e "${YELLOW}⏹  종료하려면 Ctrl+C 를 누르세요${NC}"
echo ""

# FastAPI 서버 실행
python3 app.py

