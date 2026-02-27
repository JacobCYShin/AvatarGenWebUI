#!/bin/bash
# Tailwind CSS CDN 다운로드 스크립트

echo "Tailwind CSS 다운로드 중..."

cd "$(dirname "$0")/static"

# Tailwind CSS CDN 다운로드
curl -o tailwind.min.js https://cdn.tailwindcss.com

if [ -f "tailwind.min.js" ]; then
    echo "✓ Tailwind CSS 다운로드 완료: $(pwd)/tailwind.min.js"
    echo "파일 크기: $(du -h tailwind.min.js | cut -f1)"
else
    echo "✗ 다운로드 실패"
    exit 1
fi

