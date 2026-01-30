# 온톨로지 시스템 업데이트 요약

**작성일**: 2026-01-30
**버전**: Phase 1 v2.0 (UX & Advanced Business Logic)

---

## 📊 변경 사항 요약

### 1. 엔티티 카테고리 확장
```
7개 → 11개 카테고리

[기존] GameObject, Resource, Mechanic, Content, Condition, System, Segment

[변경] GameObject, Currency_Hard, Currency_Soft, Mechanic, Content,
       Condition, Segment, Marketing, UX_Factor, Metric
```

**주요 변경**:
- ✅ `Resource` → `Currency_Hard` (유료) + `Currency_Soft` (무료)
- ✅ `System` → `Marketing` + `Metric` (명확한 분리)
- ✅ `UX_Factor` 신규 추가 (심리/경험 요소)

### 2. 관계 타입 확장
```
13개 → 22개 predicates

[기존] Core Gameplay (9개) + LiveOps & Business (4개)

[추가] Advanced Business Logic (5개) + UX & Psychology (4개)
```

**신규 관계 타입**:

#### Advanced Business Logic (5개)
- `accelerates`: 소모 속도 가속화 (예: 고난이도 → 클로버 소모)
- `converts_to`: 상태/가치 전환 (예: 신규 유저 → PU)
- `optimizes`: 지표/경험 최적화 (예: 튜토리얼 → 리텐션)
- `diversifies`: 경험 다양화 (예: AB테스트 → 상점 UI)
- `impacts`: 중립적 인과관계 (예: UI 변경 → 조작감)

#### UX & Psychology (4개)
- `balances`: 균형 맞춤 (예: 동적 난이도 → 유저 실력)
- `induces`: 감정 유발 (예: 고난이도 → 좌절감)
- `relieves`: 부정 경험 완화 (예: 힌트 아이템 → 막힘)
- `maintains`: 긍정 상태 유지 (예: 적절한 난이도 → 몰입)

### 3. Supabase 온톨로지 룰 확장
```
82개 → 116개 룰 (34개 추가)

[추가 분포]
- balances: 4개
- induces: 4개 (기존 1개 + 3개)
- relieves: 4개
- maintains: 4개
- optimizes: 5개
- diversifies: 5개
- impacts: 5개
- 기타 UX_Factor 역관계: 3개
```

**스크립트**: `scripts/add_ux_advanced_ontology_rules.py`

### 4. raw_relations 최적화
```
[기존] 모든 관계 무조건 저장

[변경] Confidence 기반 필터링 + Top-K 제한
```

**최적화 설정**:
```python
MIN_RELATION_CONFIDENCE = 0.7  # 70% 이상만 저장
MAX_RELATIONS_PER_TERM = 10    # 용어당 최대 10개
```

**효과**:
- 낮은 신뢰도 관계 필터링 (노이즈 제거)
- 관계 폭발 방지 (용어당 최대 10개)
- 품질과 풍부함의 균형 유지

---

## 🎯 예상 효과

### Phase 1 추출 결과

#### 카테고리 분류 정교화
```
[이전] "다이아몬드" → Resource (재화 통합)
[이후] "다이아몬드" → Currency_Hard (유료 재화)

[이전] "TV CF" → System (너무 포괄적)
[이후] "TV CF" → Marketing (마케팅 채널)

[이전] "몰입감" → 추출 불가
[이후] "몰입감" → UX_Factor (심리 요소)
```

#### 관계 추출 풍부화
```
예시 문서: "동적 난이도 시스템"

[이전 v1.0]
→ "동적 난이도" (0개 관계) ❌

[이후 v2.0]
→ "동적 난이도" (5-7개 관계) ✅
  - balances "유저 실력" (0.95)
  - diversifies "경험" (0.90)
  - relieves "좌절" (0.90)
  - relieves "지루함" (0.90)
  - maintains "몰입" (0.95)
  (+ 필터링된 낮은 신뢰도 관계 2-3개)
```

### Phase 2 검증 통과율

#### 온톨로지 룰 커버리지
```
[이전] 82개 룰
→ 신규 관계 타입 검증 실패율 높음

[이후] 116개 룰 (42% 증가)
→ 신규 관계 타입 대부분 통과 예상
```

#### 예상 통과율
```
[보수적 예측]
- raw_relations: 3-6개/용어
- Phase 2 통과: 1-2개/용어 (통과율 30-40%)

[낙관적 예측]
- raw_relations: 5-8개/용어
- Phase 2 통과: 2-4개/용어 (통과율 40-50%)
```

### 정량적 개선

```
[현재 상태]
문서: 2,246개
용어: 15,056개
관계: 202개
연결률: 1.8%
raw_relations 평균: 0.0개/용어

[예상 결과]
문서: 2,246개
용어: 8,000-10,000개 (관계 없는 용어 필터링)
관계: 3,000-6,000개
연결률: 40-60%
raw_relations 평균: 3-6개/용어

[개선율]
관계 수: 202개 → 4,500개 (약 22배)
연결률: 1.8% → 50% (약 28배)
```

---

## 🔧 구현된 최적화

### 1. Confidence Threshold
**위치**: `src/core/processors/semantic_processor.py:509-522`

```python
MIN_RELATION_CONFIDENCE = 0.7  # 70% 이상만 저장
MAX_RELATIONS_PER_TERM = 10    # 용어당 최대 10개

# Sort by confidence descending
sorted_relations = sorted(llm_relations, key=lambda x: x.get('confidence', 0), reverse=True)

raw_relations = []
for rel in sorted_relations[:MAX_RELATIONS_PER_TERM]:
    confidence = rel.get('confidence', 0.8)

    # Skip low confidence relations
    if confidence < MIN_RELATION_CONFIDENCE:
        logger.debug(f"Skipping low confidence relation...")
        continue

    # ... 저장 로직
```

**효과**:
- confidence < 0.7 관계 필터링 (약 20-30% 감소)
- 최대 10개 제한으로 관계 폭발 방지
- 높은 신뢰도 관계 우선 저장

### 2. 온톨로지 룰 검증 (Phase 2)
**위치**: Phase 2 파이프라인

- `playbook_ontology_rules` 테이블 패턴 매칭
- 116개 룰로 대부분의 신규 관계 타입 커버
- 양쪽 용어 존재 여부 검증
- 임베딩 유사도 검증

---

## 📝 실행 체크리스트

### ✅ 완료된 작업
- [x] `system_pokopoko.md` 카테고리 확장 (7→11)
- [x] `system_pokopoko.md` 관계 타입 확장 (13→18)
- [x] `system_relation_builder.md` Few-Shot 예시 추가 (Case 11)
- [x] `system_relation_builder.md` UX & Psychology 섹션 추가
- [x] Supabase 온톨로지 룰 추가 (82→116)
- [x] `semantic_processor.py` raw_relations 필터링 로직 추가

### 🔜 다음 단계

#### 1. Phase 1 재실행 (필수)
```bash
# 기존 데이터 삭제
python3 scripts/clear_phase1_data.py

# 테스트 실행 (100개 문서)
bash run_phase1_test.sh

# 결과 확인
python3 scripts/diagnose_relations.py
```

**예상 소요 시간**: 5-10분
**예상 비용**: $1-2

#### 2. 결과 검증
```bash
# 관계 통계 확인
python3 scripts/diagnose_relations.py

# 특정 용어 확인
python3 scripts/check_term_relations.py "동적 난이도"
python3 scripts/check_term_relations.py "몰입"
python3 scripts/check_term_relations.py "클로버"
```

**확인 포인트**:
- [ ] raw_relations 평균이 3.0 이상인가?
- [ ] 새로운 카테고리 (UX_Factor, Currency_Hard 등) 잘 분류되는가?
- [ ] 새로운 관계 타입 (balances, optimizes 등) 추출되는가?

#### 3. 필요시 임계값 조정
```python
# semantic_processor.py Line 509

# 관계가 너무 적으면 (평균 < 2.0)
MIN_RELATION_CONFIDENCE = 0.65  # 낮추기

# 관계가 너무 많으면 (평균 > 8.0)
MIN_RELATION_CONFIDENCE = 0.75  # 높이기

# 또는
MAX_RELATIONS_PER_TERM = 8  # 제한 강화
```

#### 4. Phase 2 실행
```bash
python3 run_phase2_only.py
```

#### 5. 웹 플랫폼 테스트
```bash
# Terminal 1: Backend
python3 -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd playbook-web
npm run dev
```

**브라우저**: http://localhost:3000

**테스트 쿼리**:
1. "동적 난이도가 뭐야?"
2. "몰입감을 유지하려면?"
3. "클로버 소모를 줄이려면?"
4. "신규 유저 전환율을 높이려면?"

---

## 🚨 주의사항

### 1. 온톨로지 룰 먼저 추가
**반드시 Phase 1 실행 전에 온톨로지 룰을 추가해야 합니다!**

```bash
# ❌ 잘못된 순서
bash run_phase1_test.sh  # Phase 1 먼저
python3 scripts/add_ux_advanced_ontology_rules.py  # 룰 나중에
→ Phase 2에서 신규 관계 타입 필터링됨!

# ✅ 올바른 순서
python3 scripts/add_ux_advanced_ontology_rules.py  # 룰 먼저
bash run_phase1_test.sh  # Phase 1 나중에
→ Phase 2에서 신규 관계 타입 정상 통과
```

### 2. 임계값 조정 시 주의
- **너무 낮은 임계값 (< 0.6)**: 노이즈 관계 증가
- **너무 높은 임계값 (> 0.8)**: 중요한 관계 누락
- **권장 범위**: 0.65 ~ 0.75

### 3. 점진적 검증
- 100개 문서로 먼저 테스트
- 결과 확인 후 전체 실행
- 문제 발생 시 즉시 롤백 가능

---

## 📚 참고 문서

- [RAW_RELATIONS_OPTIMIZATION.md](docs/RAW_RELATIONS_OPTIMIZATION.md) - raw_relations 최적화 전략 상세
- [READY_TO_RUN.md](READY_TO_RUN.md) - Phase 1 실행 가이드
- [PHASE1_IMPROVEMENTS.md](PHASE1_IMPROVEMENTS.md) - Phase 1 개선 내역

---

## 📞 문제 해결

### Q1: Phase 2에서 신규 관계 타입이 필터링되는 경우

**증상**: `balances`, `optimizes` 등이 Phase 2에서 모두 제거됨

**원인**: 온톨로지 룰 미추가

**해결**:
```bash
python3 scripts/add_ux_advanced_ontology_rules.py
python3 run_phase2_only.py  # Phase 2 재실행
```

### Q2: raw_relations 평균이 너무 낮은 경우 (< 2.0)

**증상**: 관계가 거의 추출되지 않음

**원인**: Confidence 임계값이 너무 높음

**해결**:
```python
# semantic_processor.py Line 509
MIN_RELATION_CONFIDENCE = 0.65  # 0.7 → 0.65로 낮춤
```

### Q3: raw_relations 평균이 너무 높은 경우 (> 10.0)

**증상**: 노이즈 관계가 너무 많음

**원인**: Confidence 임계값이 너무 낮음

**해결**:
```python
# semantic_processor.py Line 509
MIN_RELATION_CONFIDENCE = 0.75  # 0.7 → 0.75로 높임
MAX_RELATIONS_PER_TERM = 8     # 10 → 8로 제한 강화
```

### Q4: UX_Factor 카테고리가 추출되지 않는 경우

**증상**: "몰입", "좌절감" 등이 추출되지 않음

**원인**: 프롬프트 미반영 (캐시 문제)

**해결**:
```bash
# 데이터 삭제 후 재실행
python3 scripts/clear_phase1_data.py
bash run_phase1_test.sh
```

---

## ✅ 최종 체크리스트

### 실행 전
- [ ] 온톨로지 룰 116개 확인 (`python3 scripts/add_ux_advanced_ontology_rules.py`)
- [ ] 프롬프트 파일 업데이트 확인 (`system_pokopoko.md`, `system_relation_builder.md`)
- [ ] raw_relations 필터링 로직 확인 (`semantic_processor.py:509-522`)
- [ ] API 키 잔액 확인 (테스트 $2, 전체 $30)

### 실행 중
- [ ] Phase 1 로그 모니터링 (`tail -f logs/playbook.log`)
- [ ] 에러 발생 시 즉시 중단 (Ctrl+C)

### 실행 후
- [ ] 관계 통계 확인 (`scripts/diagnose_relations.py`)
- [ ] 새 카테고리 분포 확인
- [ ] 새 관계 타입 추출 확인
- [ ] 웹 플랫폼 쿼리 테스트

---

**준비 완료!** 🚀

다음 명령어로 시작하세요:
```bash
python3 scripts/clear_phase1_data.py
bash run_phase1_test.sh
```
