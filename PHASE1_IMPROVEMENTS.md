# Phase 1 개선사항 (2026-01-29)

## 배경

Phase 2 재실행으로 관계 수가 124 → 202개 (+63%)로 증가했지만, 여전히 연결률이 1.8%에 불과합니다.

**근본 원인**: LLM이 Phase 1에서 `relations` 필드를 거의 생성하지 않음 (평균 0.0개/용어)

## 개선 내용

### 1. 프롬프트 강화 (`prompts/system_pokopoko.md`)

#### 변경사항

1. **LiveOps & Business Logic 관계 타입 추가 (13개로 확장)**
   - **Core Gameplay (9개)**: triggers, consumes, clears, counters, rewards, requires, contains, unlocks, synergizes_with
   - **LiveOps & Business (4개)**: boosts, drains, promotes, targets ⚠️

   **새로운 관계 타입**:
   - `boosts`: 이벤트/시스템 → 지표/행동 강화 (예: "턴릴레이" boosts "DAU")
   - `drains`: 컨텐츠 → 재화 싱크 (예: "계속하기" drains "다이아몬드")
   - `promotes`: 상황 → 구매 촉진 (예: "난이도 상승" promotes "계속하기")
   - `targets`: 상품/이벤트 → 유저 세그먼트 (예: "웰컴 패키지" targets "신규 유저")

2. **추출 범위 명확화 (이벤트/메타 게임 강조)**
   ```markdown
   포코포코는 매치3 퍼즐 게임이지만, 다음 모든 영역에서 용어를 추출해야 합니다:
   1. 핵심 게임플레이: 매치3, 블록, 폭탄 등
   2. **메타 게임: 이벤트, BM, 랭킹, 미션 등 ⚠️**
   3. 경제 시스템: 클로버, 체리, 다이아몬드 등

   특히 이벤트 관련 용어(턴릴레이, BM, 이벤트 포인트 등)를 빠뜨리지 마십시오!
   ```

3. **이벤트/메타 게임 예시 추가**
   - 입력 예시 2: 턴릴레이 이벤트 문서
   - 출력 예시 2: BM, 이벤트 포인트, 이벤트 스테이지 + LiveOps 관계
   - 패턴 6: 이벤트/메타 게임 패턴
   - 패턴 7: LiveOps & 비즈니스 로직 패턴 (boosts, drains, promotes, targets)

4. **relations 필드 필수화 명시**
   ```markdown
   **⚠️ CRITICAL: `relations` 필드는 필수입니다!**
   모든 용어는 최소 1개 이상의 관계를 가져야 합니다.
   관계를 찾을 수 없으면 해당 용어를 추출하지 마십시오.
   ```

5. **관계 추출 가이드라인 추가**
   - 모든 용어는 **최소 1개 이상의 관계** 필수
   - 관계를 찾기 어려운 용어는 추출하지 마십시오
   - 문서에서 명시적으로 언급된 관계 우선 추출
   - 게임 로직 상 당연한 관계도 포함 (예: "스테이지" consumes "클로버")
   - 양방향 관계를 모두 추출

6. **정확성보다 풍부함 우선**
   - 기존: "확실하지 않은 관계는 포함하지 마십시오"
   - 개선: "관계가 확실하지 않더라도 합리적으로 추론 가능하면 낮은 신뢰도로 포함 (최소 confidence: 0.6)"

7. **출력 검증 체크리스트 추가**
   - [ ] 모든 용어에 relations 배열이 있습니까?
   - [ ] 각 relations 배열에 최소 1개 이상의 관계가 있습니까?
   - [ ] 각 관계에 target, type, confidence가 모두 포함되어 있습니까?
   - [ ] type은 13가지 허용된 서술어 중 하나입니까?
   - [ ] 이벤트/BM 문서인 경우 LiveOps 관계를 포함했습니까?

8. **금지 사항 명확화**
   - ❌ **relations 필드가 비어있는 용어 추출 금지** (최소 1개 이상 필수)

### 2. 코드 검증 강화 (`src/core/processors/semantic_processor.py`)

#### 추가된 검증 로직

```python
# [VALIDATION] Skip terms without relations
llm_relations = term_data.get('relations', [])
if not llm_relations or len(llm_relations) == 0:
    logger.warning(f"Skipping term '{term}' - no relations found (Phase 1 validation)")
    continue
```

**효과**: LLM이 relations 없는 용어를 출력하더라도, 프로세서 단계에서 필터링하여 저장하지 않음

### 3. 온톨로지 룰 확장 (`playbook_ontology_rules`)

#### 추가된 LiveOps 룰 (14개)

```bash
python3 scripts/add_liveops_ontology_rules.py
```

**새로운 관계 패턴**:
- `content --[boosts]--> system/mechanic` (이벤트 → 지표/행동 강화)
- `content/mechanic/gameobject --[drains]--> resource` (재화 싱크)
- `content/mechanic/condition/gameobject --[promotes]--> content/mechanic` (구매 촉진)
- `content/mechanic --[targets]--> system` (유저 세그먼트 타겟팅)

**총 온톨로지 룰**: 65개 → 79개 (14개 증가)

## 예상 효과

### 현재 상태 (개선 전)
- 문서: 2,246개
- 용어: 15,056개
- 관계: 202개 (1.8% 연결률)
- raw_relations 평균: 0.0개/용어

### 예상 결과 (개선 후)
- 문서: 2,246개 (동일)
- 용어: **5,000-8,000개** (관계 없는 용어 필터링으로 감소)
- 관계: **2,000-5,000개** (10배 이상 증가)
- 연결률: **30-50%** (25배 이상 증가)
- raw_relations 평균: **2-3개/용어** (∞ 증가)

### 품질 개선
1. **BM, 이벤트 이름 등 중요 용어의 관계 복원**
   - 현재: BM, 턴릴레이 등의 용어가 관계 없이 고립됨
   - 개선 후: 이벤트-BM-리소스 관계 체인 형성

2. **실용적인 GraphRAG 경험**
   - 현재: 대부분의 질문에 "관계 없음" 응답
   - 개선 후: 풍부한 관계 기반 추론 가능

3. **신뢰도 기반 필터링**
   - 불확실한 관계도 낮은 신뢰도로 포함
   - 사용자는 신뢰도 점수를 보고 판단 가능

## 실행 방법

### Option A: 소규모 테스트 (권장)

```bash
# 100개 문서로 먼저 테스트
python3 run_full_pipeline.py --phase 1 --max-pages 100

# 결과 확인
python3 scripts/diagnose_relations.py

# 성공 시 전체 실행
python3 run_full_pipeline.py --phase 1 --max-pages 2246
```

**예상 소요시간**: 테스트 5-10분, 전체 30-60분

**예상 비용**: 테스트 $1-2, 전체 $20-40

### Option B: 전체 실행

```bash
# 전체 문서 한번에 실행
python3 run_full_pipeline.py --phase 1 --max-pages 2246

# 결과 확인
python3 scripts/diagnose_relations.py
python3 scripts/check_term_relations.py 빈칸
python3 scripts/check_term_relations.py BM
```

## 검증 방법

### 1. 진단 스크립트 실행

```bash
python3 scripts/diagnose_relations.py
```

**확인 포인트**:
- [ ] raw_relations 평균이 2.0 이상인가?
- [ ] 총 관계 수가 2,000개 이상인가?
- [ ] 연결률이 30% 이상인가?

### 2. 특정 용어 확인

```bash
# 이전에 관계가 없던 용어 확인
python3 scripts/check_term_relations.py BM
python3 scripts/check_term_relations.py 턴릴레이
python3 scripts/check_term_relations.py 동물
python3 scripts/check_term_relations.py 포코타
```

**확인 포인트**:
- [ ] 각 용어가 최소 1-2개 이상의 관계를 가지는가?
- [ ] 관계가 의미 있는가?

### 3. 웹 플랫폼 테스트

```bash
# Backend 시작
python3 -m uvicorn src.api.main:app --reload --port 8000

# Frontend 시작 (다른 터미널)
cd playbook-web
npm run dev
```

**http://localhost:3000** 접속 후 테스트:

1. "BM이 뭐야?"
2. "턴릴레이 이벤트 설명해줘"
3. "클로버는 어떻게 사용하나요?"
4. "빈칸과 고양이손의 관계는?"

**확인 포인트**:
- [ ] 관계 체인이 2-3단계 이상 형성되는가?
- [ ] 추론 과정이 명확히 표시되는가?
- [ ] 신뢰도 점수가 합리적인가?

## 롤백 계획

만약 결과가 만족스럽지 않을 경우:

### Phase 1 재실행 (다른 파라미터)

```bash
# 온도 조정 (더 창의적으로)
# src/core/processors/semantic_processor.py:444
temperature=0.3  # 기본 0.1에서 증가

# 최대 토큰 증가 (더 많은 관계 추출)
max_tokens=3000  # 기본 2000에서 증가
```

### 프롬프트 추가 조정

1. **Few-shot 예제 추가**: 프롬프트에 3-4개의 좋은 예제 추가
2. **관계 수 목표 명시**: "각 용어당 평균 2-3개의 관계 추출"
3. **패널티 명시**: "관계 없는 용어는 0점 처리"

## 다음 단계

1. ✅ Phase 1 프롬프트 개선 완료
2. ✅ Phase 1 코드 검증 강화 완료
3. ⏳ Phase 1 소규모 테스트 (100 pages)
4. ⏳ 결과 검증 및 파라미터 조정
5. ⏳ Phase 1 전체 실행 (2,246 pages)
6. ⏳ Phase 2 실행 (관계 구성)
7. ⏳ 웹 플랫폼 최종 테스트

## 기대 효과

### 정량적 목표
- 관계 수: 202 → 2,000+ (10배 증가)
- 연결률: 1.8% → 30%+ (17배 증가)
- 평균 관계/용어: 0.0 → 2.5+ (무한 증가)

### 정성적 목표
- BM, 이벤트 이름 등 핵심 용어 관계 복원
- 실용적인 GraphRAG 질의응답 가능
- 신뢰도 기반 관계 품질 관리

## 참고 문서

- [TEST_GUIDE.md](TEST_GUIDE.md) - 테스트 방법 및 쿼리 가이드
- [prompts/system_pokopoko.md](prompts/system_pokopoko.md) - 개선된 Phase 1 프롬프트
- [src/core/processors/semantic_processor.py](src/core/processors/semantic_processor.py) - Phase 1 프로세서

---

**작성일**: 2026-01-29
**개선 버전**: v2.0 (Relation-First Extraction)
