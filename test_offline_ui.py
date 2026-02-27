#!/usr/bin/env python3
"""
폐쇄망 UI 테스트 스크립트
웹 서버가 실행 중인 상태에서 UI가 정상 작동하는지 확인합니다.
"""
import sys
import time
import requests
from pathlib import Path

def test_server_health(base_url="http://localhost:8000"):
    """서버 헬스 체크"""
    print("=" * 70)
    print("1. 서버 헬스 체크")
    print("=" * 70)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 서버 응답 정상")
            print(f"  상태: {data.get('status')}")
            print(f"  TTS 서버: {data.get('tts_server')}")
            print(f"  비디오 서버: {data.get('video_server')}")
            return True
        else:
            print(f"✗ 서버 응답 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 서버 연결 실패: {e}")
        print(f"  → http://localhost:8000 에서 서버가 실행 중인지 확인하세요")
        return False

def test_static_files(base_url="http://localhost:8000"):
    """정적 파일 로드 테스트"""
    print()
    print("=" * 70)
    print("2. 정적 파일 로드 테스트")
    print("=" * 70)
    
    files_to_check = [
        ("/static/tailwind.min.js", "Tailwind CSS", 100000),  # 최소 100KB
        ("/static/hana_logo.png", "하나금융 로고", 1000),     # 최소 1KB
    ]
    
    all_ok = True
    
    for path, name, min_size in files_to_check:
        try:
            response = requests.get(f"{base_url}{path}", timeout=5)
            if response.status_code == 200:
                size = len(response.content)
                size_kb = size / 1024
                
                if size >= min_size:
                    print(f"✓ {name}: {size_kb:.1f} KB")
                else:
                    print(f"✗ {name}: 파일이 너무 작음 ({size_kb:.1f} KB < {min_size/1024:.1f} KB)")
                    all_ok = False
            else:
                print(f"✗ {name}: HTTP {response.status_code}")
                all_ok = False
        except Exception as e:
            print(f"✗ {name}: {e}")
            all_ok = False
    
    return all_ok

def test_main_page(base_url="http://localhost:8000"):
    """메인 페이지 로드 테스트"""
    print()
    print("=" * 70)
    print("3. 메인 페이지 로드 테스트")
    print("=" * 70)
    
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            html = response.text
            
            # 필수 요소 확인
            checks = [
                ("/static/tailwind.min.js", "Tailwind CSS 로컬 경로"),
                ("하나금융융합기술원 AI 아바타", "페이지 타이틀"),
                ("텍스트 입력", "입력 폼"),
                ("비디오 생성하기", "제출 버튼"),
            ]
            
            all_ok = True
            for text, description in checks:
                if text in html:
                    print(f"✓ {description}")
                else:
                    print(f"✗ {description} 누락")
                    all_ok = False
            
            # CDN 링크 확인 (있으면 안됨)
            if "cdn.tailwindcss.com" in html:
                print(f"✗ 경고: CDN 링크가 여전히 남아있음 (폐쇄망에서 작동하지 않을 수 있음)")
                all_ok = False
            else:
                print(f"✓ 외부 CDN 의존성 없음")
            
            return all_ok
        else:
            print(f"✗ 페이지 로드 실패: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 페이지 로드 실패: {e}")
        return False

def test_local_files():
    """로컬 파일 존재 확인"""
    print()
    print("=" * 70)
    print("4. 로컬 파일 존재 확인")
    print("=" * 70)
    
    script_dir = Path(__file__).parent
    files_to_check = [
        script_dir / "static" / "tailwind.min.js",
        script_dir / "static" / "hana_logo.png",
        script_dir / "templates" / "index.html",
        script_dir / "app.py",
    ]
    
    all_ok = True
    
    for file_path in files_to_check:
        if file_path.exists():
            size = file_path.stat().st_size
            size_kb = size / 1024
            print(f"✓ {file_path.name}: {size_kb:.1f} KB")
        else:
            print(f"✗ {file_path.name}: 파일 없음")
            all_ok = False
    
    return all_ok

def main():
    """메인 테스트 실행"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "폐쇄망 UI 테스트" + " " * 32 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # 로컬 파일 확인
    file_ok = test_local_files()
    
    # 서버 테스트 (서버가 실행 중인 경우)
    server_ok = test_server_health()
    
    if server_ok:
        static_ok = test_static_files()
        page_ok = test_main_page()
    else:
        print()
        print("=" * 70)
        print("서버가 실행되지 않았습니다. 서버 테스트를 건너뜁니다.")
        print("서버를 시작하려면: python app.py 또는 ./start.sh")
        print("=" * 70)
        static_ok = False
        page_ok = False
    
    # 최종 결과
    print()
    print("=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)
    print(f"  로컬 파일: {'✓ 통과' if file_ok else '✗ 실패'}")
    print(f"  서버 헬스: {'✓ 통과' if server_ok else '✗ 실패 (서버 미실행)'}")
    
    if server_ok:
        print(f"  정적 파일: {'✓ 통과' if static_ok else '✗ 실패'}")
        print(f"  메인 페이지: {'✓ 통과' if page_ok else '✗ 실패'}")
    
    print("=" * 70)
    
    if file_ok and server_ok and static_ok and page_ok:
        print()
        print("🎉 모든 테스트 통과! 폐쇄망 환경에서 정상 작동합니다.")
        print()
        print("다음 단계:")
        print("  1. 브라우저에서 http://localhost:8000 접속")
        print("  2. UI가 정상적으로 표시되는지 육안 확인")
        print("  3. 텍스트 입력 후 '비디오 생성하기' 버튼 클릭 (TTS/비디오 서버 필요)")
        print()
        return 0
    else:
        print()
        print("⚠️  일부 테스트 실패. OFFLINE_SETUP.md를 참고하여 문제를 해결하세요.")
        print()
        
        if not file_ok:
            print("→ 로컬 파일 문제: download_tailwind.py를 실행하여 Tailwind CSS를 다운로드하세요")
        if server_ok and not static_ok:
            print("→ 정적 파일 로드 문제: static/ 폴더의 파일 권한을 확인하세요")
        if server_ok and not page_ok:
            print("→ 페이지 로드 문제: templates/index.html 파일을 확인하세요")
        
        print()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print("테스트 중단됨")
        sys.exit(1)

