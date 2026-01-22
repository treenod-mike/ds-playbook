# Git 설정 가이드

## 1. Git 초기 설정

### Git 사용자 정보 설정 (필수)

Git 커밋을 하려면 먼저 사용자 정보를 설정해야 합니다:

```bash
# 사용자 이름 설정
git config --global user.name "Your Name"

# 사용자 이메일 설정
git config --global user.email "your-email@example.com"

# 설정 확인
git config --global --list
```

**중요**: 이 정보는 환경 변수가 아니라 **Git 글로벌 설정**에 저장됩니다.

---

## 2. 환경 변수 설정

### .env 파일 생성

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 vi, code 등
```

### 필수 환경 변수

`.env` 파일에 다음 정보를 입력하세요:

```bash
# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your_confluence_api_token

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_key
```

---

## 3. Git 저장소 초기화

### 로컬 저장소 초기화

```bash
cd /Users/mike/Desktop/playbook_nexus

# Git 저장소 초기화 (아직 안했다면)
git init

# 현재 상태 확인
git status
```

### 원격 저장소 연결

GitHub, GitLab 등에 저장소를 만든 후:

```bash
# 원격 저장소 추가
git remote add origin https://github.com/your-username/playbook-nexus.git

# 원격 저장소 확인
git remote -v
```

---

## 4. 첫 커밋

### 파일 추가 및 커밋

```bash
# 모든 변경사항 스테이징
git add .

# 커밋 (Claude Code가 Co-Author로 자동 추가됨)
git commit -m "Initial commit: GraphRAG system with Phase 1, 2, 3

- Phase 1: Semantic Extraction (문서 처리 및 임베딩)
- Phase 2: Knowledge Graph Construction (온톨로지 기반 관계 검증)
- Phase 3: Graph Traversal (BFS, DFS, Subgraph 추출)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 원격 저장소에 푸시
git push -u origin main
```

---

## 5. .gitignore 확인

`.gitignore` 파일이 다음 항목들을 제외하는지 확인하세요:

```
✅ .env                    # 환경 변수 (비밀 정보)
✅ venv/                   # 가상환경
✅ __pycache__/            # Python 캐시
✅ logs/                   # 로그 파일
✅ data/                   # 데이터 파일
✅ *.backup                # 백업 파일
```

---

## 6. Git 워크플로우

### 일반적인 작업 흐름

```bash
# 1. 변경 사항 확인
git status

# 2. 변경된 파일 확인
git diff

# 3. 스테이징 (모든 파일)
git add .

# 또는 특정 파일만
git add src/core/traversal/graph_traversal.py

# 4. 커밋
git commit -m "Add new feature: XYZ"

# 5. 푸시
git push
```

### Claude Code와 함께 작업

Claude Code가 코드를 작성한 경우, 커밋 메시지에 Co-Author를 추가하는 것을 권장합니다:

```bash
git commit -m "Implement graph traversal feature

- BFS and DFS algorithms
- Subgraph extraction
- Comprehensive tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 7. 브랜치 전략 (선택사항)

### Feature Branch 사용

```bash
# 새 기능 브랜치 생성
git checkout -b feature/new-feature

# 작업 후 커밋
git add .
git commit -m "Implement new feature"

# main으로 돌아가기
git checkout main

# 브랜치 병합
git merge feature/new-feature

# 원격에 푸시
git push
```

---

## 8. 자주 사용하는 명령어

### 상태 확인
```bash
git status                 # 현재 상태
git log --oneline -10      # 최근 10개 커밋
git diff                   # 변경 사항
git branch                 # 브랜치 목록
```

### 되돌리기
```bash
git reset HEAD <file>      # 스테이징 취소
git checkout -- <file>     # 변경 사항 취소 (위험!)
git revert <commit>        # 커밋 되돌리기 (안전)
```

### 원격 저장소
```bash
git pull                   # 최신 변경사항 가져오기
git push                   # 로컬 커밋 푸시
git fetch                  # 원격 정보만 가져오기
```

---

## 9. 문제 해결

### "Author identity unknown" 오류

```bash
# 해결: Git 사용자 정보 설정
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

### ".env 파일이 커밋됨" (보안 위험!)

```bash
# .env 파일을 Git에서 제거 (파일은 유지)
git rm --cached .env

# .gitignore에 .env 추가 확인
echo ".env" >> .gitignore

# 커밋
git commit -m "Remove .env from tracking"
```

### Push 거부됨 (rejected)

```bash
# 원격 변경사항 먼저 가져오기
git pull --rebase

# 또는
git pull
git push
```

---

## 10. GitHub/GitLab 저장소 생성

### GitHub에서 저장소 만들기

1. https://github.com 접속
2. "New repository" 클릭
3. 저장소 이름: `playbook-nexus`
4. Private/Public 선택
5. README 추가 **안함** (이미 있음)
6. "Create repository"

### 생성된 저장소와 연결

```bash
# 원격 저장소 추가
git remote add origin https://github.com/your-username/playbook-nexus.git

# 푸시
git branch -M main
git push -u origin main
```

---

## 요약 체크리스트

- [ ] Git 사용자 정보 설정 (`git config --global`)
- [ ] `.env` 파일 생성 및 환경 변수 입력
- [ ] `.gitignore` 확인 (`.env` 제외되는지)
- [ ] Git 저장소 초기화 (`git init`)
- [ ] 원격 저장소 연결 (`git remote add`)
- [ ] 첫 커밋 및 푸시 (`git commit`, `git push`)

---

## 참고 자료

- [Git 공식 문서](https://git-scm.com/doc)
- [GitHub 가이드](https://guides.github.com/)
- [Git 브랜치 전략](https://nvie.com/posts/a-successful-git-branching-model/)
