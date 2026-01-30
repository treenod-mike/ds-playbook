# GraphRAG 시스템 통합 가이드

**작성일**: 2026-01-30
**버전**: v3.0
**목적**: test_chatbot_v2.py + rag_answer_generator.py 통합 및 시스템 흐름 개선

---

## 📋 통합 개요

### 통합 목표

1. **코드 중복 제거**: 두 시스템의 컨텍스트 생성 로직 통합
2. **일관성 확보**: 웹 플랫폼과 CLI 챗봇의 동일한 답변 생성 로직
3. **유지보수성 향상**: 단일 소스 of truth로 관리

### 통합 전후 비교

#### Before (v2.0)

```
┌──────────────────────────────┐
│  test_chatbot_v2.py          │
│  ├─ build_graph_context()    │  ← 자체 컨텍스트 생성
│  └─ generate_system_prompt() │  ← 자체 프롬프트 생성
└──────────────────────────────┘

┌──────────────────────────────┐
│  rag_answer_generator.py     │
│  ├─ RAGContextFormatter      │  ← 별도 컨텍스트 생성
│  └─ RAGAnswerGenerator       │  ← 별도 답변 생성
└──────────────────────────────┘

문제점:
- 컨텍스트 생성 로직 중복
- 프롬프트 불일치 가능성
- 유지보수 어려움
```

#### After (v3.0)

```
┌─────────────────────────────────────────────────────┐
│  test_chatbot_v3_integrated.py                      │
│  ├─ RAGContextFormatter (재사용)                   │
│  │   └─ build_full_context() → XML 구조            │
│  │                                                   │
│  ├─ RAGAnswerGenerator (재사용)                    │
│  │   ├─ SYSTEM_PROMPT (Evidence-based)             │
│  │   └─ generate_answer() → 근거 기반 답변         │
│  │                                                   │
│  └─ GraphRAGChatbotV3 (통합 로직)                  │
│      ├─ get_subgraph() (BFS 탐색 유지)              │
│      ├─ _convert_chunks_to_search_results()         │
│      ├─ _convert_edges_to_graph_relations()         │
│      └─ chat() (6단계 프로세스 + RAG 통합)         │
└─────────────────────────────────────────────────────┘

장점:
✅ 코드 중복 제거
✅ 일관된 답변 품질
✅ 단일 소스 유지보수
```

---

## 🔄 주요 변경 사항

### 1. 컨텍스트 생성 로직 교체

#### Before (v2.0)
```python
# test_chatbot_v2.py
def build_graph_context(self, mentioned_terms, subgraph):
    """그래프 기반 컨텍스트 생성"""
    context = f"\n\n## 🎯 지식 그래프 정보\n\n"
    context += f"**중심 개념**: {center_term}\n\n"
    # ... 마크다운 형식으로 컨텍스트 생성 ...
    return context
```

**문제점**:
- 마크다운 형식 (구조화 부족)
- LLM이 출처 식별 어려움
- 메타데이터 누락

#### After (v3.0)
```python
# test_chatbot_v3_integrated.py
from src.core.generators.rag_answer_generator import RAGContextFormatter

# 초기화
self.formatter = RAGContextFormatter()

# XML 구조화된 컨텍스트 생성
vector_results = self._convert_chunks_to_search_results(subgraph['chunks'])
graph_relations = self._convert_edges_to_graph_relations(subgraph)

# RAGContextFormatter 사용 (재사용)
context = self.formatter.build_full_context(
    query=user_message,
    vector_results=vector_results,
    graph_relations=graph_relations,
    ontology_rules=self.ontology_rules,
    center_term=center_term
)
```

**개선점**:
- XML 구조 (명확한 출처)
- 메타데이터 포함 (chunk_id, doc_title, confidence)
- LLM이 정보 식별 용이

### 2. 답변 생성 로직 교체

#### Before (v2.0)
```python
# test_chatbot_v2.py
system_prompt = self.generate_system_prompt(graph_context)

messages = [{"role": "system", "content": system_prompt}]
messages.extend(self.conversation_history[-10:])
messages.append({"role": "user", "content": user_message})

response = self.openai_client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    max_tokens=1024,
    temperature=0.7
)
```

**문제점**:
- 자체 시스템 프롬프트 (일관성 부족)
- 출처 표기 규칙 미정의
- Hallucination 방지 미흡

#### After (v3.0)
```python
# test_chatbot_v3_integrated.py
from src.core.generators.rag_answer_generator import RAGAnswerGenerator

# 초기화
self.generator = RAGAnswerGenerator(self.openai_client)

# RAGAnswerGenerator 사용 (재사용)
result = self.generator.generate_answer(
    query=user_message,
    vector_results=vector_results,
    graph_relations=graph_relations,
    ontology_rules=self.ontology_rules,
    center_term=center_term,
    temperature=0.3  # 보수적 생성
)

if result["success"]:
    assistant_message = result["answer"]
    # 메타데이터 활용 가능
    print(f"사용 토큰: {result['metadata']['tokens_used']}")
```

**개선점**:
- Evidence-based 시스템 프롬프트 (표준화)
- 출처 표기 강제 (`[Source: ...]`)
- Hallucination 방지 강화
- Temperature 0.3 (일관된 답변)

### 3. 데이터 변환 헬퍼 메서드 추가

#### 청크 변환
```python
def _convert_chunks_to_search_results(self, chunk_ids):
    """청크 ID 목록을 SearchResult 객체 리스트로 변환"""
    results = []
    for chunk_id in chunk_ids[:5]:  # 최대 5개
        chunk_result = self.supabase.table('playbook_chunks')\
            .select("chunk_id, doc_id, content")\
            .eq("chunk_id", chunk_id)\
            .limit(1)\
            .execute()

        if chunk_result.data:
            chunk = chunk_result.data[0]
            doc_result = self.supabase.table('playbook_documents')\
                .select("title")\
                .eq("doc_id", chunk['doc_id'])\
                .limit(1)\
                .execute()

            doc_title = doc_result.data[0]['title'] if doc_result.data else "Unknown"

            results.append(SearchResult(
                chunk_id=chunk['chunk_id'],
                doc_id=chunk['doc_id'],
                doc_title=doc_title,
                content=chunk['content'],
                similarity=0.85  # 시뮬레이션
            ))

    return results
```

#### 관계 변환
```python
def _convert_edges_to_graph_relations(self, subgraph):
    """서브그래프의 edges를 GraphRelation 객체 리스트로 변환"""
    relations = []

    for edge in subgraph.get('unique_edges', [])[:10]:  # 최대 10개
        relations.append(GraphRelation(
            source=edge['source'],
            predicate=edge['predicate'],
            target=edge['target'],
            confidence=edge['confidence']
        ))

    return relations
```

---

## 📊 v3.0 시스템 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input                                │
│               "동적 난이도가 뭐야?"                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Term Matching (용어 매칭)                                │
│  find_related_terms()                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Graph Traversal (그래프 탐색)                            │
│  get_subgraph(center_term, radius=2)                         │
│  └─ BFS 2-hop 탐색                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Hop Path Analysis (경로 분석)                            │
│  hop1_paths, hop2_paths 시각화                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Reasoning Chain (추론 체인)                              │
│  reasoning_chain 생성                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Data Conversion (데이터 변환)                            │
│  ├─ _convert_chunks_to_search_results()                     │
│  │   → SearchResult[]                                        │
│  └─ _convert_edges_to_graph_relations()                     │
│      → GraphRelation[]                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Context Formatting (컨텍스트 구조화)                     │
│  RAGContextFormatter.build_full_context()                    │
│  └─ XML 구조 생성                                            │
│      <Context>                                                │
│        <VectorSearchResults>...</VectorSearchResults>         │
│        <GraphRelations>...</GraphRelations>                   │
│        <OntologyRules>...</OntologyRules>                     │
│      </Context>                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Answer Generation (답변 생성)                            │
│  RAGAnswerGenerator.generate_answer()                        │
│  ├─ System Prompt: Evidence-based BI Analyst                │
│  ├─ Temperature: 0.3                                         │
│  └─ Citation: [Source: ...], [Graph: ...]                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  8. Output with Evidence (근거 포함 출력)                    │
│  ├─ 답변: assistant_message                                  │
│  └─ 메타데이터:                                              │
│      - 사용된 청크: 3개                                      │
│      - 사용된 관계: 5개                                      │
│      - 사용 토큰: 1,245                                      │
│      - 대화 컨텍스트: [동적 난이도, 몰입, 리텐션]            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 테스트 가이드

### 1. v3.0 챗봇 실행

```bash
python3 scripts/test_chatbot_v3_integrated.py
```

**환영 메시지**:
```
======================================================================
PokoPoko v3.0 GraphRAG 챗봇 (Evidence-based Answer Generation)
======================================================================

📡 Supabase 연결 중...
✅ Supabase 연결 완료

🤖 OpenAI 연결 중...
✅ OpenAI 연결 완료

📚 온톨로지 데이터 로드 중...
✅ 용어 15056개, 온톨로지 룰 116개 로드

💬 대화를 시작합니다. 종료하려면 'exit' 또는 'quit'를 입력하세요.

안녕하세요! PokoPoko 게임의 지식 그래프 어시스턴트입니다.
게임 메카닉, 이벤트, UX, 비즈니스 로직에 대해 물어보세요!
v3.0: Evidence-based 답변 생성 + XML 구조화된 컨텍스트

You:
```

### 2. 테스트 케이스

#### 케이스 1: 기본 질의
```
You: 동적 난이도가 뭐야?
```

**기대 결과**:
- ✅ 용어 매칭 성공
- ✅ 그래프 탐색 (Hop 1, 2)
- ✅ XML 컨텍스트 생성
- ✅ Evidence-based 답변 (출처 포함)

#### 케이스 2: 복합 질의
```
You: 클로버를 효율적으로 사용하는 방법은?
```

**기대 결과**:
- ✅ 여러 관계 탐색 (consumes, requires, drains 등)
- ✅ 비즈니스 인사이트 도출
- ✅ 출처 표기 (`[Source: ...]`)

#### 케이스 3: 대화 컨텍스트
```
You: 동적 난이도가 뭐야?
Assistant: [답변]
You: 그럼 리텐션을 높이려면 어떻게 해야 해?
```

**기대 결과**:
- ✅ 이전 대화 용어 기억 (동적 난이도)
- ✅ 관계 체인 활용 (동적 난이도 → 몰입 → 리텐션)

### 3. 비교 테스트

#### v2.0 vs v3.0 비교

| 항목 | v2.0 | v3.0 | 개선 |
|-----|------|------|------|
| 컨텍스트 형식 | 마크다운 | XML | ✅ 구조화 |
| 출처 표기 | 미흡 | 강제 | ✅ 신뢰성 |
| Hallucination | 가능 | 방지 | ✅ 정확도 |
| 코드 중복 | 있음 | 없음 | ✅ 유지보수 |
| Temperature | 0.7 | 0.3 | ✅ 일관성 |

**테스트 방법**:
```bash
# v2.0 실행
python3 scripts/test_chatbot_v2.py
> 동적 난이도가 뭐야?

# v3.0 실행
python3 scripts/test_chatbot_v3_integrated.py
> 동적 난이도가 뭐야?

# 답변 비교
# - 출처 표기 여부
# - 답변 논리성
# - 근거 명확성
```

---

## 🚀 웹 플랫폼 통합 방안

### 1. FastAPI 엔드포인트 수정

```python
# src/api/main.py

from src.core.generators.rag_answer_generator import (
    RAGAnswerGenerator,
    RAGContextFormatter,
    SearchResult,
    GraphRelation
)

# 전역 인스턴스
formatter = RAGContextFormatter()
generator = RAGAnswerGenerator(openai_client)

@app.post("/api/chat")
async def chat(query: str):
    """챗봇 API (v3.0: RAG Generator 통합)"""

    # 1. 용어 추출
    mentioned_terms = find_related_terms(query)

    # 2. 그래프 탐색
    subgraph = get_subgraph(mentioned_terms[0]['term'], radius=2)

    # 3. 데이터 변환
    vector_results = convert_chunks_to_search_results(subgraph['chunks'])
    graph_relations = convert_edges_to_graph_relations(subgraph)

    # 4. 답변 생성 (RAG Generator 사용)
    result = generator.generate_answer(
        query=query,
        vector_results=vector_results,
        graph_relations=graph_relations,
        ontology_rules=ontology_rules,
        center_term=mentioned_terms[0]['term'],
        temperature=0.3
    )

    if result["success"]:
        return {
            "answer": result["answer"],
            "metadata": result["metadata"],
            "reasoning": {
                "hop_paths": subgraph['hop_paths'],
                "reasoning_chain": subgraph['reasoning_chain']
            }
        }
    else:
        return {"error": result["error"]}
```

### 2. 스트리밍 API

```python
from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
async def chat_stream(query: str):
    """스트리밍 챗봇 API"""

    # ... 데이터 준비 (동일) ...

    def generate():
        for token in generator.generate_answer_streaming(
            query=query,
            vector_results=vector_results,
            graph_relations=graph_relations,
            ontology_rules=ontology_rules,
            center_term=center_term
        ):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")
```

### 3. 프론트엔드 통합 (Next.js)

```typescript
// playbook-web/src/components/Chat.tsx

async function sendMessage(query: string) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });

  const data = await response.json();

  // 답변 표시
  setMessages([...messages, {
    role: 'assistant',
    content: data.answer,
    metadata: data.metadata,
    reasoning: data.reasoning
  }]);
}

// 스트리밍 버전
async function sendMessageStreaming(query: string) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });

  const reader = response.body?.getReader();
  let accumulated = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    accumulated += new TextDecoder().decode(value);
    setCurrentMessage(accumulated);
  }
}
```

---

## 📝 마이그레이션 체크리스트

### Phase 1: 로컬 테스트
- [ ] v3.0 챗봇 실행 성공
- [ ] 기본 질의 테스트 통과
- [ ] 복합 질의 테스트 통과
- [ ] 대화 컨텍스트 유지 확인
- [ ] v2.0 대비 품질 개선 확인

### Phase 2: API 통합
- [ ] FastAPI 엔드포인트 수정
- [ ] 스트리밍 API 구현
- [ ] 에러 핸들링 추가
- [ ] API 테스트 작성

### Phase 3: 웹 플랫폼 통합
- [ ] 프론트엔드 API 호출 수정
- [ ] 스트리밍 UI 구현
- [ ] 답변 메타데이터 표시
- [ ] 추론 과정 시각화

### Phase 4: 프로덕션 배포
- [ ] 성능 테스트
- [ ] 부하 테스트
- [ ] 모니터링 설정
- [ ] 배포 및 검증

---

## 🔧 트러블슈팅

### 문제 1: SearchResult 변환 실패

**증상**: `_convert_chunks_to_search_results()` 에서 빈 리스트 반환

**원인**: `source_chunks` 필드가 비어있음

**해결**:
```python
# Phase 1 실행 시 source_chunks 저장 확인
# semantic_processor.py에서 source_chunks 필드 업데이트 로직 추가
```

### 문제 2: 답변에 출처 없음

**증상**: 답변에 `[Source: ...]` 표기 없음

**원인**: LLM이 시스템 프롬프트 무시

**해결**:
```python
# Temperature 낮추기
result = generator.generate_answer(..., temperature=0.2)

# 또는 프롬프트 강화
# RAGAnswerGenerator.SYSTEM_PROMPT에서 Citation 규칙 강조
```

### 문제 3: v2.0 대비 느린 응답

**증상**: v3.0이 v2.0보다 느림

**원인**: XML 파싱 오버헤드

**해결**:
```python
# 청크/관계 수 제한
vector_results = self._convert_chunks_to_search_results(subgraph['chunks'][:3])  # 5→3
graph_relations = self._convert_edges_to_graph_relations(subgraph)[:5]  # 10→5
```

---

## 📚 참고 문서

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 프로젝트 구조 및 시스템 흐름
- [RAG_ANSWER_GENERATION.md](RAG_ANSWER_GENERATION.md) - RAG 답변 생성 가이드
- [ONTOLOGY_UPDATE_SUMMARY.md](../ONTOLOGY_UPDATE_SUMMARY.md) - v2.0 온톨로지 업그레이드

---

**문의**: 통합 관련 질문은 이슈 등록 또는 담당자에게 연락하세요.
