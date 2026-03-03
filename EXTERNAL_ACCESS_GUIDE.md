# AvatarGenWebUI 외부 접속 가이드

`avatar.hanafn-ai.com` 서브도메인을 통해 외부에서 HTTPS로 접속하는 방법입니다.

---

## 1. 접속 URL

설정 완료 후 외부에서 접속할 URL:

```
https://avatar.hanafn-ai.com/
```

- 포트 번호 없이 접속 가능 (443 HTTPS 사용)
- `http://`가 아닌 **`https://`** 사용

---

## 2. 서버 실행 방법 (평소와 동일)

AvatarGenWebUI는 **항상 평소처럼** 실행하면 됩니다. Nginx가 외부 요청을 받아 8000 포트로 전달합니다.

```bash
cd /home/dev/AvatarGenWebUI
source .venv/bin/activate
python app.py
```

- `python app.py` 그대로 사용
- 포트 8000에서 실행 (기본값)
- `--port` 옵션으로 변경하지 않는 한 8000 유지

---

## 3. 초기 설정 (한 번만 수행)

### 3-1. DNS 설정

DNS 관리 화면에서 다음 A 레코드를 추가합니다:

| 타입 | 호스트    | 값         |
|------|-----------|------------|
| A    | avatar    | hanafn-ai.com과 동일한 서버 공인 IP |

- `avatar.hanafn-ai.com`이 서버 IP를 가리키도록 설정
- 전파에 5~30분 걸릴 수 있음

### 3-2. Nginx 설정 스크립트 실행

```bash
cd /home/dev/AvatarGenWebUI
chmod +x setup_avatar_nginx.sh
./setup_avatar_nginx.sh
```

스크립트가 자동으로:

1. DNS 확인
2. SSL 인증서에 `avatar.hanafn-ai.com` 추가
3. Nginx 설정 복사 및 적용
4. Nginx 재시작

---

## 4. 서비스 구조

```
외부 사용자 (브라우저)
    ↓ https://avatar.hanafn-ai.com/ (443)
Nginx (리버스 프록시)
    ↓ http://127.0.0.1:8000
AvatarGenWebUI (python app.py)
```

- livehuman-kr: `https://hanafn-ai.com/` → 8010
- AvatarGenWebUI: `https://avatar.hanafn-ai.com/` → 8000

---

## 5. 문제 해결

### 접속이 안 될 때

1. **AvatarGenWebUI 실행 여부**
   ```bash
   curl http://localhost:8000/health
   ```
   - 200 응답이면 정상

2. **Nginx 상태**
   ```bash
   sudo systemctl status nginx
   ```

3. **Nginx 로그**
   ```bash
   sudo tail -f /var/log/nginx/avatar.hanafn-ai.com.error.log
   ```

### SSL 인증서 수동 확장

```bash
sudo certbot certonly --nginx --expand \
  -d hanafn-ai.com -d www.hanafn-ai.com -d avatar.hanafn-ai.com
```

### Nginx 설정 수동 적용

```bash
sudo cp /home/dev/AvatarGenWebUI/nginx_avatar_hanafn-ai.conf /etc/nginx/sites-available/avatar.hanafn-ai.com
sudo ln -sf /etc/nginx/sites-available/avatar.hanafn-ai.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. 요약

| 항목        | 내용 |
|-------------|------|
| 접속 URL    | `https://avatar.hanafn-ai.com/` |
| 서버 실행   | `python app.py` (평소와 동일) |
| 초기 설정   | `./setup_avatar_nginx.sh` (한 번만) |
| 포트        | 8000 (내부), 443 (외부 HTTPS) |
