# Project Playbook Web

시맨틱 웹과 그래프 DAG 구조를 테스트하기 위한 웹 인터페이스입니다.

## 빠른 시작

### 1. 백엔드 실행
```bash
cd /Users/mike/Desktop/playbook_nexus
python3 -m uvicorn src.api.main:app --reload
```

### 2. 프론트엔드 실행
```bash
cd playbook-web
npm install
npm run dev
```

### 3. 접속
http://localhost:3000

## 테스트 쿼리 예시

- "스테이지의 영향 범위 분석해줘"
- "체리와 관련된 노드를 보여줘"
- "승리 포인트와 연결된 관계를 찾아줘"

그래프 시각화를 통해 시맨틱 관계를 확인할 수 있습니다.

## 기술 스택

- Next.js + React (프론트엔드)
- FastAPI (백엔드)
- ReactFlow (그래프 시각화)
- shadcn/ui (UI 컴포넌트)
