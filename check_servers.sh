#!/bin/bash
# ========================================
# AvatarGenWebUI 서버 상태 확인 스크립트
# ========================================

INTERVAL=5
MODE="watch"

usage() {
    echo "사용법: $0 [--watch] [--interval SEC] [--once]"
    echo "  --watch         지속 모니터링 (기본값)"
    echo "  --interval SEC  갱신 주기 (기본 5초)"
    echo "  --once          1회만 실행"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --watch)
            MODE="watch"
            shift
            ;;
        --once)
            MODE="once"
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "알 수 없는 옵션: $1"
            usage
            exit 1
            ;;
    esac
done

check_once() {
    echo "🔍 AvatarGenWebUI 서버 상태 ($(date '+%Y-%m-%d %H:%M:%S'))"
    echo ""

    # 1. Screen 세션
    echo "📺 Screen 세션:"
    screen -ls 2>/dev/null | grep -q "avatar_melo" && echo "  ✅ avatar_melo (MeloTTS)" || echo "  ❌ avatar_melo 없음"
    screen -ls 2>/dev/null | grep -q "avatar_video" && echo "  ✅ avatar_video (Video Gen)" || echo "  ❌ avatar_video 없음"
    screen -ls 2>/dev/null | grep -q "avatar_web" && echo "  ✅ avatar_web (AvatarGenWebUI)" || echo "  ❌ avatar_web 없음"

    # 2. 포트 확인
    echo ""
    echo "🔌 포트 사용:"
    lsof -i:7009 >/dev/null 2>&1 && echo "  ✅ 7009 (MeloTTS)" || echo "  ❌ 7009 미사용"
    lsof -i:8001 >/dev/null 2>&1 && echo "  ✅ 8001 (Video Gen)" || echo "  ❌ 8001 미사용"
    lsof -i:8000 >/dev/null 2>&1 && echo "  ✅ 8000 (AvatarGenWebUI)" || echo "  ❌ 8000 미사용"

    # 3. 헬스 체크 (선택)
    echo ""
    echo "🏥 헬스 체크:"
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "200" && echo "  ✅ AvatarGenWebUI (8000) 응답 정상" || echo "  ⚠️  AvatarGenWebUI (8000) 응답 없음"
    curl -s -o /dev/null -w "%{http_code}" http://localhost:7009/ 2>/dev/null | grep -q "200" && echo "  ✅ MeloTTS (7009) 응답 정상" || echo "  ⚠️  MeloTTS (7009) 응답 없음"
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null | grep -q "200" && echo "  ✅ Video Gen (8001) 응답 정상" || echo "  ⚠️  Video Gen (8001) 응답 없음"

    echo ""
    echo "💡 Tip: screen -r <세션명> 으로 로그 확인"
}

if [[ "$MODE" == "once" ]]; then
    check_once
    exit 0
fi

while true; do
    clear
    check_once
    echo ""
    echo "⏱️  ${INTERVAL}초마다 갱신 (중지: Ctrl+C)"
    sleep "$INTERVAL"
done
