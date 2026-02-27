#!/usr/bin/env python3
"""
Tailwind CSS CDN 다운로드 스크립트
폐쇄망 배포 전 인터넷 연결된 환경에서 실행하세요.
"""
import os
import urllib.request
from pathlib import Path
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def download_tailwind():
    """Tailwind CSS 다운로드"""
    script_dir = Path(__file__).parent
    static_dir = script_dir / "static"
    output_file = static_dir / "tailwind.min.js"
    
    print("=" * 70)
    print("Tailwind CSS 다운로드 중...")
    print("=" * 70)
    
    # static 폴더 확인
    if not static_dir.exists():
        print(f"✗ static 폴더가 없습니다: {static_dir}")
        return False
    
    try:
        # Tailwind CSS CDN에서 다운로드
        url = "https://cdn.tailwindcss.com"
        print(f"URL: {url}")
        print(f"저장 위치: {output_file}")
        print()
        print("다운로드 중... (약 100-200KB)")
        
        urllib.request.urlretrieve(url, output_file)
        
        # 파일 크기 확인
        file_size = output_file.stat().st_size
        file_size_kb = file_size / 1024
        
        print()
        print("=" * 70)
        print(f"✓ 다운로드 완료!")
        print(f"  파일: {output_file}")
        print(f"  크기: {file_size_kb:.1f} KB")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"✗ 다운로드 실패: {e}")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = download_tailwind()
    exit(0 if success else 1)

