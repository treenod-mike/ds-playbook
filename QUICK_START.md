# Playbook Nexus - 빠른 시작 가이드

## 1단계: Git 설정 (필수)

```bash
# Git 사용자 정보 설정 (커밋에 표시될 이름)
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

# 설정 확인
git config --global --list
```

---

## 2단계: 환경 변수 설정 (필수)

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (nano, vi, code 등 사용)
nano .env
```

**필수 환경 변수**:
```bash
# Confluence API (문서 소스)
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your_api_token

# OpenAI API (임베딩 및 LLM)
OPENAI_API_KEY=sk-your-openai-api-key

# Supabase (데이터베이스)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
```

**Confluence API Token 발급 방법**:
1. https://id.atlassian.com/manage-profile/security/api-tokens
2. "Create API token" 클릭
3. 토큰 복사하여 `.env`에 붙여넣기

**Supabase 프로젝트 생성 방법**:
1. https://supabase.com 가입
2. "New Project" 생성
3. Settings → API에서 URL과 anon key 복사

---

## 3단계: Git 저장소 초기화

```bash
# Git 저장소 초기화
git init

# .gitignore 확인 (.env가 제외되는지 확인)
cat .gitignore | grep ".env"

# 현재 상태 확인
git status
```

---

## 4단계: 데이터베이스 마이그레이션

```bash
# Supabase SQL Editor에서 실행
# 파일: supabase/migrations/20250121_init_playbook_full.sql
# 또는 Supabase CLI 사용:
supabase db reset
```

**수동 실행**:
1. Supabase 대시보드 접속
2. SQL Editor 메뉴
3. `supabase/migrations/20250121_init_playbook_full.sql` 내용 복사
4. 실행

**결과**: 5개 테이블 + 42개 온톨로지 규칙 생성

---

## 5단계: 페이지 ID 파일 준비

```bash
# data 폴더 생성
mkdir -p data

# 페이지 ID 파일 생성
nano data/page_ids.txt
```

**형식**:
```
123456789
234567890
345678901
```

**Confluence 페이지 ID 찾는 방법**:
- 페이지 URL: `https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456789/Page+Title`
- 숫자 부분(`123456789`)이 페이지 ID

---

## 6단계: 파이프라인 실행

### 테스트 실행 (10개 페이지)

```bash
# Phase 1 + Phase 2 통합 실행
python3 run_full_pipeline.py --max-pages 10
```

**예상 소요 시간**: 5-10분 (페이지당 30초~1분)

**진행 상황**:
```
Phase 1: Semantic Extraction
├─ [1/10] Processing page 123456789...
├─ [2/10] Processing page 234567890...
└─ ...

Phase 2: Knowledge Graph Construction
├─ Processing 50 raw relations...
└─ Created 35 valid relationships
```

### 전체 실행 (모든 페이지)

```bash
# 전체 페이지 처리 (체크포인트 활용)
python3 run_full_pipeline.py --full
```

---

## 7단계: 결과 확인

### Supabase에서 확인

```sql
-- 문서 수
SELECT COUNT(*) FROM playbook_documents;

-- 청크 수
SELECT COUNT(*) FROM playbook_chunks;

-- 시맨틱 용어 수
SELECT COUNT(*) FROM playbook_semantic_terms;

-- 관계 수
SELECT COUNT(*) FROM playbook_semantic_relations;

-- 지식 그래프 샘플 조회
SELECT * FROM playbook_knowledge_graph LIMIT 10;
```

### Graph Traversal 데모

```bash
# 탐색 기능 데모
python3 scripts/demo_traversal.py
```

---

## 8단계: Git 커밋 (선택사항)

```bash
# 모든 변경사항 스테이징
git add .

# 커밋
git commit -m "Initial commit: Setup Playbook Nexus

- Configured environment variables
- Initialized database schema (v1.4)
- Added 10 pages to knowledge graph

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 원격 저장소 연결 (GitHub/GitLab)
git remote add origin https://github.com/your-username/playbook-nexus.git
git push -u origin main
```

---

## 문제 해결

### "Missing required environment variables" 오류

→ `.env` 파일이 제대로 설정되었는지 확인:
```bash
cat .env | grep "CONFLUENCE_EMAIL"
cat .env | grep "OPENAI_API_KEY"
cat .env | grep "SUPABASE_URL"
```

### "Confluence authentication failed" 오류

→ Confluence API Token 재발급:
1. https://id.atlassian.com/manage-profile/security/api-tokens
2. 기존 토큰 삭제
3. 새 토큰 생성

### "Supabase connection failed" 오류

→ Supabase 프로젝트가 활성 상태인지 확인:
```bash
curl -I $SUPABASE_URL/rest/v1/
```

### "OpenAI rate limit exceeded" 오류

→ API 요청 제한에 걸렸습니다:
- 잠시 대기 후 재실행
- `--max-pages` 옵션으로 페이지 수 줄이기
- OpenAI 계정에서 rate limit 확인

---

## 다음 단계

### Phase 1 + 2 완료 후

1. **Graph Traversal 사용**:
   ```bash
   python3 scripts/demo_traversal.py
   ```

2. **Reinforcement Learning 테스트**:
   ```bash
   python3 tests/integration/test_reinforcement.py
   ```

3. **API 개발** (향후):
   - FastAPI로 REST API 구축
   - 프론트엔드에서 지식 그래프 시각화

---

## 참고 문서

- [`docs/GIT_SETUP.md`](docs/GIT_SETUP.md) - 상세 Git 가이드
- [`docs/TRAVERSAL_DESIGN.md`](docs/TRAVERSAL_DESIGN.md) - Graph Traversal 설계
- [`README.md`](README.md) - 전체 프로젝트 문서

---

## 체크리스트

- [ ] Git 사용자 정보 설정
- [ ] `.env` 파일 생성 및 환경 변수 입력
- [ ] Git 저장소 초기화
- [ ] Supabase 마이그레이션 실행
- [ ] `data/page_ids.txt` 준비
- [ ] 테스트 실행 (`--max-pages 10`)
- [ ] 결과 확인 (Supabase 쿼리)
- [ ] Graph Traversal 데모 실행
- [ ] Git 커밋 및 푸시 (선택)

완료되면 GraphRAG 시스템이 준비됩니다! 🎉
