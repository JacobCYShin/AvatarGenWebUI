# 폐쇄망 배포 가이드

이 문서는 인터넷이 없는 폐쇄망 환경에서 웹 데모를 실행하기 위한 준비 과정을 설명합니다.

## 1. 사전 준비 (인터넷 연결된 환경에서)

### 1.1 Tailwind CSS 다운로드

폐쇄망으로 이관하기 전에 **반드시** Tailwind CSS를 다운로드해야 합니다.

#### 방법 1: Python 스크립트 사용 (권장)

```bash
# 프로젝트 루트에서
python download_tailwind.py
```

#### 방법 2: Bash 스크립트 사용

```bash
# 프로젝트 루트에서
chmod +x download_tailwind.sh
./download_tailwind.sh
```

#### 방법 3: 수동 다운로드

1. 브라우저에서 https://cdn.tailwindcss.com 접속
2. 페이지의 JavaScript 코드를 모두 복사 (Ctrl+A, Ctrl+C)
3. `static/tailwind.min.js` 파일로 저장

### 1.2 다운로드 확인

```bash
ls -lh static/tailwind.min.js
```

파일이 존재하고 크기가 100KB 이상이면 정상입니다.

## 2. 폐쇄망으로 이관할 파일 목록

다음 파일/폴더를 **전체** 복사해야 합니다:

```
web_demo/
├── app.py                    # 메인 서버 애플리케이션
├── requirements.txt          # Python 의존성
├── start.sh                  # 서버 시작 스크립트
├── static/
│   ├── hana_logo.png        # 하나금융 로고
│   └── tailwind.min.js      # ⚠️ 중요: 반드시 다운로드 필요!
├── templates/
│   └── index.html           # 웹 UI (CDN → 로컬 경로로 수정됨)
├── outputs/                 # 생성된 비디오 저장 폴더
└── temp/                    # 임시 파일 폴더
```

### ⚠️ 필수 확인 사항

**폐쇄망으로 이관하기 전 체크리스트:**

- [ ] `static/tailwind.min.js` 파일이 존재하는가?
- [ ] `static/tailwind.min.js` 파일 크기가 100KB 이상인가?
- [ ] `templates/index.html`에서 CDN 링크가 로컬 경로로 변경되었는가?
  ```html
  <!-- 변경 전 (CDN) -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- 변경 후 (로컬) ✓ -->
  <script src="/static/tailwind.min.js"></script>
  ```

## 3. 폐쇄망 환경에서 실행

### 3.1 의존성 설치

```bash
cd web_demo
pip install -r requirements.txt
```

### 3.2 서버 실행

```bash
# 방법 1: 스크립트 사용
./start.sh

# 방법 2: 직접 실행
python app.py
```

### 3.3 접속 확인

- 웹 브라우저에서 `http://localhost:8000` 접속
- UI가 정상적으로 표시되는지 확인 (버튼, 입력창 등)

## 4. 문제 해결

### UI가 깨져 보이는 경우

**증상:** 텍스트만 보이고 스타일이 전혀 적용되지 않음

**원인:** `static/tailwind.min.js` 파일이 없거나 로드되지 않음

**해결:**
1. 브라우저 개발자 도구(F12) 열기
2. Console 탭에서 에러 확인
3. 일반적인 에러:
   ```
   GET http://localhost:8000/static/tailwind.min.js 404 (Not Found)
   ```

4. 해결 방법:
   - `static/tailwind.min.js` 파일이 있는지 확인
   - 파일이 없으면 인터넷 연결된 환경에서 다시 다운로드
   - 서버 재시작

### Tailwind가 로드되지만 스타일이 적용되지 않는 경우

**증상:** Console에 에러는 없지만 UI가 여전히 깨짐

**원인:** `tailwind.min.js` 파일이 손상되었거나 불완전함

**해결:**
1. `static/tailwind.min.js` 삭제
2. 인터넷 연결된 환경에서 재다운로드
3. 파일 크기가 150-200KB 정도인지 확인

## 5. 시스템 구성

### 전체 아키텍처

```
┌─────────────────┐
│  웹 브라우저     │
│  (localhost:8000)│
└────────┬────────┘
         │
┌────────▼────────┐
│  웹 서버 (FastAPI)│
│  포트: 8000      │
└────────┬────────┘
         │
         ├─────► TTS 서버 (localhost:7009)
         │
         └─────► 비디오 생성 서버 (localhost:8001)
```

### 포트 사용

- **8000**: 웹 UI 서버 (이 애플리케이션)
- **7009**: TTS (음성 합성) 서버
- **8001**: 비디오 생성 서버

## 6. 추가 참고사항

### 폐쇄망 보안 고려사항

1. **외부 CDN 의존성 제거 완료**
   - Tailwind CSS: 로컬 파일로 변경 ✓
   
2. **확인된 로컬 리소스**
   - `/static/hana_logo.png`: 하나금융 로고
   - `/static/tailwind.min.js`: Tailwind CSS

3. **외부 API 호출 없음**
   - 모든 API는 localhost 내부 통신만 사용

### 성능 최적화

- Tailwind CSS 로컬 파일: 약 150-200KB
- 초기 로딩 시간: 1-2초 (인터넷 연결 불필요)
- 캐싱: 브라우저가 자동으로 `tailwind.min.js` 캐싱

## 7. 연락처

문제 발생 시:
- 로그 확인: 서버 실행 터미널 출력
- 브라우저 Console 확인: F12 → Console 탭
- Network 탭 확인: F12 → Network 탭에서 실패한 리소스 확인

