# raw_relations 최적화 전략

## 현재 상황

### v1.0 (기존)
- raw_relations 평균: **0.0개/용어**
- 문제: 관계가 거의 추출되지 않음

### v2.0 (개선 후 예상)
- raw_relations 평균: **2~7개/용어**
- 문제: 관계 폭발, 노이즈 증가 가능성

---

## 최적화 전략

### 전략 1: Confidence Threshold (권장)

**목적**: 낮은 신뢰도 관계 필터링으로 품질 유지

#### 1.1 기본 필터링 (Confidence >= 0.7)
```python
# semantic_processor.py Line 507 이후 수정
MIN_RELATION_CONFIDENCE = 0.7  # 70% 이상만 저장

raw_relations = []
for rel in llm_relations:
    confidence = rel.get('confidence', 0.8)

    # [FILTER] Skip low confidence relations
    if confidence < MIN_RELATION_CONFIDENCE:
        logger.debug(f"Skipping low confidence relation: {rel} (conf: {confidence})")
        continue

    target_term = rel.get('term', '').lower().strip() if isinstance(rel.get('term'), str) else rel.get('target', '').lower().strip()
    relation_type = rel.get('type', 'related_to')

    raw_relations.append({
        "target": target_term,
        "type": relation_type,
        "confidence": confidence,
        "desc": rel.get('desc', '')
    })
```

**효과**:
- confidence < 0.7 관계 제거 (약 20-30% 감소 예상)
- 품질 향상 (노이즈 제거)

**예시**:
```
[이전] "동적 난이도" -> 7개 관계
  - balances "유저 실력" (0.95) ✅
  - diversifies "경험" (0.90) ✅
  - relieves "좌절" (0.90) ✅
  - relieves "지루함" (0.90) ✅
  - maintains "몰입" (0.95) ✅
  - prevents "이탈" (0.65) ❌ (필터링)
  - optimizes "리텐션" (0.65) ❌ (필터링)

[이후] "동적 난이도" -> 5개 관계
```

#### 1.2 동적 임계값 (Predicate별 차등 적용)

```python
# 관계 타입별 최소 신뢰도 설정
PREDICATE_MIN_CONFIDENCE = {
    # Core Gameplay - 높은 정확도 필요
    'triggers': 0.8,
    'consumes': 0.8,
    'clears': 0.8,

    # LiveOps & Business - 보통
    'boosts': 0.7,
    'drains': 0.7,
    'promotes': 0.7,
    'targets': 0.75,

    # Advanced Business - 추론 허용
    'optimizes': 0.65,
    'diversifies': 0.65,
    'impacts': 0.6,  # 가장 낮음 (중립적 관계)

    # UX & Psychology - 추론 허용
    'balances': 0.7,
    'induces': 0.7,
    'relieves': 0.65,
    'maintains': 0.7,
}

for rel in llm_relations:
    relation_type = rel.get('type', 'related_to')
    confidence = rel.get('confidence', 0.8)
    min_conf = PREDICATE_MIN_CONFIDENCE.get(relation_type, 0.7)

    if confidence < min_conf:
        logger.debug(f"Skipping {relation_type} with conf {confidence} < {min_conf}")
        continue

    # ... 저장 로직
```

**효과**:
- 게임 로직 관계: 높은 정확도 유지
- 비즈니스/UX 관계: 추론 허용으로 풍부함 유지

---

### 전략 2: Top-K 제한 (선택)

**목적**: 용어당 최대 관계 수 제한

```python
MAX_RELATIONS_PER_TERM = 10  # 용어당 최대 10개

# Sort by confidence descending
sorted_relations = sorted(llm_relations, key=lambda x: x.get('confidence', 0), reverse=True)

# Take top K
top_relations = sorted_relations[:MAX_RELATIONS_PER_TERM]

for rel in top_relations:
    # ... 저장 로직
```

**효과**:
- 관계 폭발 방지
- 최고 신뢰도 관계만 저장

**주의**:
- 낮은 K 값: 중요한 관계 누락 가능
- 높은 K 값: 효과 미미

**권장 K 값**:
- K=5: 매우 보수적 (핵심 관계만)
- K=10: 균형적 (권장)
- K=15: 풍부함 우선

---

### 전략 3: Predicate 타입별 제한 (선택)

**목적**: 같은 타입의 관계가 너무 많은 경우 제한

```python
MAX_SAME_TYPE_RELATIONS = 3  # 같은 타입 최대 3개

from collections import defaultdict
type_count = defaultdict(int)

for rel in sorted_relations:  # Already sorted by confidence
    relation_type = rel.get('type', 'related_to')

    if type_count[relation_type] >= MAX_SAME_TYPE_RELATIONS:
        logger.debug(f"Skipping {relation_type} - already have {type_count[relation_type]}")
        continue

    type_count[relation_type] += 1
    # ... 저장 로직
```

**예시**:
```
[이전] "동적 난이도"
  - relieves "좌절" (0.90)
  - relieves "지루함" (0.90)
  - relieves "막힘" (0.85)
  - relieves "불만" (0.80)
  → 4개 relieves 관계

[이후] "동적 난이도"
  - relieves "좌절" (0.90)
  - relieves "지루함" (0.90)
  - relieves "막힘" (0.85)
  → 3개 relieves 관계 (최고 신뢰도 3개만)
```

---

### 전략 4: Phase 2 필터링 강화 (현재 적용 중)

**Phase 2에서 온톨로지 룰 검증으로 필터링**

현재 Phase 2는 이미 다음을 수행:
1. `playbook_ontology_rules`에 있는 패턴만 통과
2. 양쪽 용어가 모두 존재하는 경우만 통과
3. 임베딩 유사도 검증

→ **raw_relations이 많아도 Phase 2에서 자동 정제됨**

---

## 권장 조합

### Option A: 보수적 접근 (품질 우선)
```python
MIN_RELATION_CONFIDENCE = 0.75
MAX_RELATIONS_PER_TERM = 8
```
- 예상 평균: 2-4개/용어
- 품질: 높음
- 커버리지: 중간

### Option B: 균형적 접근 (권장)
```python
MIN_RELATION_CONFIDENCE = 0.7
MAX_RELATIONS_PER_TERM = 10
```
- 예상 평균: 3-6개/용어
- 품질: 중간-높음
- 커버리지: 높음

### Option C: 풍부함 우선 (실험적)
```python
MIN_RELATION_CONFIDENCE = 0.6
MAX_RELATIONS_PER_TERM = 15
```
- 예상 평균: 5-10개/용어
- 품질: 중간
- 커버리지: 매우 높음

---

## 구현 우선순위

### 1단계: Confidence Threshold (즉시 적용 가능)
- 구현 난이도: ⭐ (매우 쉬움)
- 효과: ⭐⭐⭐⭐ (매우 높음)
- 부작용: 거의 없음

### 2단계: Predicate별 차등 임계값 (선택)
- 구현 난이도: ⭐⭐ (쉬움)
- 효과: ⭐⭐⭐ (높음)
- 부작용: 없음

### 3단계: Top-K 제한 (필요시)
- 구현 난이도: ⭐⭐ (쉬움)
- 효과: ⭐⭐⭐ (높음)
- 부작용: 중요한 관계 누락 가능

### 4단계: 타입별 제한 (필요시)
- 구현 난이도: ⭐⭐⭐ (보통)
- 효과: ⭐⭐ (보통)
- 부작용: 같은 타입 관계 누락 가능

---

## 측정 지표

### 최적화 전후 비교 지표

1. **관계 수 지표**
   - 평균 raw_relations 수/용어
   - 최대 raw_relations 수
   - 분포 (25%, 50%, 75%, 95% 백분위)

2. **품질 지표**
   - Phase 2 통과율 (raw_relations → semantic_relations)
   - 평균 confidence
   - 낮은 confidence 관계 비율 (< 0.7)

3. **성능 지표**
   - Phase 1 실행 시간
   - Phase 2 실행 시간
   - DB 저장 용량

### 측정 스크립트
```bash
# 관계 통계 확인
python3 scripts/diagnose_relations.py

# raw_relations 상세 분석
python3 scripts/analyze_raw_relations.py
```

---

## 다음 단계

1. **Option B (균형적 접근) 구현**
   ```bash
   # semantic_processor.py에 필터링 로직 추가
   MIN_RELATION_CONFIDENCE = 0.7
   MAX_RELATIONS_PER_TERM = 10
   ```

2. **테스트 실행**
   ```bash
   python3 scripts/clear_phase1_data.py
   bash run_phase1_test.sh
   ```

3. **결과 분석**
   ```bash
   python3 scripts/diagnose_relations.py
   ```

4. **필요시 임계값 조정**
   - 관계가 너무 적으면: MIN_CONFIDENCE 낮추기 (0.65)
   - 관계가 너무 많으면: MIN_CONFIDENCE 높이기 (0.75)

---

**작성일**: 2026-01-30
**버전**: Phase 1 v2.0
