# WSL 설치 및 Ubuntu 설정 스크립트
# PowerShell에서 관리자 권한으로 실행 필요

Write-Host "=== WSL 설치 가이드 ===" -ForegroundColor Green
Write-Host ""

# 1. WSL 업데이트 확인
Write-Host "1. WSL 업데이트 확인 중..." -ForegroundColor Yellow
wsl --update

# 2. 기본 버전을 WSL 2로 설정
Write-Host "`n2. WSL 기본 버전을 2로 설정 중..." -ForegroundColor Yellow
wsl --set-default-version 2

# 3. Ubuntu 설치
Write-Host "`n3. Ubuntu 설치 중..." -ForegroundColor Yellow
Write-Host "   (설치 중 사용자 이름과 비밀번호를 입력하세요)" -ForegroundColor Cyan
wsl --install -d Ubuntu

Write-Host "`n=== 설치 완료! ===" -ForegroundColor Green
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. 새 터미널 창을 열고 'wsl' 명령어를 실행하세요" -ForegroundColor White
Write-Host "2. 또는 'wsl -d Ubuntu' 명령어로 Ubuntu를 실행하세요" -ForegroundColor White
Write-Host "3. WSL에서 프로젝트 폴더 접근: cd /mnt/c/Users/hanati/Desktop/CODE/web_demo" -ForegroundColor White
Write-Host ""
