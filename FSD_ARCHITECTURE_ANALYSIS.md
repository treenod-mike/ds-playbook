# FSD 2.1 Architecture Analysis & Migration Plan

## 📋 목차
1. [현재 구조 분석](#현재-구조-분석)
2. [FSD 2.1 제안 구조](#fsd-21-제안-구조)
3. [마이그레이션 전략](#마이그레이션-전략)
4. [확장성 평가](#확장성-평가)
5. [팀 협업 가이드](#팀-협업-가이드)

---

## 현재 구조 분석

### Backend (Python - FastAPI)

```
playbook_nexus/
├── src/
│   ├── api/               # API 엔드포인트
│   │   └── main.py       # FastAPI app (500+ lines)
│   ├── core/             # 비즈니스 로직
│   │   ├── generators/   # RAG 답변 생성
│   │   ├── loaders/      # DB 로더
│   │   ├── processors/   # 온톨로지 빌더, 시맨틱 프로세서
│   │   ├── rules/        # 관계 분류 규칙
│   │   └── traversal/    # 그래프 탐색, 서브그래프 추출
│   └── shared/           # 공통 유틸리티
│       ├── config.py
│       └── utils.py
├── scripts/              # 실행 스크립트
└── tests/                # 테스트
```

**문제점**:
1. **Layer 혼재**: API와 비즈니스 로직이 main.py에 혼재 (500+ lines)
2. **Feature 미분리**: 모든 기능이 단일 파일에 집중
3. **의존성 방향 불명확**: 모듈 간 의존성 규칙 없음
4. **확장 어려움**: 새 기능 추가 시 main.py 수정 필수

### Frontend (Next.js - React)

```
playbook-web/
├── app/
│   ├── layout.tsx        # 루트 레이아웃
│   ├── page.tsx          # 메인 페이지
│   └── api/              # API 프록시
├── components/
│   ├── chat-interface.tsx    # 채팅 인터페이스 (280+ lines)
│   ├── knowledge-graph.tsx   # 그래프 시각화 (260+ lines)
│   └── ui/               # Shadcn UI 컴포넌트
└── lib/
    └── utils.ts          # 유틸리티
```

**문제점**:
1. **컴포넌트 비대화**: 단일 컴포넌트가 여러 책임 담당
2. **상태 관리 분산**: 각 컴포넌트에서 상태 관리
3. **재사용성 낮음**: UI와 비즈니스 로직 강결합
4. **타입 안정성 부족**: API 타입이 컴포넌트 내부에 정의

---

## FSD 2.1 제안 구조

### FSD 2.1 핵심 원칙

1. **Layers** (레이어): 수직 분리
   - `app/` - 앱 초기화, 프로바이더
   - `pages/` - 페이지 라우팅
   - `widgets/` - 복합 UI 블록
   - `features/` - 사용자 시나리오 (기능)
   - `entities/` - 비즈니스 엔티티
   - `shared/` - 공통 코드

2. **Slices** (슬라이스): 수평 분리
   - 각 레이어 내에서 도메인별 분리

3. **Segments** (세그먼트): 코드 목적별 분리
   - `ui/` - UI 컴포넌트
   - `model/` - 비즈니스 로직, 상태
   - `api/` - API 호출
   - `lib/` - 헬퍼 함수
   - `config/` - 설정

### Backend - Python/FastAPI 구조 제안

```
playbook_nexus/
├── src/
│   ├── app/                          # [Layer 1] 앱 초기화
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app 생성 (< 100 lines)
│   │   ├── dependencies.py           # DI 컨테이너
│   │   └── middleware.py             # CORS, logging 등
│   │
│   ├── features/                     # [Layer 2] 사용자 시나리오
│   │   ├── chat/                     # 채팅 기능
│   │   │   ├── api/
│   │   │   │   └── routes.py         # /api/chat 엔드포인트
│   │   │   ├── model/
│   │   │   │   ├── schemas.py        # Pydantic 모델
│   │   │   │   └── service.py        # 비즈니스 로직
│   │   │   └── lib/
│   │   │       └── fuzzy_matching.py # Fuzzy 매칭 유틸
│   │   │
│   │   ├── graph_traversal/          # 그래프 탐색 기능
│   │   │   ├── api/
│   │   │   │   └── routes.py         # /api/graph/* 엔드포인트
│   │   │   ├── model/
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   └── lib/
│   │   │       ├── bfs_traversal.py
│   │   │       └── subgraph_extractor.py
│   │   │
│   │   └── ontology_builder/         # 온톨로지 구축 기능
│   │       ├── model/
│   │       │   └── service.py        # Phase 2 로직
│   │       └── lib/
│   │           ├── term_matcher.py
│   │           └── relation_validator.py
│   │
│   ├── entities/                     # [Layer 3] 비즈니스 엔티티
│   │   ├── term/                     # 용어 엔티티
│   │   │   ├── model/
│   │   │   │   ├── schemas.py        # Term 모델
│   │   │   │   └── repository.py     # DB 접근
│   │   │   └── lib/
│   │   │       └── normalizer.py
│   │   │
│   │   ├── relation/                 # 관계 엔티티
│   │   │   ├── model/
│   │   │   │   ├── schemas.py        # Relation 모델
│   │   │   │   └── repository.py
│   │   │   └── lib/
│   │   │       ├── confidence.py     # 신뢰도 계산
│   │   │       └── reinforcement.py  # 강화 로직
│   │   │
│   │   └── document/                 # 문서 엔티티
│   │       └── model/
│   │           ├── schemas.py
│   │           └── repository.py
│   │
│   └── shared/                       # [Layer 4] 공통 코드
│       ├── config/
│       │   └── settings.py           # 환경 변수
│       ├── db/
│       │   └── supabase.py           # DB 클라이언트
│       ├── llm/
│       │   └── openai_client.py      # LLM 클라이언트
│       └── lib/
│           ├── logger.py
│           └── exceptions.py
│
├── scripts/                          # CLI 스크립트
│   ├── phase1_extract.py
│   ├── phase2_build.py
│   └── cli.py                        # 통합 CLI
│
└── tests/                            # 테스트
    ├── features/
    ├── entities/
    └── shared/
```

### Frontend - Next.js/React 구조 제안

```
playbook-web/
├── src/
│   ├── app/                          # [Layer 1] Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # 홈페이지
│   │   └── providers.tsx             # Context providers
│   │
│   ├── pages/                        # [Layer 2] 페이지 (없음 - App Router 사용)
│   │
│   ├── widgets/                      # [Layer 3] 복합 UI 블록
│   │   ├── chat-panel/
│   │   │   ├── ui/
│   │   │   │   ├── ChatPanel.tsx     # 메인 컴포넌트 (< 100 lines)
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   └── SearchProcess.tsx
│   │   │   ├── model/
│   │   │   │   └── useChatStore.ts   # 상태 관리 (Zustand)
│   │   │   └── lib/
│   │   │       └── formatters.ts
│   │   │
│   │   └── knowledge-graph-panel/
│   │       ├── ui/
│   │       │   ├── GraphPanel.tsx
│   │       │   ├── GraphLegend.tsx
│   │       │   └── NodeDetail.tsx
│   │       ├── model/
│   │       │   ├── useGraphStore.ts
│   │       │   └── transformers.ts   # API → ReactFlow 변환
│   │       └── lib/
│   │           ├── layout.ts         # 방사형 레이아웃 계산
│   │           └── colors.ts         # 카테고리별 색상
│   │
│   ├── features/                     # [Layer 4] 사용자 시나리오
│   │   ├── send-message/
│   │   │   ├── ui/
│   │   │   │   └── SendButton.tsx
│   │   │   └── model/
│   │   │       └── useSendMessage.ts # 메시지 전송 로직
│   │   │
│   │   ├── fuzzy-search/
│   │   │   └── lib/
│   │   │       └── fuzzyMatcher.ts
│   │   │
│   │   └── graph-interaction/
│   │       ├── ui/
│   │       │   ├── ZoomControls.tsx
│   │       │   └── NodeClickHandler.tsx
│   │       └── model/
│   │           └── useGraphInteraction.ts
│   │
│   ├── entities/                     # [Layer 5] 비즈니스 엔티티
│   │   ├── message/
│   │   │   ├── model/
│   │   │   │   ├── types.ts          # Message 타입
│   │   │   │   └── messageStore.ts
│   │   │   ├── api/
│   │   │   │   └── messageApi.ts     # API 호출
│   │   │   └── ui/
│   │   │       ├── MessageCard.tsx
│   │   │       └── MessageAvatar.tsx
│   │   │
│   │   ├── graph/
│   │   │   ├── model/
│   │   │   │   ├── types.ts          # GraphData 타입
│   │   │   │   └── graphStore.ts
│   │   │   ├── api/
│   │   │   │   └── graphApi.ts
│   │   │   └── ui/
│   │   │       ├── Node.tsx
│   │   │       └── Edge.tsx
│   │   │
│   │   └── term/
│   │       ├── model/
│   │       │   └── types.ts
│   │       └── ui/
│   │           └── TermBadge.tsx
│   │
│   └── shared/                       # [Layer 6] 공통 코드
│       ├── api/
│       │   ├── base.ts               # Axios 인스턴스
│       │   └── types.ts              # 공통 API 타입
│       ├── ui/
│       │   ├── Avatar/
│       │   ├── Button/
│       │   ├── Card/
│       │   └── ... (Shadcn UI)
│       ├── lib/
│       │   ├── utils.ts
│       │   └── cn.ts                 # Tailwind merge
│       └── config/
│           └── constants.ts
│
└── public/
    └── ...
```

---

## 마이그레이션 전략

### Phase 1: 준비 (Breaking Changes 없음)

1. **타입 정의 추출**
   ```python
   # Before: src/api/main.py (500 lines)
   class ChatRequest(BaseModel):
       messages: List[Message]
       use_graph: bool = True

   # After: src/entities/message/model/schemas.py
   class Message(BaseModel):
       role: str
       content: str

   class ChatRequest(BaseModel):
       messages: List[Message]
       use_graph: bool = True
   ```

2. **서비스 로직 분리**
   ```python
   # Before: src/api/main.py
   @app.post("/api/chat")
   async def chat(request: ChatRequest):
       # 200 lines of business logic
       ...

   # After: src/features/chat/api/routes.py
   @router.post("")
   async def chat(request: ChatRequest):
       return await ChatService().handle(request)

   # src/features/chat/model/service.py
   class ChatService:
       def __init__(self, term_repo, llm_client):
           self.term_repo = term_repo
           self.llm_client = llm_client

       async def handle(self, request):
           # Business logic
           ...
   ```

3. **Repository 패턴 도입**
   ```python
   # src/entities/term/model/repository.py
   class TermRepository:
       def __init__(self, db_client):
           self.db = db_client

       def find_all(self) -> List[Term]:
           return self.db.table('playbook_semantic_terms').select('*').execute()

       def find_by_fuzzy(self, query: str) -> List[Term]:
           # Fuzzy matching logic
           ...
   ```

### Phase 2: 점진적 마이그레이션

**우선순위**:
1. ✅ **High**: `chat` 기능 (가장 복잡)
2. ⬜ **Medium**: `graph_traversal` 기능
3. ⬜ **Low**: `ontology_builder` (CLI 스크립트로 충분)

**단계별 작업**:
```bash
# Week 1-2: Backend Chat Feature
1. src/entities/message/ 생성
2. src/entities/term/ 생성
3. src/features/chat/ 생성
4. main.py에서 chat 로직 이동
5. 테스트 작성 및 검증

# Week 3-4: Frontend Chat Widget
1. src/entities/message/ 생성
2. src/widgets/chat-panel/ 생성
3. chat-interface.tsx 분해
4. 테스트 작성 및 검증

# Week 5-6: Graph Feature
1. Backend graph_traversal 이동
2. Frontend graph-panel 위젯 생성
3. knowledge-graph.tsx 분해
```

### Phase 3: 최적화

1. **의존성 주입** (DI)
   ```python
   # src/app/dependencies.py
   def get_term_repository():
       db = get_db_client()
       return TermRepository(db)

   def get_chat_service(
       term_repo: TermRepository = Depends(get_term_repository),
       llm_client: OpenAIClient = Depends(get_llm_client)
   ):
       return ChatService(term_repo, llm_client)
   ```

2. **상태 관리** (Zustand)
   ```typescript
   // src/entities/message/model/messageStore.ts
   export const useMessageStore = create<MessageStore>((set) => ({
     messages: [],
     addMessage: (msg) => set((state) => ({
       messages: [...state.messages, msg]
     })),
   }))
   ```

---

## 확장성 평가

### ✅ 확장 가능한 시나리오

#### 1. **새 기능 추가: "관계 편집"**

**Before (현재 구조)**:
```
❌ main.py에 200+ lines 추가
❌ chat-interface.tsx에 100+ lines 추가
❌ 기존 코드 수정 필요
```

**After (FSD 구조)**:
```
✅ src/features/edit-relation/ 생성
   ├── api/routes.py           # 독립적
   ├── model/service.py
   └── lib/validator.py

✅ src/widgets/relation-editor/ 생성
   ├── ui/RelationEditor.tsx   # 독립적
   └── model/useRelationEdit.ts

✅ 기존 코드 0% 수정
✅ 다른 팀원이 동시 작업 가능
```

#### 2. **새 엔티티 추가: "청크(Chunk)"**

**Before**:
```
❌ 여러 파일에 흩어져서 수정
❌ 타입 불일치 가능성
```

**After**:
```
✅ src/entities/chunk/ 생성
   ├── model/
   │   ├── schemas.py
   │   ├── repository.py
   │   └── types.ts
   ├── api/chunkApi.ts
   └── ui/ChunkCard.tsx

✅ 단일 책임 원칙
✅ 타입 안정성 보장
```

#### 3. **새 LLM 프로바이더 추가: "Claude"**

**Before**:
```
❌ main.py 수정
❌ 조건문 추가
```

**After**:
```
✅ src/shared/llm/claude_client.py 생성
✅ LLMClient 인터페이스 구현
✅ DI 컨테이너에서 주입

# src/shared/llm/base.py
class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

# src/app/dependencies.py
def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER")
    if provider == "openai":
        return OpenAIClient()
    elif provider == "claude":
        return ClaudeClient()
```

### 🔥 확장성 지표

| 지표 | 현재 | FSD 적용 후 |
|------|------|------------|
| **새 기능 추가 시간** | 2-3일 (기존 코드 이해 필요) | 1일 (독립적 개발) |
| **코드 충돌** | 높음 (main.py 공유) | 낮음 (독립 파일) |
| **테스트 용이성** | 낮음 (강결합) | 높음 (모듈화) |
| **신규 개발자 온보딩** | 1-2주 (전체 구조 이해) | 3-5일 (레이어별 학습) |
| **코드 리뷰** | 어려움 (큰 파일) | 쉬움 (작은 파일) |

---

## 팀 협업 가이드

### 역할별 작업 영역

#### 1. **Backend Developer**
```
담당 레이어:
├── features/     # 새 기능 구현
├── entities/     # 엔티티 로직
└── shared/llm/   # LLM 통합

작업 흐름:
1. features/에 새 슬라이스 생성
2. entities/에서 필요한 엔티티 사용
3. shared/에서 공통 유틸 사용
4. 테스트 작성
5. PR 제출
```

#### 2. **Frontend Developer**
```
담당 레이어:
├── widgets/      # UI 블록 구현
├── features/     # 인터랙션 로직
└── entities/ui/  # 엔티티 UI

작업 흐름:
1. entities/에서 타입 가져오기
2. features/에 로직 구현
3. widgets/에 UI 조립
4. Storybook 작성
5. PR 제출
```

#### 3. **ML Engineer (온톨로지 빌더)**
```
담당 영역:
└── features/ontology_builder/
    ├── model/
    │   └── service.py        # Phase 2 로직
    └── lib/
        ├── term_matcher.py   # Fuzzy matching
        ├── relation_validator.py
        └── confidence_scorer.py

독립 작업 가능:
✅ src/entities/term/ 사용
✅ src/entities/relation/ 사용
✅ API 팀과 독립적
✅ CLI로 실행 가능

예시 - 새 매칭 알고리즘 추가:
1. lib/term_matcher.py 수정
2. 테스트 작성
3. PR 제출 (main.py 수정 불필요!)
```

### 협업 시나리오

#### Scenario 1: "채팅에 파일 업로드 기능 추가"

```
Backend Dev:
└── features/file_upload/
    ├── api/routes.py
    ├── model/service.py
    └── lib/parser.py

Frontend Dev:
└── features/upload-file/
    ├── ui/UploadButton.tsx
    └── model/useFileUpload.ts

Timeline:
Day 1: API 스펙 논의
Day 2-3: 병렬 개발 (충돌 없음!)
Day 4: 통합 테스트
```

#### Scenario 2: "온톨로지 빌더 개선"

```
ML Engineer (단독 작업):
└── features/ontology_builder/
    └── lib/
        ├── term_matcher.py      # 새 알고리즘
        └── semantic_similarity.py  # 추가

API 팀 영향: 0%
Frontend 팀 영향: 0%
```

### 코드 리뷰 가이드라인

1. **레이어 의존성 체크**
   ```python
   # ❌ Bad: 상위 레이어가 하위 레이어 import
   # src/entities/term/model/repository.py
   from src.features.chat.model.service import ChatService  # 금지!

   # ✅ Good: 하위 레이어가 상위 레이어 import
   # src/features/chat/model/service.py
   from src.entities.term.model.repository import TermRepository  # OK
   ```

2. **Public API 체크**
   ```python
   # 각 슬라이스의 __init__.py에서 public API 명시
   # src/entities/term/__init__.py
   from .model.schemas import Term
   from .model.repository import TermRepository

   __all__ = ['Term', 'TermRepository']
   ```

---

## 마이그레이션 체크리스트

### Week 1-2: Backend Chat Feature
- [ ] `src/entities/message/` 생성
  - [ ] `model/schemas.py` - Message, ChatRequest 타입
  - [ ] `model/repository.py` - 메시지 저장/조회 (향후)
- [ ] `src/entities/term/` 생성
  - [ ] `model/schemas.py` - Term 타입
  - [ ] `model/repository.py` - Term CRUD
- [ ] `src/features/chat/` 생성
  - [ ] `api/routes.py` - /api/chat 엔드포인트
  - [ ] `model/service.py` - ChatService 로직
  - [ ] `lib/fuzzy_matching.py` - Fuzzy 매칭 이동
- [ ] `main.py` 리팩토링
  - [ ] Chat 로직 제거
  - [ ] Router 등록만 유지
- [ ] 테스트 작성
  - [ ] `tests/features/chat/test_service.py`
  - [ ] `tests/entities/term/test_repository.py`

### Week 3-4: Frontend Chat Widget
- [ ] `src/entities/message/` 생성
  - [ ] `model/types.ts` - Message 타입
  - [ ] `model/messageStore.ts` - Zustand store
  - [ ] `api/messageApi.ts` - API 호출
  - [ ] `ui/MessageCard.tsx` - 메시지 카드
- [ ] `src/widgets/chat-panel/` 생성
  - [ ] `ui/ChatPanel.tsx` - 메인 컴포넌트
  - [ ] `ui/MessageList.tsx` - 메시지 리스트
  - [ ] `ui/MessageInput.tsx` - 입력창
  - [ ] `ui/SearchProcess.tsx` - 검색 과정 표시
  - [ ] `model/useChatStore.ts` - 상태 관리
- [ ] `chat-interface.tsx` 리팩토링
  - [ ] 로직 분해
  - [ ] ChatPanel 사용

### Week 5-6: Graph Feature
- [ ] Backend `src/features/graph_traversal/` 생성
- [ ] Frontend `src/widgets/knowledge-graph-panel/` 생성
- [ ] 테스트 작성

---

## 결론

### ✅ 확장 가능성: **매우 높음**

FSD 2.1 적용 시:
1. **모듈화**: 기능별 독립 개발
2. **확장성**: 새 기능 추가 용이
3. **협업**: 역할별 명확한 작업 영역
4. **유지보수**: 코드 위치 예측 가능

### 🎯 권장 사항

**즉시 시작 가능**:
- ✅ 새 기능은 FSD 구조로 작성
- ✅ 기존 코드는 점진적 마이그레이션

**마이그레이션 우선순위**:
1. **High**: Chat feature (복잡도 높음)
2. **Medium**: Graph traversal
3. **Low**: Ontology builder (CLI로 충분)

### 📚 참고 자료

- [FSD 2.1 공식 문서](https://feature-sliced.design/)
- [Python 버전 FSD 예제](https://github.com/feature-sliced/examples/tree/master/python-fastapi)
- [Next.js + FSD 예제](https://github.com/feature-sliced/examples/tree/master/nextjs)

---

**질문이나 피드백이 있으시면 언제든지 말씀해주세요!**
