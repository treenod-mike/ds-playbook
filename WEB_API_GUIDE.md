# 🌐 웹 API 가이드 (3001 포트)

**서버 주소**: http://localhost:3001
**상태**: ✅ 실행 중
**버전**: v1.0.0 (GraphRAG API)

---

## 🚀 빠른 시작

### 1. 서버 실행 (이미 실행 중)

```bash
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

**현재 상태**:
- ✅ Supabase 연결됨
- ✅ OpenAI 연결됨 (LiteLLM)
- ✅ 262개 용어 로드
- ✅ 35개 관계 활성화

---

## 📡 API 엔드포인트

### 1. 기본 정보

#### GET /
서비스 상태 및 엔드포인트 목록

```bash
curl http://localhost:3001/
```

**응답**:
```json
{
  "service": "DS-Playbook GraphRAG API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/api/health",
    "terms": "/api/terms",
    "impact_analysis": "/api/impact-analysis",
    "subgraph": "/api/subgraph",
    "shortest_path": "/api/shortest-path",
    "chat": "/api/chat"
  }
}
```

---

#### GET /api/health
헬스 체크

```bash
curl http://localhost:3001/api/health
```

**응답**:
```json
{
  "status": "healthy",
  "supabase": "connected",
  "terms_available": true
}
```

---

### 2. 용어 조회

#### GET /api/terms
DB에 저장된 용어 목록 조회

**파라미터**:
- `limit` (optional): 최대 개수 (기본값: 10)
- `category` (optional): 카테고리 필터 (예: GameObject, Mechanic)

```bash
# 기본 10개 조회
curl http://localhost:3001/api/terms

# 카테고리 필터
curl "http://localhost:3001/api/terms?category=GameObject&limit=5"
```

**응답 예시**:
```json
{
  "terms": [
    {
      "term": "석판",
      "category": "GameObject",
      "definition": null
    },
    {
      "term": "한정 동물",
      "category": "GameObject",
      "definition": null
    }
  ],
  "count": 2
}
```

---

### 3. 서브그래프 추출

#### POST /api/subgraph
특정 용어를 중심으로 관계 그래프 추출

**요청 본문**:
```json
{
  "center_node": "모험 81 챕터 보상",
  "radius": 2,
  "min_confidence": 0.5
}
```

**cURL 예시**:
```bash
curl -X POST http://localhost:3001/api/subgraph \
  -H "Content-Type: application/json" \
  -d '{
    "center_node": "모험 81 챕터 보상",
    "radius": 2,
    "min_confidence": 0.5
  }'
```

**응답**:
```json
{
  "nodes": [
    {
      "id": "uuid-1",
      "label": "모험 81 챕터 보상",
      "category": "Content"
    },
    {
      "id": "uuid-2",
      "label": "포코코로",
      "category": "GameObject"
    }
  ],
  "edges": [
    {
      "from": "uuid-1",
      "to": "uuid-2",
      "label": "rewards",
      "confidence": 0.96
    }
  ],
  "center": "모험 81 챕터 보상"
}
```

---

### 4. 챗봇 API (GPT-4o 기반)

#### POST /api/chat
지식 그래프 기반 대화형 질문 응답

**요청 본문**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "모험 81 챕터 보상이 뭐야?"
    }
  ],
  "use_graph": true
}
```

**cURL 예시**:
```bash
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "모험 81 챕터 보상이 뭐야?"}
    ],
    "use_graph": true
  }'
```

**응답**:
```json
{
  "message": "모험 81 챕터를 클리어하면 '포코코로'라는 보상을 받을 수 있어요. 이 보상은 챕터 클리어 보상 시스템의 일부로, 플레이어의 진행 동기를 부여하는 역할을 합니다...",
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  },
  "search_process": {
    "steps": [
      {
        "step": 1,
        "name": "데이터베이스 조회",
        "description": "Supabase에서 모든 용어와 온톨로지 룰 로드 중..."
      },
      {
        "step": 2,
        "name": "데이터 로드 완료",
        "description": "용어 262개, 온톨로지 룰 90개 로드"
      },
      {
        "step": 3,
        "name": "용어 매칭",
        "description": "질문에서 관련 용어 추출 중..."
      },
      {
        "step": 4,
        "name": "용어 매칭 완료",
        "description": "1개의 고유 용어 발견: 모험 81 챕터 보상"
      },
      {
        "step": 5,
        "name": "관계 그래프 탐색",
        "description": "'모험 81 챕터 보상' 중심으로 반경 2 단계 그래프 추출 중..."
      },
      {
        "step": 6,
        "name": "그래프 추출 완료",
        "description": "노드 2개, 관계 1개 발견"
      },
      {
        "step": 7,
        "name": "컨텍스트 생성",
        "description": "온톨로지 룰과 관계 데이터를 기반으로 AI 응답 생성 중..."
      }
    ],
    "found_terms": [
      {
        "term": "모험 81 챕터 보상",
        "category": "Content"
      }
    ],
    "center_term": "모험 81 챕터 보상",
    "nodes_count": 2,
    "edges_count": 1
  }
}
```

---

### 5. 최단 경로 탐색

#### GET /api/shortest-path
두 용어 간 최단 경로 찾기

**파라미터**:
- `start`: 시작 용어
- `end`: 도착 용어
- `max_depth` (optional): 최대 탐색 깊이 (기본값: 5)
- `min_confidence` (optional): 최소 신뢰도 (기본값: 0.5)

```bash
curl "http://localhost:3001/api/shortest-path?start=상점&end=메달&max_depth=3"
```

**응답 (경로 발견 시)**:
```json
{
  "found": true,
  "path": {
    "nodes": ["상점", "메달"],
    "edges": ["consumes"],
    "depth": 1,
    "confidence": 0.96
  }
}
```

**응답 (경로 없음)**:
```json
{
  "found": false,
  "message": "No path found between '석판' and '메달' within 3 hops"
}
```

---

### 6. 영향 분석 (Impact Analysis)

#### POST /api/impact-analysis
특정 용어가 미치는 영향 범위 분석 (DFS)

**요청 본문**:
```json
{
  "source_node": "메달",
  "max_depth": 3,
  "min_confidence": 0.5
}
```

**cURL 예시**:
```bash
curl -X POST http://localhost:3001/api/impact-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "source_node": "메달",
    "max_depth": 3,
    "min_confidence": 0.5
  }'
```

**응답**:
```json
{
  "source": "메달",
  "max_depth": 3,
  "impact_map": {
    "0": ["메달"],
    "1": ["상점", "구매"],
    "2": ["아이템", "보상"]
  },
  "total_nodes": 5
}
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 보상 체인 탐색

```bash
# 1. 용어 검색
curl "http://localhost:3001/api/terms?limit=5"

# 2. 서브그래프 추출
curl -X POST http://localhost:3001/api/subgraph \
  -H "Content-Type: application/json" \
  -d '{"center_node": "모험 81 챕터 보상", "radius": 2}'

# 3. 챗봇 질문
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "모험 81 챕터 보상이 뭐야?"}], "use_graph": true}'
```

---

### 시나리오 2: 관계 탐색

```bash
# 1. 최단 경로 찾기
curl "http://localhost:3001/api/shortest-path?start=상점&end=메달"

# 2. 영향 분석
curl -X POST http://localhost:3001/api/impact-analysis \
  -H "Content-Type: application/json" \
  -d '{"source_node": "메달", "max_depth": 2}'
```

---

## 🎯 추천 테스트 질문 (챗봇)

### 관계가 있는 질문 (추천)

```bash
# 1. 모험 81 챕터 보상
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "모험 81 챕터 보상이 뭐야?"}], "use_graph": true}'

# 2. 뱀파이어 제프
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "뱀파이어 제프는 뭐야?"}], "use_graph": true}'

# 3. 메달 사용처
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "메달은 어디에 쓰나요?"}], "use_graph": true}'

# 4. 상점 기능
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "상점에서 뭘 살 수 있어?"}], "use_graph": true}'
```

---

## 🔧 서버 관리

### 서버 시작

```bash
# 3001 포트 (현재)
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

# 8000 포트 (기본)
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 서버 중지

```bash
# 프로세스 찾기
lsof -i :3001

# 프로세스 종료 (PID 확인 후)
kill <PID>

# 또는 터미널에서 Ctrl+C
```

### 로그 확인

서버 로그는 실시간으로 터미널에 출력됩니다:
```
INFO:src.api.main:Initializing Supabase connection...
INFO:src.api.main:✅ Supabase connection established
INFO:src.api.main:✅ OpenAI initialized (base_url: https://litellm.treenod.com)
INFO:     Application startup complete.
```

---

## 🌐 웹 인터페이스 (선택)

FastAPI는 자동으로 Swagger UI를 제공합니다:

**Swagger UI**: http://localhost:3001/docs
**ReDoc**: http://localhost:3001/redoc

브라우저에서 위 주소로 접속하면 대화형 API 문서를 볼 수 있습니다.

---

## 📊 현재 시스템 상태

- **서버**: ✅ http://localhost:3001
- **데이터베이스**: ✅ Supabase 연결
- **LLM**: ✅ GPT-4o via LiteLLM
- **용어**: 262개
- **관계**: 35개 (100% evidence)
- **온톨로지 룰**: 90개

---

## 🔍 트러블슈팅

### 1. "Address already in use" 오류

```bash
# 포트 확인
lsof -i :3001

# 프로세스 종료
kill <PID>

# 또는 다른 포트 사용
python3 -m uvicorn src.api.main:app --port 3002
```

### 2. "OPENAI_API_KEY not found" 경고

챗봇 엔드포인트(`/api/chat`)는 사용할 수 없습니다. `.env` 파일에 API 키를 설정하세요:
```bash
OPENAI_API_KEY=your-key-here
OPENAI_BASE_URL=https://litellm.treenod.com
```

### 3. "Term not found" 오류

요청한 용어가 DB에 없습니다. 사용 가능한 용어 확인:
```bash
curl "http://localhost:3001/api/terms?limit=100"
```

---

## 📚 관련 문서

- [TEST_QUERIES.md](docs/TEST_QUERIES.md) - 테스트 질문 가이드
- [V3_INTEGRATION_STATUS.md](docs/V3_INTEGRATION_STATUS.md) - 시스템 상태
- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - 프로젝트 구조

---

**서버 주소**: http://localhost:3001
**Swagger UI**: http://localhost:3001/docs
**상태**: ✅ 실행 중

질문이 있으시면 언제든지 문의하세요!

---

## 🔧 최근 수정 사항 (2026-01-30)

### DB 스키마 호환성 수정 완료 ✅

**문제**: `subgraph_extractor.py`가 존재하지 않는 `relation_type`, `weight` 필드를 조회하려고 시도

**해결**:
1. `_get_outgoing_relations()` - relation_type, weight SELECT 제거
2. `_get_incoming_relations()` - relation_type, weight SELECT 제거  
3. `extract_by_predicate()` - relation_type, weight SELECT 제거
4. 모든 엣지 데이터 구조에서 relation_type, weight 필드 제거
5. 정렬 기준을 `weight` → `confidence`로 변경

**결과**: 
- ✅ 웹 API 정상 작동
- ✅ 챗봇 API 테스트 성공 ("포코코로는 뭐야?" → 정상 답변)
- ✅ 그래프 데이터 조회 성공 (2개 노드, 2개 관계)

### 테스트 결과

```bash
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "포코코로는 뭐야?"}], "use_graph": true}'
```

**응답 예시**:
```
포코코로는 PokoPoko 게임 내에서 사용되는 "리소스(Resource)"입니다...
지식 그래프에 따르면, "모험 81 챕터 보상"이라는 콘텐츠를 클리어하면 
포코코로를 보상으로 받을 수 있습니다...

그래프 데이터:
✅ 노드: 2개
✅ 관계: 2개 (rewards: 신뢰도 0.96)
```

---
