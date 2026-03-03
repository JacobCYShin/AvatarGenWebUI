#!/bin/bash
# ========================================
# AvatarGenWebUI 서버 종료 스크립트
# ========================================
# livehuman-kr 서버(melo, whisper, live)에는 영향 없음
# ========================================

echo "🛑 AvatarGenWebUI 서버를 종료합니다..."
echo ""

# 1. Screen 세션 종료
echo "📺 Screen 세션 종료 중..."
screen -S avatar_melo -X quit 2>/dev/null && echo "  ✓ avatar_melo (MeloTTS) 종료" || true
screen -S avatar_video -X quit 2>/dev/null && echo "  ✓ avatar_video (Video Gen) 종료" || true
screen -S avatar_web -X quit 2>/dev/null && echo "  ✓ avatar_web (AvatarGenWebUI) 종료" || true

sleep 2

# 2. 남은 프로세스 정리 (AvatarGenWebUI 관련만)
echo ""
echo "🔪 남은 프로세스 정리 중..."
pkill -f "video_server.py" 2>/dev/null && echo "  ✓ Video Generation 프로세스 종료" || true
# app.py는 livehuman-kr과 구분 불가 → screen 종료만 사용

sleep 1

echo ""
echo "✅ AvatarGenWebUI 서버가 모두 종료되었습니다."
echo ""
echo "📋 남은 Screen 세션:"
screen -ls 2>/dev/null || echo "  (없음)"
echo ""
