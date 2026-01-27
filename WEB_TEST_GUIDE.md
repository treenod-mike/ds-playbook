# GraphRAG 웹 테스트 플랫폼 가이드

## 🎯 개요

PokoPoko GraphRAG 시스템의 화이트박스 테스팅을 위한 Next.js 기반 웹 인터페이스입니다.
검색 과정, BFS 탐색 로그, 추론 체인을 실시간으로 확인할 수 있습니다.

---

## 🚀 빠른 시작

### 1. 백엔드 서버 실행 (터미널 1)

```bash
cd /Users/mike/Desktop/playbook_nexus
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**확인:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     ✅ Supabase connection established
INFO:     ✅ OpenAI initialized (base_url: https://litellm.treenod.com)
```

### 2. 프론트엔드 서버 실행 (터미널 2)

```bash
cd /Users/mike/Desktop/playbook_nexus/playbook-web
npm run dev
```

**확인:**
```
✓ Ready in 2.5s
○ Local:   http://localhost:3000
```

### 3. 브라우저 접속

```
http://localhost:3000
```

---

## 📊 테스트 화면 구성

### 1. 초기 화면
- **제목:** PokoPoko GraphRAG
- **설명:** 지식 그래프 기반으로 게임 콘텐츠에 대해 질문해보세요
- **추천 질문 4개:**
  - 스테이지에 대해 설명해줘
  - 미션은 어떤 역할을 하나요?
  - 그룹 폭탄모으기는 뭐야?
  - 여행 동호회에 대해 알려줘

### 2. 검색 과정 (7단계)

질문을 입력하면 다음 7단계가 표시됩니다:

1. **데이터베이스 조회**
   - Supabase에서 모든 용어와 온톨로지 룰 로드

2. **데이터 로드 완료**
   - 용어 1000개, 온톨로지 룰 42개 로드

3. **용어 매칭**
   - 질문에서 관련 용어 추출 중

4. **용어 매칭 완료**
   - N개의 고유 용어 발견: [용어들...]

5. **관계 그래프 탐색**
   - 중심 노드로부터 반경 2 단계 그래프 추출

6. **그래프 추출 완료**
   - 노드 N개, 관계 N개 발견

7. **컨텍스트 생성** (⭐ 추론 체인 표시)
   - 보라색 박스에 추론 체인 표시
   - 예: `스테이지 → [contains] → 그룹 배틀 이벤트 | 그룹 배틀 이벤트 → [rewards] → 승리 포인트`

### 3. BFS 탐색 로그 (상세) ⭐ 새로 추가

노란색 박스에 BFS의 모든 Hop 과정이 표시됩니다:

```
🎯 시작: 스테이지 (중심 노드)
  ✅ 스테이지 → [contains] → 그룹 배틀 이벤트 (신뢰도: 0.96)
📍 Hop 1: 그룹 배틀 이벤트 방문
  ✅ 그룹 배틀 이벤트 → [rewards] → 승리 포인트 (신뢰도: 0.92)
📍 Hop 2: 승리 포인트 방문
```

**로그 기호 설명:**
- 🎯 시작: 탐색 시작점 (중심 노드)
- 📍 Hop N: 각 단계에서 방문한 노드
- ✅ 발견된 엣지 (신뢰도 포함)
- ⏭️ 필터링된 엣지 (신뢰도 부족, radius 제한 등)
- ⚠️ 관계가 없는 경우

### 4. Found Terms (용어 뱃지)

발견된 용어들이 파란색 뱃지로 표시:
- `스테이지 (Content)`
- `미션 (Content)`

---

## 🧪 테스트 시나리오

### Step 1: 질문 주입 (Query Injection)

복합 추론이 필요한 질문을 입력:

```
✅ 완료:
- "스테이지에 대해 설명해줘"
- "미션은 어떤 역할을 하나요?"
- "그룹 폭탄모으기는 뭐야?"

⚠️ 현재 하드코딩:
- radius=2 (탐색 깊이)
- min_confidence=0.5 (최소 신뢰도)
```

### Step 2: Path Tracing (경로 추적) ✅ 완료

BFS 알고리즘의 모든 단계를 실시간 추적:

**테스트 방법:**
1. 질문 입력: "스테이지에 대해 설명해줘"
2. 7단계 "컨텍스트 생성" 확인 → 추론 체인 표시
3. "BFS 탐색 로그 (상세)" 섹션 확인 → 모든 Hop 과정 표시

**확인 사항:**
- [ ] 시작 노드 표시 (🎯)
- [ ] 각 Hop에서 방문한 노드 표시 (📍)
- [ ] 발견된 엣지와 신뢰도 표시 (✅)
- [ ] 필터링된 엣지 표시 (⏭️)
- [ ] radius 제한 확인

### Step 3: Visual Verification (시각적 검증) ⚠️ 부분 완료

**완료:**
- ✅ 7단계 검색 과정 표시
- ✅ 추론 체인 시각화 (텍스트)
- ✅ Found terms 뱃지
- ✅ BFS 탐색 로그

**미완료:**
- ❌ Node → Edge → Node 카드 UI (그래프 시각화 제거됨)

### Step 4: Data Correction (데이터 교정) ❌ 미완료

Supabase 테이블 수정 기능 없음

---

## 🔍 화이트박스 테스팅 체크리스트

### 기본 동작 확인
- [ ] 백엔드 서버 정상 실행 (포트 8000)
- [ ] 프론트엔드 서버 정상 실행 (포트 3000)
- [ ] 브라우저에서 접속 가능
- [ ] 추천 질문 버튼 클릭 동작
- [ ] 직접 질문 입력 및 전송 동작

### 검색 과정 확인
- [ ] 7단계 모두 표시
- [ ] 각 단계의 description 정상 표시
- [ ] Found terms 뱃지 표시
- [ ] 추론 체인 표시 (보라색 박스)
- [ ] BFS 탐색 로그 표시 (노란색 박스)

### BFS 탐색 로그 확인
- [ ] 시작 노드 표시
- [ ] 각 Hop 표시
- [ ] 발견된 엣지와 신뢰도 표시
- [ ] 필터링된 엣지 표시 (있는 경우)
- [ ] 로그 스크롤 가능 (max-h-48)

### 관계 데이터 확인
- [ ] 온톨로지 룰 42개 로드
- [ ] 용어 1000개 로드
- [ ] 노드 개수 정확
- [ ] 엣지 개수 정확
- [ ] 신뢰도 범위 확인 (0.5 이상)

### 오류 처리
- [ ] 관계가 없는 용어 질문 시 적절한 메시지
- [ ] API 에러 시 에러 메시지 표시
- [ ] 로딩 상태 표시

---

## 🛠️ 통합 테스트 실행

### Python 통합 테스트

백엔드 API를 직접 테스트:

```bash
cd /Users/mike/Desktop/playbook_nexus
source venv/bin/activate
python tests/integration/test_chat_api_integration.py
```

**테스트 항목 (7개):**
1. Health Check
2. Response Structure
3. Search Process Steps (7단계)
4. Term Deduplication
5. Ontology Rules Loading (42개)
6. Graph Data Structure
7. Conversation History (Multi-turn)

**예상 결과:**
```
Result: 7/7 tests passed
```

### cURL 테스트

개별 API 호출 테스트:

```bash
# 헬스 체크
curl http://localhost:8000/api/health | jq '.'

# 채팅 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"스테이지에 대해 설명해줘"}],"use_graph":true}' \
  | jq '.search_process'

# BFS 탐색 로그 확인
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"스테이지에 대해 설명해줘"}],"use_graph":true}' \
  | jq '.search_process.traversal_log'
```

---

## 📝 테스트 결과 예시

### 질문: "스테이지에 대해 설명해줘"

**1. 검색 과정 (7단계):**
```
1. 데이터베이스 조회: Supabase에서 모든 용어와 온톨로지 룰 로드 중...
2. 데이터 로드 완료: 용어 1000개, 온톨로지 룰 42개 로드
3. 용어 매칭: 질문에서 관련 용어 추출 중...
4. 용어 매칭 완료: 1개의 고유 용어 발견: 스테이지 ...
5. 관계 그래프 탐색: '스테이지' 중심으로 반경 2 단계 그래프 추출 중...
6. 그래프 추출 완료: 노드 3개, 관계 2개 발견
7. 컨텍스트 생성: 온톨로지 룰과 관계 데이터를 기반으로 AI 응답 생성 중...
   추론 체인: 스테이지 → [contains] → 그룹 배틀 이벤트 | 그룹 배틀 이벤트 → [rewards] → 승리 포인트
```

**2. BFS 탐색 로그:**
```
🎯 시작: 스테이지 (중심 노드)
  ✅ 스테이지 → [contains] → 그룹 배틀 이벤트 (신뢰도: 0.96)
📍 Hop 1: 그룹 배틀 이벤트 방문
  ✅ 그룹 배틀 이벤트 → [rewards] → 승리 포인트 (신뢰도: 0.92)
📍 Hop 2: 승리 포인트 방문
```

**3. Found Terms:**
- `스테이지 (Content)`

**4. AI 응답:**
```
스테이지는 PokoPoko 게임의 핵심 콘텐츠 단위입니다.
각 스테이지는 그룹 배틀 이벤트를 포함하고 있으며,
플레이어는 이를 클리어하면 승리 포인트를 획득할 수 있습니다.
```

---

## 🔧 문제 해결

### 1. 백엔드 서버가 시작되지 않음

**증상:**
```
ImportError: No module named 'fastapi'
```

**해결:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 프론트엔드가 백엔드와 연결되지 않음

**증상:**
```
Network Error: connect ECONNREFUSED 127.0.0.1:8000
```

**해결:**
1. 백엔드 서버 실행 확인: `curl http://localhost:8000/api/health`
2. `.env` 파일 확인: `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`

### 3. BFS 탐색 로그가 표시되지 않음

**증상:** 7단계까지는 표시되지만 BFS 로그 섹션이 없음

**해결:**
1. 백엔드 코드 업데이트 확인: `src/core/traversal/subgraph_extractor.py`
2. 서버 재시작: Ctrl+C 후 다시 실행
3. 브라우저 캐시 클리어: Ctrl+Shift+R

### 4. 추론 체인이 표시되지 않음

**증상:** Step 7에 추론 체인이 없음

**해결:**
- 관계가 없는 용어를 질문한 경우: 정상 동작
- 관계가 있는데도 표시 안 됨: `src/api/main.py` 업데이트 확인

---

## 📚 관련 문서

- **백엔드 API 테스트:** [TEST_API.md](TEST_API.md)
- **프로젝트 README:** [README.md](README.md)
- **빠른 시작:** [QUICK_START.md](QUICK_START.md)

---

## 🎉 다음 단계

현재 구현된 기능:
- ✅ Step 1: 질문 주입 (기본)
- ✅ Step 2: Path Tracing (BFS 로그)
- ⚠️ Step 3: Visual Verification (부분)
- ❌ Step 4: Data Correction

향후 개선 가능 항목:
1. **파라미터 조절 UI 추가**
   - `radius` (1-5) 슬라이더
   - `min_confidence` (0.0-1.0) 슬라이더

2. **Node-Edge-Node 카드 UI 복원**
   - 그래프 시각화 추가

3. **데이터 수정 기능**
   - Supabase 테이블 직접 수정
   - 온톨로지 룰 추가/수정
   - Feedback Loop 구현

---

**작성일:** 2026-01-26
**버전:** 1.0
**작성자:** Claude Code
