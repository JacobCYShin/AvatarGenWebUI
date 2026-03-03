#!/bin/bash
# ========================================
# AvatarGenWebUI 전체 서버 자동 시작 스크립트
# ========================================
# TTS(7009) + Video Generation(8001) + Web Demo(8000)
# ========================================

echo "🚀 AvatarGenWebUI 서버를 시작합니다..."
echo ""

# 1. MeloTTS 서버 (7009) - 이미 실행 중이면 건너뜀
echo "🔊 MeloTTS 서버 확인 중..."
if lsof -i:7009 >/dev/null 2>&1; then
    echo "  ✅ MeloTTS 이미 실행 중 (포트 7009) - 건너뜀"
else
    echo "  MeloTTS 서버 시작..."
    screen -dmS avatar_melo bash -c "
        cd /home/dev/MeloTTS-server && \
        source .venv/bin/activate && \
        uvicorn tts_server:app --host 0.0.0.0 --port 7009
    "
    echo "  ✅ MeloTTS 시작 완료 (포트: 7009)"
fi

sleep 2

# 2. Video Generation 서버 (8001)
echo ""
echo "🎬 Video Generation 서버 시작..."
screen -dmS avatar_video bash -c "
    cd /home/dev/VideoGenerationServer && \
    source /home/dev/livehuman-kr/.venv/bin/activate && \
    python video_server.py
"
echo "✅ Video Generation 서버 시작 완료 (포트: 8001)"

sleep 3

# 3. AvatarGenWebUI (8000)
echo ""
echo "🌐 AvatarGenWebUI 웹 서버 시작..."
screen -dmS avatar_web bash -c "
    cd /home/dev/AvatarGenWebUI && \
    source .venv/bin/activate && \
    python app.py
"
echo "✅ AvatarGenWebUI 시작 완료 (포트: 8000)"

sleep 2

echo ""
echo "=========================================="
echo "✅ AvatarGenWebUI 서버가 모두 시작되었습니다!"
echo "=========================================="
echo ""
echo "📋 실행 중인 서버:"
echo "  ✅ MeloTTS        (7009)"
echo "  ✅ Video Gen      (8001)"
echo "  ✅ AvatarGenWebUI (8000)"
echo ""
echo "📋 Screen 세션:"
screen -ls | grep -E "avatar_melo|avatar_video|avatar_web" || true
echo ""
echo "🌐 접속 URL:"
echo "  로컬:     http://localhost:8000"
echo "  외부:     https://avatar.hanafn-ai.com/"
echo ""
echo "🔍 서버 로그 확인:"
echo "  - MeloTTS:        screen -r avatar_melo"
echo "  - Video Gen:      screen -r avatar_video"
echo "  - AvatarGenWebUI: screen -r avatar_web"
echo ""
echo "🛑 종료: ./stop_all_servers.sh"
echo "🔍 상태 확인: ./check_servers.sh"
echo "=========================================="
