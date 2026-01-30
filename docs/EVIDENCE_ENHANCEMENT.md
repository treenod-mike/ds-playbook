# Evidence-based Relation Enhancement

**작성일**: 2026-01-30
**버전**: v3.1 (Evidence Text Integration)
**목적**: 관계의 근거 텍스트를 LLM 컨텍스트에 포함하여 답변 품질 향상

---

## 📋 개요

### 문제점
기존 시스템에서는 관계 정보만 제공:
```
동적 난이도 --[balances]--> 유저 실력 (신뢰도: 0.95)
```

LLM이 이 관계가 **왜** 존재하는지, **어디서** 나왔는지 알 수 없어:
- 추상적인 답변 생성
- Hallucination 위험 증가
- 출처 표기 불가

### 해결 방안
관계의 **근거 텍스트**를 함께 제공:
```
동적 난이도 --[balances]--> 유저 실력 (신뢰도: 0.95)
근거: "[155레벨 기획서] 유저 실력에 맞춰 자동으로 난이도를 조절합니다..."
```

이제 LLM이:
- 구체적이고 정확한 답변 생성 가능
- 원본 문서 텍스트 기반 출처 표기
- Hallucination 방지

---

## 🗄️ DB 스키마 활용

### playbook_semantic_relations 테이블

```sql
CREATE TABLE playbook_semantic_relations (
    id UUID PRIMARY KEY,
    source_term_id UUID REFERENCES playbook_semantic_terms(id),
    target_term_id UUID REFERENCES playbook_semantic_terms(id),
    predicate TEXT,
    confidence FLOAT,

    -- Evidence 컬럼 (기존 스키마)
    evidence TEXT,                -- LLM이 추출한 관계의 근거 텍스트
    evidence_chunk_id UUID REFERENCES playbook_chunks(id),  -- 근거가 된 청크

    ...
);
```

**활용 방식**:
1. **evidence**: LLM이 Phase 2에서 추출한 짧은 근거 텍스트 (우선 사용)
2. **evidence_chunk_id**: 근거가 된 청크 ID → 전체 문단 조회 가능 (보조)

---

## 🔧 구현 내용

### 1. get_subgraph 함수 수정 (v2, v3 공통)

#### Before
```python
# Relations SELECT (evidence 정보 없음)
outgoing = self.supabase.table('playbook_semantic_relations')\
    .select("id, source_term_id, target_term_id, predicate, confidence")\
    .eq("source_term_id", current_id)\
    .execute()
```

#### After
```python
# Evidence 정보 포함
outgoing = self.supabase.table('playbook_semantic_relations')\
    .select("id, source_term_id, target_term_id, predicate, confidence, evidence, evidence_chunk_id")\
    .eq("source_term_id", current_id)\
    .execute()
```

### 2. Evidence Chunk 조회 로직 추가

```python
# [추가] 1. 수집된 엣지들에서 evidence_chunk_id 추출
chunk_ids = set()
for edge in visited_edges.values():
    if edge.get('evidence_chunk_id'):
        chunk_ids.add(edge['evidence_chunk_id'])

# [추가] 2. 실제 청크 텍스트 조회
evidence_map = {}
if chunk_ids:
    chunks_result = self.supabase.table('playbook_chunks')\
        .select("id, content, metadata, doc_id")\
        .in_("id", list(chunk_ids))\
        .execute()

    for c in chunks_result.data:
        title = c.get('metadata', {}).get('title', 'Unknown Doc')
        content_preview = c['content'][:100] + "..."
        evidence_map[str(c['id'])] = f"[{title}] {content_preview}"
```

### 3. unique_edges 구조 확장

```python
unique_edges[edge_key] = {
    'source': source_term,
    'predicate': edge['predicate'],
    'target': target_term,
    'confidence': edge['confidence'],

    # [추가] Evidence 텍스트
    'evidence_text': evidence_text,  # LLM에게 전달
    'evidence_chunk_id': edge.get('evidence_chunk_id')
}
```

**evidence_text 우선순위**:
1. `edge['evidence']` - LLM이 추출한 짧은 근거 (최우선)
2. `evidence_map[chunk_id]` - 전체 청크 미리보기 (보조)

### 4. LLM 프롬프트 개선 (test_chatbot_v2.py)

#### build_graph_context 함수

**Before**:
```python
context += f"- {edge['source']} → {edge['predicate']} → {edge['target']} (신뢰도: {edge['confidence']:.2f})\n"
```

**After**:
```python
relation_str = f"- {edge['source']} → {edge['predicate']} → {edge['target']} (신뢰도: {edge['confidence']:.2f})"

# Evidence 텍스트가 있으면 추가
if edge.get('evidence_text'):
    relation_str += f"\n  근거: \"{edge['evidence_text'][:150]}...\""

context += relation_str + "\n"
```

### 5. GraphRelation 변환 개선 (test_chatbot_v3_integrated.py)

```python
def _convert_edges_to_graph_relations(self, subgraph):
    relations = []
    for edge in subgraph.get('unique_edges', [])[:10]:
        relations.append(GraphRelation(
            source=edge['source'],
            predicate=edge['predicate'],
            target=edge['target'],
            confidence=edge['confidence'],
            evidence=edge.get('evidence_text', '')  # [추가]
        ))
    return relations
```

---

## 📊 답변 품질 비교

### Before (근거 없음)

**LLM 프롬프트**:
```
**관계** (실제 데이터):
- 동적 난이도 → balances → 유저 실력 (신뢰도: 0.95)
- 동적 난이도 → maintains → 몰입 (신뢰도: 0.90)
```

**LLM 답변**:
```
동적 난이도는 유저 실력과 균형을 맞추고 몰입을 유지하는 시스템입니다.
이를 통해 게임 경험을 최적화합니다.
```
❌ **문제점**: 추상적, 근거 부족, 출처 표기 불가

---

### After (근거 포함)

**LLM 프롬프트**:
```
**관계** (실제 데이터):
- 동적 난이도 → balances → 유저 실력 (신뢰도: 0.95)
  근거: "[155레벨 기획서] 유저의 실력 수준에 맞춰 자동으로 난이도를 조절합니다. 너무 어렵거나 쉬운 경험을 방지..."

- 동적 난이도 → maintains → 몰입 (신뢰도: 0.90)
  근거: "[UX 개선 방안] 적절한 난이도 밸런스는 지속적인 몰입(Flow) 상태를 유지시킵니다..."
```

**LLM 답변**:
```
## 동적 난이도

### 핵심 답변
동적 난이도 시스템은 유저의 실력 수준에 맞춰 자동으로 난이도를 조절합니다.
[Source: 155레벨 기획서]

이를 통해 너무 어렵거나 쉬운 경험을 방지하여 지속적인 몰입(Flow) 상태를
유지시킵니다. [Source: UX 개선 방안]

### 비즈니스 인사이트
적절한 난이도 밸런스는 좌절이나 지루함으로 인한 이탈을 방지하여
리텐션 향상에 기여합니다.
```
✅ **개선점**: 구체적, 출처 명확, 실제 문서 기반

---

## 🎯 기대 효과

### 1. Hallucination 방지 강화
- **Before**: 관계만 제공 → LLM이 상상력으로 채움
- **After**: 원본 텍스트 제공 → LLM이 실제 내용 기반 답변

### 2. 답변 품질 향상
| 항목 | Before | After |
|------|--------|-------|
| 구체성 | 추상적 | 구체적 원문 기반 |
| 출처 표기 | 불가능 | 문서명 명시 가능 |
| 신뢰도 | 낮음 | 높음 (검증 가능) |
| 근거 확인 | 불가능 | 가능 (청크 ID 제공) |

### 3. 사용자 경험 개선
```
[사용자]: "동적 난이도가 왜 좋은가요?"

[AI - Before]:
"동적 난이도는 게임 밸런스를 조정합니다."
❓ 어떻게? 왜? 출처는?

[AI - After]:
"155레벨 기획서에 따르면, 동적 난이도는 유저 실력에 맞춰
자동으로 조절되어 좌절이나 지루함을 방지합니다.
이는 지속적인 몰입(Flow) 상태 유지로 이어집니다."
✅ 구체적, 출처 명확, 설득력 있음
```

---

## 🚀 사용 가이드

### Phase 2 실행 시 (Relations 생성)

LLM이 관계 추출 시 **evidence**와 **evidence_chunk_id** 함께 저장:

```python
# Phase 2: Relation Extraction
relation = {
    "source_term_id": uuid_1,
    "target_term_id": uuid_2,
    "predicate": "balances",
    "confidence": 0.95,

    # [중요] Evidence 저장
    "evidence": "유저 실력에 맞춰 자동으로 난이도를 조절합니다",  # LLM 추출 텍스트
    "evidence_chunk_id": chunk_uuid  # 근거가 된 청크
}

supabase.table('playbook_semantic_relations').insert(relation).execute()
```

### 챗봇 실행

**v2.0 (그래프 기반 프롬프트)**:
```bash
python3 scripts/test_chatbot_v2.py
```
- 관계 프롬프트에 근거 텍스트 자동 포함
- LLM이 더 정확한 답변 생성

**v3.0 (RAG 통합)**:
```bash
python3 scripts/test_chatbot_v3_integrated.py
```
- GraphRelation에 evidence 포함
- RAGAnswerGenerator가 출처 표기 활용

---

## 🔍 검증 방법

### 1. Evidence 데이터 확인

```sql
-- Evidence가 있는 관계 조회
SELECT
    s.term AS source,
    r.predicate,
    t.term AS target,
    r.confidence,
    r.evidence,
    r.evidence_chunk_id
FROM playbook_semantic_relations r
JOIN playbook_semantic_terms s ON r.source_term_id = s.id
JOIN playbook_semantic_terms t ON r.target_term_id = t.id
WHERE r.evidence IS NOT NULL
LIMIT 10;
```

### 2. 챗봇 답변 품질 검증

**테스트 질문**:
```
"동적 난이도가 뭐야?"
"클로버는 어디에 쓰이나요?"
"리텐션을 높이려면 어떻게 해야 하나요?"
```

**확인 항목**:
- [ ] 관계 설명에 구체적인 텍스트 사용
- [ ] 출처 표기 (문서명)
- [ ] 추상적 표현 최소화
- [ ] 원본 문서와 일치하는 내용

### 3. 프롬프트 확인

챗봇 실행 시 "5️⃣ LLM 컨텍스트 생성" 단계에서 출력되는 프롬프트 확인:

```
**관계** (실제 데이터, 중복 제거, 5개):
- 동적 난이도 → balances → 유저 실력 (신뢰도: 0.95)
  근거: "[155레벨 기획서] 유저 실력에 맞춰..."  ← 이 부분 확인
```

---

## 📈 성능 영향

### 추가 쿼리
- **Before**: 관계 조회만 (1 query)
- **After**: 관계 + 청크 조회 (2 queries)

### 쿼리 최적화
```python
# 배치 조회 (N+1 문제 방지)
chunks_result = self.supabase.table('playbook_chunks')\
    .select("id, content, metadata")\
    .in_("id", list(chunk_ids))  # 한 번에 여러 청크 조회
    .execute()
```

### 예상 오버헤드
- 청크 조회: +50-100ms (배치 조회)
- 메모리: +10KB (청크 미리보기 100자 × 10개 관계)
- **총 영향**: 미미 (전체 응답 시간의 <3%)

---

## 🔄 마이그레이션 가이드

### 기존 데이터 (Phase 2 이전)
- `evidence` 및 `evidence_chunk_id`가 NULL
- 시스템은 정상 작동 (NULL 체크 포함)
- 근거 없이 관계만 표시

### Phase 2 재실행 (권장)
```bash
# 1. 기존 관계 삭제
DELETE FROM playbook_semantic_relations;

# 2. Phase 2 재실행 (evidence 포함)
bash run_phase2_test.sh

# 3. 확인
SELECT COUNT(*) FROM playbook_semantic_relations WHERE evidence IS NOT NULL;
```

---

## 📚 관련 문서

- [V3_INTEGRATION_STATUS.md](V3_INTEGRATION_STATUS.md) - v3.0 통합 상태
- [RAG_ANSWER_GENERATION.md](RAG_ANSWER_GENERATION.md) - RAG 시스템 상세
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 전체 프로젝트 구조

---

## ✅ 체크리스트

### 구현 완료
- [x] `get_subgraph` 함수에 evidence 조회 로직 추가
- [x] `unique_edges`에 `evidence_text` 필드 추가
- [x] v2.0 프롬프트에 근거 텍스트 포함
- [x] v3.0 GraphRelation 변환 개선
- [x] NULL 체크 및 예외 처리

### 다음 단계
- [ ] Phase 2 실행하여 실제 evidence 데이터 생성
- [ ] 답변 품질 A/B 테스트 (Before/After)
- [ ] Evidence가 긴 경우 요약 로직 추가 고려
- [ ] 사용자 피드백 수집

---

**문의**: 구현 관련 질문은 이슈 등록 또는 담당자에게 연락하세요.
