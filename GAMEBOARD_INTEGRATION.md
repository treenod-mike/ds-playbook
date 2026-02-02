# GAMEBOARD GraphRAG 연동 가이드

## 📋 목차
1. [연동 방식 선택](#연동-방식-선택)
2. [Option 1: MCP Server](#option-1-mcp-server)
3. [Option 2: REST API](#option-2-rest-api)
4. [Option 3: Python SDK](#option-3-python-sdk)

---

## 🎯 연동 방식 선택

| 방식 | 사용 케이스 | 장점 | 단점 |
|------|------------|------|------|
| **MCP Server** | Claude 기반 LLM | 최신 프로토콜, 동적 체인 | Claude 전용 |
| **REST API** | 모든 LLM/플랫폼 | 범용성, 언어 무관 | HTTP 오버헤드 |
| **Python SDK** | Python 프로젝트 | 직접 통합, 빠름 | Python 전용 |

---

## Option 1: MCP Server

### 1.1 구조
```
GAMEBOARD (LLM)
    ↓ MCP Protocol
playbook-nexus MCP Server
    ↓
GraphRAG Engine (Supabase + FastAPI)
```

### 1.2 제공 Tools

**Tool 1: search_playbook_knowledge**
```json
{
  "name": "search_playbook_knowledge",
  "description": "포코포코 게임 지식 검색 (용어, 관계, 시스템 정보)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "검색 질문 (예: 'BM이 뭐야?', '턴릴레이 보상')"
      },
      "use_graph": {
        "type": "boolean",
        "description": "그래프 탐색 사용 여부",
        "default": true
      },
      "depth": {
        "type": "integer",
        "description": "그래프 탐색 깊이 (1-5)",
        "default": 2
      }
    },
    "required": ["query"]
  }
}
```

**Tool 2: explore_term_relations**
```json
{
  "name": "explore_term_relations",
  "description": "특정 용어의 관계 네트워크 탐색",
  "inputSchema": {
    "type": "object",
    "properties": {
      "term": {
        "type": "string",
        "description": "탐색할 용어명 (예: 'BM', '턴릴레이')"
      },
      "radius": {
        "type": "integer",
        "description": "탐색 반경 (hop 수)",
        "default": 2
      },
      "relation_types": {
        "type": "array",
        "items": {"type": "string"},
        "description": "필터링할 관계 타입 (예: ['rewards', 'requires'])"
      }
    },
    "required": ["term"]
  }
}
```

**Tool 3: find_relation_path**
```json
{
  "name": "find_relation_path",
  "description": "두 용어 간의 연결 경로 찾기",
  "inputSchema": {
    "type": "object",
    "properties": {
      "from_term": {"type": "string"},
      "to_term": {"type": "string"},
      "max_depth": {"type": "integer", "default": 5}
    },
    "required": ["from_term", "to_term"]
  }
}
```

### 1.3 설치 방법

**1. MCP 서버 실행:**
```bash
cd /Users/mike/Desktop/playbook_nexus
python src/mcp/server.py
```

**2. GAMEBOARD에서 MCP 설정:**
```json
{
  "mcpServers": {
    "playbook-graphrag": {
      "command": "python",
      "args": ["/Users/mike/Desktop/playbook_nexus/src/mcp/server.py"],
      "env": {
        "SUPABASE_URL": "https://kxvgjkebuzpmflmhnbno.supabase.co",
        "SUPABASE_KEY": "<your-key>"
      }
    }
  }
}
```

**3. GAMEBOARD에서 사용:**
```python
# GAMEBOARD LLM에서 자동으로 Tool 호출
response = llm.chat([
    {"role": "user", "content": "BM 만드는 방법 알려줘"}
])
# → MCP Tool 'search_playbook_knowledge' 자동 호출
# → GraphRAG 검색 결과 반환
# → LLM이 해석해서 답변
```

---

## Option 2: REST API

### 2.1 구조
```
GAMEBOARD (HTTP Client)
    ↓ HTTP/REST
playbook-nexus FastAPI Server (Port 8000)
    ↓
GraphRAG Engine
```

### 2.2 제공 Endpoints

**Endpoint 1: Search**
```http
POST http://localhost:8000/api/search
Content-Type: application/json

{
  "query": "BM 만드는 방법",
  "use_graph": true,
  "depth": 2
}

Response:
{
  "message": "BM은 4매치로 만들 수 있습니다...",
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  },
  "search_process": {
    "found_terms": ["BM", "4매치"],
    "reasoning_chain": [...]
  }
}
```

**Endpoint 2: Explore Relations**
```http
GET http://localhost:8000/api/terms/{term}/relations?radius=2

Response:
{
  "term": "BM",
  "category": "resource",
  "relations": [
    {
      "predicate": "requires",
      "target": "4매치",
      "confidence": 0.95
    }
  ]
}
```

**Endpoint 3: Find Path**
```http
POST http://localhost:8000/api/paths
Content-Type: application/json

{
  "from_term": "BM",
  "to_term": "클로버",
  "max_depth": 5
}

Response:
{
  "paths": [
    {
      "nodes": ["BM", "4매치", "스테이지", "클로버"],
      "edges": ["requires", "triggers", "consumes"],
      "confidence": 0.85
    }
  ]
}
```

### 2.3 설치 방법

**1. FastAPI 서버 실행:**
```bash
cd /Users/mike/Desktop/playbook_nexus
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**2. GAMEBOARD에서 HTTP 호출:**
```python
# GAMEBOARD 코드
import requests

def search_playbook(query: str):
    response = requests.post(
        "http://localhost:8000/api/search",
        json={"query": query, "use_graph": True}
    )
    return response.json()

# 사용 예시
result = search_playbook("BM 만드는 방법")
print(result["message"])
print(result["graph_data"])
```

**3. GAMEBOARD LLM에 통합:**
```python
# GAMEBOARD LLM 프롬프트에 추가
system_prompt = """
당신은 포코포코 게임 전문가입니다.
질문에 답변할 때 playbook_graphrag API를 사용하세요.

사용 가능한 API:
- POST /api/search: 지식 검색
- GET /api/terms/{term}/relations: 관계 탐색
- POST /api/paths: 경로 찾기
"""

def llm_with_graphrag(user_query):
    # 1. LLM이 API 호출 필요 판단
    if needs_knowledge_search(user_query):
        graphrag_result = search_playbook(user_query)
        context = graphrag_result["message"]

    # 2. LLM이 컨텍스트와 함께 답변 생성
    return llm.generate(user_query, context=context)
```

---

## Option 3: Python SDK

### 3.1 구조
```
GAMEBOARD (Python)
    ↓ Direct Import
playbook-nexus Python Module
    ↓
GraphRAG Engine
```

### 3.2 제공 Classes

**Class 1: PlaybookGraphRAG**
```python
from playbook_nexus import PlaybookGraphRAG

# 초기화
graphrag = PlaybookGraphRAG(
    supabase_url="...",
    supabase_key="...",
    openai_api_key="..."
)

# 검색
result = graphrag.search("BM 만드는 방법")
print(result.message)
print(result.graph_data)

# 관계 탐색
relations = graphrag.explore_relations("BM", radius=2)

# 경로 찾기
paths = graphrag.find_path("BM", "클로버", max_depth=5)
```

### 3.3 설치 방법

**1. playbook_nexus 모듈 설치:**
```bash
cd /Users/mike/Desktop/playbook_nexus
pip install -e .
```

**2. GAMEBOARD에서 import:**
```python
# GAMEBOARD 코드
from playbook_nexus import PlaybookGraphRAG
from playbook_nexus.config import Config

# 초기화
graphrag = PlaybookGraphRAG.from_env()  # .env에서 자동 로드

# 사용
def answer_with_graphrag(user_query):
    # GraphRAG 검색
    result = graphrag.search(user_query, use_graph=True)

    # LLM에 컨텍스트 제공
    llm_response = llm.generate(
        query=user_query,
        context=result.message,
        graph_data=result.graph_data
    )

    return llm_response
```

---

## 🎯 추천 방식

### **GAMEBOARD가 Claude 기반 → Option 1 (MCP)**
- ✅ 가장 강력한 통합
- ✅ 동적 체인 구성
- ✅ 최소 코드 변경

### **GAMEBOARD가 범용 LLM → Option 2 (REST API)**
- ✅ 언어/플랫폼 무관
- ✅ 마이크로서비스 아키텍처
- ✅ 독립 배포 가능

### **GAMEBOARD가 Python 프로젝트 → Option 3 (SDK)**
- ✅ 가장 빠른 성능
- ✅ 타입 안전성
- ✅ 직접 제어 가능

---

## 📦 다음 단계

**제가 구현해드릴 파일들:**

### Option 1 선택 시:
- `src/mcp/server.py` - MCP 서버 메인
- `src/mcp/tools.py` - Tool 정의
- `src/mcp/handlers.py` - Tool 핸들러
- `mcp_config.json` - 설정 파일

### Option 2 선택 시:
- `src/api/routes/graphrag.py` - REST API 엔드포인트
- `src/api/schemas/graphrag.py` - Request/Response 스키마
- `docs/api_integration.md` - API 문서

### Option 3 선택 시:
- `src/sdk/__init__.py` - SDK 엔트리포인트
- `src/sdk/client.py` - PlaybookGraphRAG 클래스
- `setup.py` - 패키지 설정
- `docs/sdk_guide.md` - SDK 가이드

---

## 🔧 현재 준비 상태

- ✅ GraphRAG 엔진 (완성)
- ✅ FastAPI 백엔드 (완성)
- ✅ Supabase 데이터 (5,665 용어, 4,676 관계)
- ⏳ MCP Server (구현 필요)
- ⏳ REST API 확장 (일부 구현됨)
- ⏳ Python SDK (구현 필요)

**어떤 방식으로 진행하시겠습니까?**
