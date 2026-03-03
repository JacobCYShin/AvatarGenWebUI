#!/bin/bash
# ========================================
# AvatarGenWebUI - avatar.hanafn-ai.com Nginx 설정 스크립트
# ========================================
# 서브도메인 방식으로 외부 HTTPS 접속 활성화
# ========================================

set -e

echo "=========================================="
echo "  AvatarGenWebUI - Nginx 외부 접속 설정"
echo "=========================================="
echo ""

# 1. DNS 확인
echo "📋 Step 1/6: DNS 확인 중..."
if host avatar.hanafn-ai.com &>/dev/null; then
    AVATAR_IP=$(host avatar.hanafn-ai.com | grep "has address" | head -1 | awk '{print $NF}')
    echo "  ✅ avatar.hanafn-ai.com → $AVATAR_IP"
else
    echo "  ⚠️  avatar.hanafn-ai.com DNS 조회 실패"
    echo ""
    echo "  DNS 설정이 필요합니다. hanafn-ai.com과 동일한 서버 IP로:"
    echo "    - A 레코드: avatar.hanafn-ai.com → [서버 공인 IP]"
    echo ""
    read -p "  DNS 설정을 완료하셨나요? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "  DNS 설정 후 다시 실행해주세요."
        exit 1
    fi
fi
echo ""

# 2. SSL 인증서에 avatar 도메인 추가
echo "🔐 Step 2/6: SSL 인증서에 avatar.hanafn-ai.com 추가 중..."
CERT_PATH="/etc/letsencrypt/live/hanafn-ai.com"
if sudo test -f "$CERT_PATH/fullchain.pem"; then
    if sudo openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -text | grep -q "avatar.hanafn-ai.com"; then
        echo "  ✅ 인증서에 avatar.hanafn-ai.com이 이미 포함되어 있습니다."
    else
        echo "  certbot으로 인증서 확장 중..."
        if ! sudo certbot certonly --nginx --expand \
            -d hanafn-ai.com -d www.hanafn-ai.com -d avatar.hanafn-ai.com \
            --non-interactive --keep-until-expiring 2>/dev/null; then
            echo "  ⚠️  certbot 자동 실행 실패. 수동 실행이 필요할 수 있습니다:"
            echo "     sudo certbot certonly --nginx --expand -d hanafn-ai.com -d www.hanafn-ai.com -d avatar.hanafn-ai.com"
            read -p "  계속 진행할까요? (인증서가 이미 있다면 y): " -n 1 -r
            echo
            [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
        fi
        if sudo openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -text | grep -q "avatar.hanafn-ai.com"; then
            echo "  ✅ 인증서 확장 완료"
        else
            echo "  ❌ 인증서 확장 실패. 수동 실행:"
            echo "     sudo certbot certonly --nginx --expand -d hanafn-ai.com -d www.hanafn-ai.com -d avatar.hanafn-ai.com"
            exit 1
        fi
    fi
else
    echo "  ❌ 기존 SSL 인증서를 찾을 수 없습니다."
    echo "     먼저 livehuman-kr의 setup_nginx.sh로 hanafn-ai.com 인증서를 발급해주세요."
    exit 1
fi
echo ""

# 3. Nginx 설정 파일 복사
echo "📝 Step 3/6: Nginx 설정 파일 복사 중..."
if [ -f /etc/nginx/sites-available/avatar.hanafn-ai.com ]; then
    sudo cp /etc/nginx/sites-available/avatar.hanafn-ai.com \
        /etc/nginx/sites-available/avatar.hanafn-ai.com.backup.$(date +%Y%m%d_%H%M%S)
fi
sudo cp /home/dev/AvatarGenWebUI/nginx_avatar_hanafn-ai.conf /etc/nginx/sites-available/avatar.hanafn-ai.com
echo "  ✅ 복사 완료"
echo ""

# 4. sites-enabled 링크 생성
echo "🔗 Step 4/6: sites-enabled 링크 생성 중..."
sudo ln -sf /etc/nginx/sites-available/avatar.hanafn-ai.com /etc/nginx/sites-enabled/
echo "  ✅ 완료"
echo ""

# 5. Nginx 설정 테스트
echo "🧪 Step 5/6: Nginx 설정 테스트 중..."
if sudo nginx -t; then
    echo "  ✅ 설정이 올바릅니다."
else
    echo "  ❌ Nginx 설정 오류. 위 메시지를 확인해주세요."
    exit 1
fi
echo ""

# 6. Nginx 재시작
echo "🔄 Step 6/6: Nginx 재시작 중..."
sudo systemctl reload nginx
if sudo systemctl is-active --quiet nginx; then
    echo "  ✅ Nginx가 정상적으로 실행 중입니다."
else
    echo "  ❌ Nginx 재시작 실패"
    sudo systemctl status nginx
    exit 1
fi
echo ""

echo "=========================================="
echo "  ✅ avatar.hanafn-ai.com 설정 완료!"
echo "=========================================="
echo ""
echo "📌 접속 URL:"
echo "   https://avatar.hanafn-ai.com/"
echo ""
echo "📌 서버 실행 (평소와 동일):"
echo "   cd /home/dev/AvatarGenWebUI"
echo "   source .venv/bin/activate"
echo "   python app.py"
echo ""
echo "   AvatarGenWebUI가 8000 포트에서 실행 중이어야 합니다."
echo ""
echo "📌 로그 확인:"
echo "   sudo tail -f /var/log/nginx/avatar.hanafn-ai.com.access.log"
echo "   sudo tail -f /var/log/nginx/avatar.hanafn-ai.com.error.log"
echo ""
