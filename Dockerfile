FROM python:3.10-slim

WORKDIR /app

# 필요한 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 디렉토리 생성
RUN mkdir -p outputs temp static templates

# 포트 노출
EXPOSE 8000

# 서버 실행
CMD ["python", "app.py"]

