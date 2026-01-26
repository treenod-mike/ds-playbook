# FastAPI 테스트 가이드

## 🚀 빠른 시작

### 1. API 서버 실행
```bash
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**결과:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. 브라우저 테스트

**API 문서 (Swagger UI):**
```
http://localhost:8000/docs
```
→ 모든 엔드포인트를 브라우저에서 바로 테스트 가능!

**API 정보:**
```
http://localhost:8000
```

**헬스 체크:**
```
http://localhost:8000/api/health
```

---

## 📋 엔드포인트 테스트

### 1. 헬스 체크
```bash
curl http://localhost:8000/api/health
```

**응답:**
```json
{
  "status": "healthy",
  "supabase": "connected",
  "terms_available": true
}
```

---

### 2. 시맨틱 용어 조회
```bash
curl "http://localhost:8000/api/terms?limit=5"
```

**응답:**
```json
{
  "terms": [
    {
      "term": "스테이지",
      "category": "Content",
      "definition": "게임 레벨"
    },
    ...
  ],
  "count": 5
}
```

**카테고리 필터:**
```bash
curl "http://localhost:8000/api/terms?category=Content&limit=10"
```

---

### 3. 영향 분석 (Impact Analysis)
```bash
curl -X POST http://localhost:8000/api/impact-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "source_node": "스테이지",
    "max_depth": 3,
    "min_confidence": 0.5
  }'
```

**응답:**
```json
{
  "source": "스테이지",
  "max_depth": 3,
  "impact_map": {
    "0": ["스테이지"],
    "1": ["그룹 배틀 이벤트"],
    "2": ["승리 포인트"]
  },
  "total_nodes": 3
}
```

---

### 4. 서브그래프 추출
```bash
curl -X POST http://localhost:8000/api/subgraph \
  -H "Content-Type: application/json" \
  -d '{
    "center_node": "스테이지",
    "radius": 2,
    "min_confidence": 0.5
  }'
```

**응답:**
```json
{
  "nodes": [
    {
      "id": "uuid-1",
      "term": "스테이지",
      "category": "Content"
    },
    ...
  ],
  "edges": [
    {
      "source": "uuid-1",
      "target": "uuid-2",
      "predicate": "contains"
    },
    ...
  ],
  "center": "스테이지"
}
```

---

### 5. 최단 경로 탐색
```bash
# URL 인코딩 주의!
curl "http://localhost:8000/api/shortest-path?start=bomb&end=cherry&max_depth=5"
```

**한글 용어 사용 시:**
```bash
# Python urllib로 인코딩
python3 -c "import urllib.parse; print(urllib.parse.quote('스테이지'))"
# 출력: %EC%8A%A4%ED%85%8C%EC%9D%B4%EC%A7%80

curl "http://localhost:8000/api/shortest-path?start=%EC%8A%A4%ED%85%8C%EC%9D%B4%EC%A7%80&end=%EC%B2%B4%EB%A6%AC"
```

**응답:**
```json
{
  "found": true,
  "path": {
    "nodes": ["스테이지", "보상", "체리"],
    "edges": ["rewards", "contains"],
    "depth": 2,
    "confidence": 0.95
  }
}
```

---

## 🧪 자동 테스트 스크립트

### 전체 엔드포인트 테스트
```bash
./test_api.sh
```

또는:
```bash
./test_api.sh http://localhost:8000
```

---

## 🌐 외부 접근 테스트 (ngrok)

### 1. ngrok 설치 확인
```bash
ngrok version
```

### 2. 터널링 시작
```bash
# 터미널 1: API 서버
python3 -m uvicorn src.api.main:app --port 8000

# 터미널 2: ngrok
ngrok http 8000
```

**출력:**
```
Forwarding: https://abc-123.ngrok-free.app -> http://localhost:8000
```

### 3. 외부에서 테스트
```bash
# 외부 URL로 테스트
curl https://abc-123.ngrok-free.app/api/health

# 스마트폰에서도 접근 가능!
https://abc-123.ngrok-free.app/docs
```

---

## 🐳 Docker 테스트

### 1. 이미지 빌드
```bash
docker build -t playbook-api .
```

### 2. 실행
```bash
docker run -p 8000:8000 \
  -e SUPABASE_URL="$SUPABASE_URL" \
  -e SUPABASE_KEY="$SUPABASE_KEY" \
  playbook-api
```

### 3. 테스트
```bash
curl http://localhost:8000/api/health
```

---

## 📊 성능 테스트

### Apache Bench
```bash
# 100 요청, 동시 10개
ab -n 100 -c 10 http://localhost:8000/api/health
```

### wrk
```bash
# 10초 동안 2 스레드로 부하 테스트
wrk -t2 -c10 -d10s http://localhost:8000/api/health
```

---

## 🔍 문제 해결

### 1. 포트 이미 사용 중
```bash
# 8000 포트 사용 중인 프로세스 확인
lsof -ti:8000

# 종료
kill -9 $(lsof -ti:8000)
```

### 2. Supabase 연결 실패
```bash
# 환경변수 확인
echo $SUPABASE_URL
echo $SUPABASE_KEY

# .env 파일 확인
cat .env | grep SUPABASE
```

### 3. 한글 인코딩 문제
```bash
# Python으로 URL 인코딩
python3 << EOF
import urllib.parse
term = "스테이지"
print(urllib.parse.quote(term))
EOF
```

---

## 📝 테스트 체크리스트

- [ ] API 서버 시작 확인
- [ ] `/api/health` 헬스 체크 통과
- [ ] `/api/terms` 용어 조회 정상
- [ ] `/api/impact-analysis` 영향 분석 동작
- [ ] `/api/subgraph` 서브그래프 추출 동작
- [ ] `/api/shortest-path` 최단 경로 탐색 동작
- [ ] Swagger UI (`/docs`) 접근 가능
- [ ] ngrok 터널링 테스트 (선택)
- [ ] Docker 빌드 및 실행 (선택)

---

## 🎯 다음 단계

### 배포 옵션

1. **Railway**: `railway up`
2. **Render**: GitHub 연결 후 자동 배포
3. **Docker**: 자체 서버에 배포

자세한 내용: [README.md - FastAPI 서버 배포](README.md#-fastapi-서버-배포)
