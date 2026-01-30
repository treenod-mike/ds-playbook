# Playbook Nexus - 프로젝트 구조 및 시스템 흐름

**작성일**: 2026-01-30
**버전**: v2.0
**목적**: 프로젝트 전체 구조 파악 및 시스템 흐름 이해

---

## 📁 프로젝트 디렉토리 구조

```
playbook_nexus/
├── 📂 src/                          # 소스 코드
│   ├── 📂 core/                     # 핵심 비즈니스 로직
│   │   ├── 📂 loaders/              # 데이터 로더 (Confluence, Notion 등)
│   │   │   ├── confluence_loader.py
│   │   │   └── notion_loader.py
│   │   │
│   │   ├── 📂 processors/           # 데이터 처리 파이프라인
│   │   │   ├── semantic_processor.py    # Phase 1: 용어 추출 + raw_relations
│   │   │   ├── embedding_processor.py   # 임베딩 생성
│   │   │   └── ontology_builder.py      # Phase 2: 관계 검증
│   │   │
│   │   ├── 📂 generators/           # 답변 생성
│   │   │   └── rag_answer_generator.py  # Evidence-based 답변 생성
│   │   │
│   │   ├── 📂 rules/                # 온톨로지 룰 관리
│   │   │   ├── ontology_schema.py       # 스키마 정의
│   │   │   ├── rule_matcher.py          # 룰 매칭 로직
│   │   │   └── validators.py            # 검증 로직
│   │   │
│   │   └── 📂 traversal/            # 그래프 탐색
│   │       ├── graph_engine.py          # BFS/DFS 탐색
│   │       ├── subgraph_extractor.py    # 서브그래프 추출
│   │       └── path_finder.py           # 경로 찾기
│   │
│   ├── 📂 api/                      # FastAPI 웹 서버
│   │   ├── main.py                      # API 엔드포인트
│   │   └── routers/
│   │       ├── chat.py                  # 챗봇 API
│   │       └── graph.py                 # 그래프 API
│   │
│   ├── 📂 shared/                   # 공통 유틸리티
│   │   ├── config.py                    # 설정 관리
│   │   ├── logger.py                    # 로깅 설정
│   │   └── supabase_client.py           # Supabase 클라이언트
│   │
│   └── main.py                      # CLI 진입점
│
├── 📂 scripts/                      # 실행 스크립트
│   ├── 🔧 Phase 1 관련
│   │   ├── test_chatbot_v2.py           # 대화형 챗봇 테스트 (v2.0)
│   │   └── test_rag_answer_generation.py # RAG 답변 생성 테스트
│   │
│   ├── 🔧 Phase 2 관련
│   │   ├── add_ux_advanced_ontology_rules.py  # v2.0 온톨로지 룰 추가
│   │   ├── add_liveops_ontology_rules.py      # LiveOps 룰 추가
│   │   └── add_missing_ontology_rules.py      # 누락 룰 보완
│   │
│   ├── 🔧 진단 및 검증
│   │   ├── diagnose_relations.py        # 관계 통계 분석
│   │   ├── check_term_relations.py      # 특정 용어 관계 확인
│   │   └── demo_traversal.py            # 그래프 탐색 데모
│   │
│   └── 🔧 데이터 관리
│       └── clear_phase1_data.py         # Phase 1 데이터 초기화
│
├── 📂 prompts/                      # LLM 프롬프트
│   ├── system_pokopoko.md               # Phase 1 용어 추출 프롬프트
│   └── system_relation_builder.md       # Phase 2 관계 추출 프롬프트
│
├── 📂 supabase/                     # Supabase 마이그레이션
│   └── migrations/
│       ├── 20250130_v2_ux_advanced_ontology.sql  # v2.0 스키마
│       └── clear_phase1_data.sql                  # 데이터 초기화
│
├── 📂 docs/                         # 문서
│   ├── PROJECT_STRUCTURE.md             # 프로젝트 구조 (이 파일)
│   ├── ONTOLOGY_UPDATE_SUMMARY.md       # v2.0 온톨로지 업그레이드 요약
│   ├── RAG_ANSWER_GENERATION.md         # RAG 답변 생성 가이드
│   ├── RAW_RELATIONS_OPTIMIZATION.md    # raw_relations 최적화
│   ├── TRAVERSAL_DESIGN.md              # 그래프 탐색 설계
│   ├── PROJECT_CONTEXT.md               # 프로젝트 컨텍스트
│   └── GIT_SETUP.md                     # Git 설정
│
├── 📂 playbook-web/                 # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/                         # App Router
│   │   ├── components/                  # React 컴포넌트
│   │   └── lib/                         # 유틸리티
│   └── package.json
│
├── 📄 run_phase1_test.sh            # Phase 1 테스트 실행 (100개)
├── 📄 run_phase1_full.sh            # Phase 1 전체 실행
├── 📄 run_full_pipeline.py          # 전체 파이프라인 실행
├── 📄 requirements.txt              # Python 의존성
├── 📄 .env                          # 환경 변수
└── 📄 README.md                     # 프로젝트 소개
```

---

## 🔄 시스템 흐름도 (GraphRAG Pipeline)

### 전체 파이프라인

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. Data Ingestion                             │
│                  (문서 수집 및 전처리)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Confluence/Notion API                                           │
│  ├─ confluence_loader.py                                         │
│  └─ notion_loader.py                                             │
│                                                                   │
│  Output: playbook_documents (2,246개)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. Document Chunking                          │
│                     (문서 청킹)                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Semantic Chunking (Token-based)                                 │
│  ├─ 청크 크기: 500 tokens                                        │
│  ├─ 오버랩: 50 tokens                                            │
│  └─ embedding_processor.py                                       │
│                                                                   │
│  Output: playbook_chunks (15,056개)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. Phase 1: Term Extraction                   │
│                  (용어 추출 + raw_relations)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  semantic_processor.py                                           │
│  ├─ Prompt: system_pokopoko.md (11개 카테고리)                  │
│  ├─ LLM: GPT-4o                                                  │
│  └─ Filtering: confidence ≥ 0.7, max 10 relations/term          │
│                                                                   │
│  Output:                                                          │
│  ├─ playbook_semantic_terms (8,000~10,000개 예상)               │
│  └─ raw_relations (JSONB, 평균 3-6개/용어)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. Phase 2: Relation Validation               │
│                     (관계 검증 및 확정)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  ontology_builder.py                                             │
│  ├─ Ontology Rules: 116개 (v2.0)                                │
│  ├─ Rule Matching: subject_type, predicate, object_type         │
│  ├─ Embedding Similarity: ≥ 0.7                                 │
│  └─ Term Existence Check                                         │
│                                                                   │
│  Output:                                                          │
│  └─ playbook_semantic_relations (3,000~6,000개 예상)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. Knowledge Graph Ready                      │
│                      (지식 그래프 완성)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. Query Processing                           │
│                     (사용자 질의 처리)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────────┐              ┌──────────────────┐
│  Vector Search   │              │ Graph Traversal  │
│  (Hybrid Search) │              │  (BFS 2-hop)     │
└────────┬─────────┘              └────────┬─────────┘
         │                                  │
         │  Top-K Chunks                    │  Relations
         │  (similarity ≥ 0.7)              │  (confidence ≥ 0.5)
         │                                  │
         └────────────────┬─────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7. Context Formatting                         │
│                   (컨텍스트 구조화)                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  RAGContextFormatter                                             │
│  ├─ Vector Search → XML <VectorSearchResults>                   │
│  ├─ Graph Relations → XML <GraphRelations>                      │
│  └─ Ontology Rules → XML <OntologyRules>                        │
│                                                                   │
│  Output: Structured Context (XML)                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    8. Answer Generation                          │
│                   (근거 기반 답변 생성)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  RAGAnswerGenerator                                              │
│  ├─ System Prompt: BI Analyst Role                              │
│  ├─ Constraints: Evidence-based Only                            │
│  ├─ Citation: [Source: ...], [Graph: ...]                       │
│  └─ Model: GPT-4o (temperature=0.3)                             │
│                                                                   │
│  Output: Markdown Answer with Citations                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    9. User Interface                             │
│                  (사용자 인터페이스)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            │                          │
            ▼                          ▼
    ┌──────────────┐          ┌──────────────┐
    │   Web Chat   │          │  CLI Chatbot │
    │ (Next.js)    │          │ (Python)     │
    │ Port: 3000   │          │ v2.0         │
    └──────────────┘          └──────────────┘
```

---

## 🎯 핵심 컴포넌트 상세

### 1. Data Loaders (데이터 로더)

| 파일 | 역할 | 입력 | 출력 |
|-----|------|------|------|
| [confluence_loader.py](../src/core/loaders/confluence_loader.py) | Confluence 페이지 수집 | Space Key, Page IDs | Raw Documents |
| [notion_loader.py](../src/core/loaders/notion_loader.py) | Notion 페이지 수집 | Database ID | Raw Documents |

**출력 테이블**: `playbook_documents`
```sql
CREATE TABLE playbook_documents (
    doc_id SERIAL PRIMARY KEY,
    title TEXT,
    source TEXT,
    url TEXT,
    content TEXT,
    created_at TIMESTAMP
);
```

### 2. Processors (데이터 처리)

#### 2.1. semantic_processor.py (Phase 1)

**역할**: 청크에서 용어 추출 + raw_relations 생성

**핵심 기능**:
- LLM 호출로 용어 + 관계 추출
- Confidence 기반 필터링 (≥ 0.7)
- Top-K 제한 (최대 10개/용어)

**입력**: `playbook_chunks`
**출력**: `playbook_semantic_terms` (with raw_relations JSONB)

**코드 위치**: [src/core/processors/semantic_processor.py:509-532](../src/core/processors/semantic_processor.py)

```python
MIN_RELATION_CONFIDENCE = 0.7
MAX_RELATIONS_PER_TERM = 10

sorted_relations = sorted(llm_relations, key=lambda x: x.get('confidence', 0), reverse=True)

for rel in sorted_relations[:MAX_RELATIONS_PER_TERM]:
    if rel['confidence'] < MIN_RELATION_CONFIDENCE:
        continue
    raw_relations.append({...})
```

#### 2.2. ontology_builder.py (Phase 2)

**역할**: raw_relations 검증 및 확정

**검증 단계**:
1. 온톨로지 룰 매칭 (116개 룰)
2. 양쪽 용어 존재 확인
3. 임베딩 유사도 검증 (≥ 0.7)

**입력**: `playbook_semantic_terms.raw_relations`
**출력**: `playbook_semantic_relations`

**코드 위치**: [src/core/processors/ontology_builder.py](../src/core/processors/ontology_builder.py)

### 3. Generators (답변 생성)

#### 3.1. rag_answer_generator.py

**역할**: Evidence-based 답변 생성

**핵심 클래스**:
- `RAGContextFormatter`: 검색 결과 → XML 컨텍스트
- `RAGAnswerGenerator`: LLM 호출 → 근거 기반 답변

**주요 메서드**:
```python
# Context 포맷팅
context = formatter.build_full_context(
    query=query,
    vector_results=vector_results,
    graph_relations=graph_relations,
    ontology_rules=ontology_rules
)

# 답변 생성
result = generator.generate_answer(
    query=query,
    vector_results=vector_results,
    graph_relations=graph_relations,
    ontology_rules=ontology_rules,
    temperature=0.3
)
```

**코드 위치**: [src/core/generators/rag_answer_generator.py](../src/core/generators/rag_answer_generator.py)

### 4. Traversal (그래프 탐색)

**파일 구조**:
- `graph_engine.py`: BFS/DFS 알고리즘
- `subgraph_extractor.py`: 서브그래프 추출
- `path_finder.py`: 최단 경로 찾기

**사용 예시**: [test_chatbot_v2.py:97-257](../scripts/test_chatbot_v2.py)

```python
def get_subgraph(self, center_term, radius=2):
    """중심 용어 기반 서브그래프 추출 (BFS 2-hop)"""
    queue = [(center_id, 0, [center_term])]
    hop_paths = []

    while queue:
        current_id, depth, path = queue.pop(0)
        # ... BFS 탐색 ...
```

---

## 📊 데이터베이스 스키마 (v2.0)

### 1. playbook_documents
```sql
CREATE TABLE playbook_documents (
    doc_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT,
    url TEXT,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. playbook_chunks
```sql
CREATE TABLE playbook_chunks (
    chunk_id SERIAL PRIMARY KEY,
    doc_id INTEGER REFERENCES playbook_documents(doc_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_embedding ON playbook_chunks USING ivfflat (embedding vector_cosine_ops);
```

### 3. playbook_semantic_terms (v2.0)
```sql
CREATE TABLE playbook_semantic_terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term TEXT NOT NULL,
    category TEXT NOT NULL,  -- 11개 카테고리 (v2.0)
    definition TEXT,
    raw_relations JSONB,  -- Phase 1 관계 (미검증)
    source_chunks INTEGER[],  -- 출처 청크 ID 배열
    created_at TIMESTAMP DEFAULT NOW()
);

-- 11개 카테고리 (v2.0)
-- GameObject, Currency_Hard, Currency_Soft, Mechanic, Content,
-- Condition, Segment, Marketing, UX_Factor, Metric, System
```

### 4. playbook_semantic_relations (v2.0)
```sql
CREATE TABLE playbook_semantic_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_term_id UUID REFERENCES playbook_semantic_terms(id) ON DELETE CASCADE,
    target_term_id UUID REFERENCES playbook_semantic_terms(id) ON DELETE CASCADE,
    predicate TEXT NOT NULL,  -- 22개 predicate (v2.0)
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    evidence TEXT,  -- 근거 텍스트
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_relations_source ON playbook_semantic_relations(source_term_id);
CREATE INDEX idx_relations_target ON playbook_semantic_relations(target_term_id);
CREATE INDEX idx_relations_confidence ON playbook_semantic_relations(confidence);

-- 22개 predicates (v2.0)
-- Core Gameplay: triggers, consumes, clears, counters, rewards, requires, contains, unlocks, synergizes_with
-- LiveOps & Business: boosts, drains, promotes, targets
-- Advanced Business Logic: accelerates, converts_to, optimizes, diversifies, impacts
-- UX & Psychology: balances, induces, relieves, maintains
```

### 5. playbook_ontology_rules (v2.0)
```sql
CREATE TABLE playbook_ontology_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_type TEXT NOT NULL,  -- 11개 카테고리
    predicate TEXT NOT NULL,     -- 22개 predicate
    object_type TEXT NOT NULL,   -- 11개 카테고리
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(subject_type, predicate, object_type)
);

-- v2.0: 116개 룰
```

---

## 🧪 테스트 스크립트 매핑

| 스크립트 | 테스트 대상 | 실행 방법 | 출력 |
|---------|------------|----------|------|
| [test_chatbot_v2.py](../scripts/test_chatbot_v2.py) | 전체 GraphRAG 파이프라인 (Query → Answer) | `python3 scripts/test_chatbot_v2.py` | 6단계 추론 과정 + 답변 |
| [test_rag_answer_generation.py](../scripts/test_rag_answer_generation.py) | RAG 답변 생성 (Context Formatter + Generator) | `python3 scripts/test_rag_answer_generation.py` | XML 컨텍스트 + 근거 기반 답변 |
| [diagnose_relations.py](../scripts/diagnose_relations.py) | Phase 2 결과 통계 분석 | `python3 scripts/diagnose_relations.py` | 관계 통계, 연결률, 카테고리 분포 |
| [check_term_relations.py](../scripts/check_term_relations.py) | 특정 용어의 관계 확인 | `python3 scripts/check_term_relations.py "동적 난이도"` | 해당 용어의 모든 관계 |
| [demo_traversal.py](../scripts/demo_traversal.py) | 그래프 탐색 알고리즘 | `python3 scripts/demo_traversal.py` | BFS/DFS 탐색 결과 |

---

## 🚀 실행 가이드

### 1. Phase 1 실행 (용어 추출)

```bash
# 테스트 실행 (100개 문서)
bash run_phase1_test.sh

# 전체 실행 (2,246개 문서)
bash run_phase1_full.sh
```

**예상 소요 시간**:
- 테스트: 5-10분
- 전체: 40-60분

**예상 비용**:
- 테스트: $1-2
- 전체: $20-30

### 2. Phase 2 실행 (관계 검증)

```bash
python3 run_phase2_only.py
```

**예상 소요 시간**: 10-20분 (임베딩 검증)

### 3. 웹 플랫폼 실행

```bash
# Terminal 1: Backend
python3 -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd playbook-web
npm run dev
```

**브라우저**: http://localhost:3000

### 4. CLI 챗봇 실행

```bash
python3 scripts/test_chatbot_v2.py
```

**특징**:
- 6단계 추론 과정 시각화
- Hop-by-hop 경로 추적
- 대화 컨텍스트 유지

---

## 🔄 통합 가능한 컴포넌트

### 1. 통합 대상: test_chatbot_v2.py + rag_answer_generator.py

**현재 상태**:
- `test_chatbot_v2.py`: 자체 컨텍스트 생성 로직 (`build_graph_context()`)
- `rag_answer_generator.py`: XML 기반 구조화된 컨텍스트 생성

**통합 방안**:
```python
# test_chatbot_v2.py 수정
from src.core.generators.rag_answer_generator import RAGContextFormatter, RAGAnswerGenerator

class GraphRAGChatbot:
    def __init__(self):
        # 기존 초기화 유지
        self.formatter = RAGContextFormatter()
        self.generator = RAGAnswerGenerator(self.openai_client)

    def chat(self, user_message):
        # 1-4단계: 기존 로직 유지 (용어 매칭, 그래프 탐색, hop 분석)

        # 5단계: 컨텍스트 생성 (RAGContextFormatter 사용)
        vector_results = self._convert_chunks_to_search_results(subgraph)
        graph_relations = self._convert_edges_to_graph_relations(subgraph)

        # 6단계: 답변 생성 (RAGAnswerGenerator 사용)
        result = self.generator.generate_answer(
            query=user_message,
            vector_results=vector_results,
            graph_relations=graph_relations,
            ontology_rules=self.ontology_rules,
            center_term=center_term
        )
```

**장점**:
- XML 구조화된 컨텍스트 사용 (LLM이 출처 식별 용이)
- Evidence-based 시스템 프롬프트 적용
- 코드 중복 제거

### 2. 통합 대상: 온톨로지 룰 스크립트

**현재 상태**:
- `add_ux_advanced_ontology_rules.py` (v2.0 UX & Advanced Business Logic)
- `add_liveops_ontology_rules.py` (LiveOps)
- `add_missing_ontology_rules.py` (일반 보완)

**통합 방안**:
```python
# scripts/manage_ontology_rules.py (통합 스크립트)

import argparse

def add_rules(rule_type: str):
    """온톨로지 룰 추가"""
    if rule_type == "v2_ux_advanced":
        # add_ux_advanced_ontology_rules.py 로직
    elif rule_type == "liveops":
        # add_liveops_ontology_rules.py 로직
    elif rule_type == "missing":
        # add_missing_ontology_rules.py 로직
    elif rule_type == "all":
        # 모든 룰 추가

def remove_rules(rule_pattern: str):
    """온톨로지 룰 삭제"""
    ...

def list_rules(filter_by: str = None):
    """온톨로지 룰 목록 조회"""
    ...

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["add", "remove", "list"])
    parser.add_argument("--type", choices=["v2_ux_advanced", "liveops", "missing", "all"])
    args = parser.parse_args()
```

**사용 예시**:
```bash
# 룰 추가
python3 scripts/manage_ontology_rules.py add --type v2_ux_advanced
python3 scripts/manage_ontology_rules.py add --type all

# 룰 목록 조회
python3 scripts/manage_ontology_rules.py list

# 특정 패턴 삭제
python3 scripts/manage_ontology_rules.py remove --pattern "test_*"
```

### 3. 통합 대상: 진단 스크립트

**현재 상태**:
- `diagnose_relations.py`: 전체 관계 통계
- `check_term_relations.py`: 특정 용어 관계

**통합 방안**:
```python
# scripts/analyze_knowledge_graph.py (통합 스크립트)

import argparse

def show_statistics():
    """전체 통계 (diagnose_relations.py)"""
    ...

def show_term_relations(term: str):
    """특정 용어 관계 (check_term_relations.py)"""
    ...

def show_category_distribution():
    """카테고리 분포"""
    ...

def show_predicate_distribution():
    """Predicate 분포"""
    ...

def export_graph(format: str):
    """그래프 내보내기 (JSON, CSV, GraphML)"""
    ...

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["stats", "term", "categories", "predicates", "export"])
    parser.add_argument("--term", help="특정 용어")
    parser.add_argument("--format", choices=["json", "csv", "graphml"])
    args = parser.parse_args()
```

**사용 예시**:
```bash
# 전체 통계
python3 scripts/analyze_knowledge_graph.py stats

# 특정 용어
python3 scripts/analyze_knowledge_graph.py term --term "동적 난이도"

# 카테고리 분포
python3 scripts/analyze_knowledge_graph.py categories

# 그래프 내보내기
python3 scripts/analyze_knowledge_graph.py export --format json
```

---

## 📚 문서 정리

### 핵심 문서 (필수)
1. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 프로젝트 구조 및 시스템 흐름 (이 파일)
2. [ONTOLOGY_UPDATE_SUMMARY.md](../ONTOLOGY_UPDATE_SUMMARY.md) - v2.0 온톨로지 업그레이드 요약
3. [RAG_ANSWER_GENERATION.md](RAG_ANSWER_GENERATION.md) - RAG 답변 생성 가이드
4. [READY_TO_RUN.md](../READY_TO_RUN.md) - Phase 1 실행 가이드

### 참고 문서
5. [RAW_RELATIONS_OPTIMIZATION.md](RAW_RELATIONS_OPTIMIZATION.md) - raw_relations 최적화
6. [TRAVERSAL_DESIGN.md](TRAVERSAL_DESIGN.md) - 그래프 탐색 설계
7. [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - 프로젝트 컨텍스트
8. [PHASE1_IMPROVEMENTS.md](../PHASE1_IMPROVEMENTS.md) - Phase 1 개선 내역

---

## 🎯 다음 단계

### 단기 (1-2주)
1. ✅ v2.0 온톨로지 업그레이드 완료
2. ✅ RAG 답변 생성 시스템 구현
3. ⏳ Phase 1 실행 (500개 문서)
4. ⏳ test_chatbot_v2.py + rag_answer_generator.py 통합
5. ⏳ 웹 플랫폼 통합

### 중기 (1개월)
1. 스크립트 통합 (ontology rules, diagnostics)
2. 벡터 검색 + 그래프 탐색 하이브리드 최적화
3. 대화 컨텍스트 유지 개선
4. 답변 품질 평가 시스템

### 장기 (3개월)
1. 멀티모달 지원 (이미지, 표, 그래프)
2. 다국어 지원 (영어, 일본어)
3. 실시간 증분 업데이트
4. 프로덕션 배포

---

**문의**: 구조 관련 질문은 이슈 등록 또는 담당자에게 연락하세요.
