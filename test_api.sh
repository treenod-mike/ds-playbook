#!/bin/bash
# FastAPI 엔드포인트 테스트 스크립트

API_URL="${1:-http://localhost:8000}"

echo "=========================================="
echo "FastAPI 엔드포인트 테스트"
echo "API URL: $API_URL"
echo "=========================================="

# 1. API 정보
echo -e "\n[1] GET / - API 정보"
curl -s "$API_URL/" | jq '.'

# 2. 헬스 체크
echo -e "\n[2] GET /api/health - 헬스 체크"
curl -s "$API_URL/api/health" | jq '.'

# 3. Terms 조회
echo -e "\n[3] GET /api/terms?limit=5 - 시맨틱 용어 조회"
curl -s "$API_URL/api/terms?limit=5" | jq '.'

# 4. 실제 데이터로 Impact Analysis 테스트
echo -e "\n[4] POST /api/impact-analysis - 영향 분석"
curl -s -X POST "$API_URL/api/impact-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "source_node": "스테이지",
    "max_depth": 3,
    "min_confidence": 0.5
  }' | jq '.'

# 5. Subgraph 추출 테스트
echo -e "\n[5] POST /api/subgraph - 서브그래프 추출"
curl -s -X POST "$API_URL/api/subgraph" \
  -H "Content-Type: application/json" \
  -d '{
    "center_node": "스테이지",
    "radius": 2,
    "min_confidence": 0.5
  }' | jq '.'

# 6. Shortest Path 테스트
echo -e "\n[6] GET /api/shortest-path - 최단 경로"
curl -s "$API_URL/api/shortest-path?start=스테이지&end=체리&max_depth=5" | jq '.'

echo -e "\n=========================================="
echo "테스트 완료!"
echo "=========================================="
