# WSL 설치 가이드

Windows에서 Linux 환경을 사용하기 위한 WSL(Windows Subsystem for Linux) 설치 가이드입니다.

## 📋 사전 요구사항

- Windows 10 버전 2004 이상 (현재: Windows 10 10.0.19042)
- 관리자 권한

## 🚀 빠른 설치 방법

### 방법 1: PowerShell 스크립트 실행 (권장)

1. **PowerShell을 관리자 권한으로 실행**
   - Windows 키 + X → "Windows PowerShell (관리자)" 선택
   - 또는 검색에서 "PowerShell" → 우클릭 → "관리자 권한으로 실행"

2. **스크립트 실행**
   ```powershell
   cd C:\Users\hanati\Desktop\CODE\web_demo
   .\install_wsl.ps1
   ```

3. **Ubuntu 설정**
   - 설치 완료 후 Ubuntu 창이 열리면 사용자 이름과 비밀번호를 설정합니다

### 방법 2: 수동 설치

1. **WSL 업데이트**
   ```powershell
   wsl --update
   ```

2. **기본 버전을 WSL 2로 설정**
   ```powershell
   wsl --set-default-version 2
   ```

3. **Ubuntu 설치**
   ```powershell
   wsl --install -d Ubuntu
   ```

4. **설치 확인**
   ```powershell
   wsl --list --verbose
   ```

## 🔧 WSL 2 사용 확인

설치 후 WSL 버전 확인:
```powershell
wsl --list --verbose
```

출력에서 Ubuntu가 VERSION 2로 표시되어야 합니다.

만약 VERSION 1로 표시되면:
```powershell
wsl --set-version Ubuntu 2
```

## 📁 프로젝트 접근 방법

WSL에서 Windows 파일 시스템 접근:

```bash
# Windows 파일 시스템은 /mnt/ 드라이브에 마운트됨
cd /mnt/c/Users/hanati/Desktop/CODE/web_demo

# 또는 홈 디렉토리에서 심볼릭 링크 생성 (선택사항)
cd ~
ln -s /mnt/c/Users/hanati/Desktop/CODE/web_demo ./web_demo
```

## 🐍 Python 가상환경 설정 (WSL 내)

프로젝트를 WSL에서 실행하려면:

```bash
# 1. 프로젝트 디렉토리로 이동
cd /mnt/c/Users/hanati/Desktop/CODE/web_demo

# 2. Python 가상환경 생성
python3 -m venv .venv

# 3. 가상환경 활성화
source .venv/bin/activate

# 4. 패키지 설치
pip install -r requirements.txt

# 5. 서버 실행
bash start.sh
```

## 🔌 GPU 사용 설정 (선택사항)

WSL 2에서 NVIDIA GPU를 사용하려면:

1. **NVIDIA 드라이버 설치** (Windows에 설치)
   - [NVIDIA 드라이버 다운로드](https://www.nvidia.com/Download/index.aspx)
   - WSL용 드라이버를 설치해야 함

2. **CUDA Toolkit 설치** (WSL 내)
   ```bash
   # Ubuntu에서
   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
   sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
   wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda-repo-wsl-ubuntu-12-3-local_12.3.0-1_amd64.deb
   sudo dpkg -i cuda-repo-wsl-ubuntu-12-3-local_12.3.0-1_amd64.deb
   sudo cp /var/cuda-repo-wsl-ubuntu-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
   sudo apt-get update
   sudo apt-get -y install cuda
   ```

3. **설치 확인**
   ```bash
   nvidia-smi
   ```

## ⚡ 유용한 명령어

```bash
# WSL에서 Windows 명령어 실행
cmd.exe /c "dir"

# Windows에서 WSL 명령어 실행
wsl ls -la

# WSL 종료
wsl --shutdown

# 특정 배포판 실행
wsl -d Ubuntu

# WSL 기본 배포판 변경
wsl --set-default Ubuntu
```

## 🐛 문제 해결

### 문제 1: "WSL 2 requires an update to its kernel component"
해결:
```powershell
# WSL 업데이트
wsl --update
```

### 문제 2: "This operation can only be performed on a system that is running"
해결:
- 컴퓨터 재시작 후 다시 시도

### 문제 3: 파일 권한 문제
해결:
- Windows 파일 시스템(/mnt/c)에서 파일을 직접 수정하는 것보다, WSL 내부로 복사하여 작업하는 것을 권장
```bash
# 프로젝트를 WSL 홈 디렉토리로 복사
cp -r /mnt/c/Users/hanati/Desktop/CODE/web_demo ~/web_demo
cd ~/web_demo
```

### 문제 4: 느린 파일 I/O
해결:
- `/etc/wsl.conf` 파일 생성 및 설정:
```bash
sudo nano /etc/wsl.conf
```

다음 내용 추가:
```ini
[automount]
enabled = true
options = "metadata,umask=22,fmask=11"
```

WSL 재시작:
```powershell
wsl --shutdown
```

## 📚 추가 자료

- [Microsoft WSL 공식 문서](https://learn.microsoft.com/ko-kr/windows/wsl/)
- [WSL 2 GPU 지원](https://learn.microsoft.com/ko-kr/windows/wsl/tutorials/gpu-compute)

## ✅ 체크리스트

- [ ] WSL 2 설치 완료
- [ ] Ubuntu 배포판 설치 완료
- [ ] WSL 버전 확인 (VERSION 2)
- [ ] 프로젝트 디렉토리 접근 확인
- [ ] Python 가상환경 설정 (선택사항)
- [ ] GPU 설정 (필요시)

---

설치 중 문제가 발생하면 이 문서의 문제 해결 섹션을 참고하세요.
