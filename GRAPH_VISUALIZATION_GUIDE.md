# 🌐 지식 그래프 시각화 가이드

**작성일**: 2026-01-30
**목적**: Split Screen 레이아웃에 실시간 지식 그래프 시각화 구현

---

## 📊 완성된 기능

### ✅ 구현 완료

1. **Split Screen 레이아웃** (40% Chat / 60% Graph)
2. **React Flow 기반 인터랙티브 그래프**
3. **실시간 데이터 연동** (API 응답과 동기화)
4. **다크모드 테마** 적용
5. **노드/엣지 인터랙션** (드래그, 줌, 클릭)
6. **카테고리별 색상 구분**
7. **신뢰도 기반 엣지 스타일링**
8. **범례 및 정보 패널**

---

## 🎨 UI 구조

```
┌──────────────────────────────────────────────────────────┐
│                       Header                              │
├─────────────────────┬────────────────────────────────────┤
│                     │                                     │
│   Chat Interface    │    Knowledge Graph                 │
│      (40%)          │         (60%)                      │
│                     │                                     │
│  • 메시지 리스트     │  • 노드/엣지 시각화                 │
│  • 검색 과정 로그    │  • 실시간 업데이트                 │
│  • 입력창           │  • 인터랙티브 조작                 │
│                     │  • 범례/정보 패널                  │
└─────────────────────┴────────────────────────────────────┘
```

---

## 🔧 주요 파일

### 1. **KnowledgeGraph 컴포넌트**
**위치**: `/playbook-web/components/knowledge-graph.tsx`

**기능**:
- React Flow 기반 그래프 렌더링
- 카테고리별 노드 색상 매핑
- 신뢰도 기반 엣지 애니메이션
- 노드 클릭 시 상세 정보 표시
- Background, Controls, MiniMap 제공

**Props**:
```typescript
interface KnowledgeGraphProps {
  data: GraphData | null;
  onNodeClick?: (nodeId: string, nodeData: any) => void;
}

interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    category?: string;
    group?: string;
  }>;
  edges?: Array<{
    from: string;
    to: string;
    label: string;
    confidence?: number;
  }>;
  links?: Array<{
    source: string;
    target: string;
    label: string;
    confidence?: number;
  }>;
}
```

### 2. **ChatInterface 컴포넌트 (업데이트)**
**위치**: `/playbook-web/components/chat-interface.tsx`

**변경 사항**:
- Split Screen 레이아웃으로 변경
- `currentGraphData` state 추가
- API 응답에서 `graph_data` 추출 및 저장
- KnowledgeGraph 컴포넌트 통합

---

## 🎨 카테고리별 색상

```typescript
const CATEGORY_COLORS = {
  'Content': '#22c55e',      // green-500
  'GameObject': '#3b82f6',   // blue-500
  'Currency_Soft': '#eab308', // yellow-500
  'Currency_Hard': '#ef4444', // red-500
  'Resource': '#a855f7',     // purple-500
  'Mechanic': '#f97316',     // orange-500
  'Difficulty': '#ec4899',   // pink-500
  'Metric': '#06b6d4',       // cyan-500
  'UX_Factor': '#8b5cf6',    // violet-500
  'Condition': '#64748b',    // slate-500
  'System': '#6366f1',       // indigo-500
};
```

---

## 📡 API 연동

### 요청 (Chat Endpoint)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "클로버는 어디에 쓰나요?"}],
    "use_graph": true
  }'
```

### 응답 구조
```json
{
  "message": "클로버는 다양한 콘텐츠에서 사용됩니다...",
  "graph_data": {
    "nodes": [
      {
        "id": "uuid-1",
        "label": "포코숲 리그",
        "category": "Content"
      },
      {
        "id": "uuid-2",
        "label": "클로버",
        "category": "Currency_Soft"
      }
    ],
    "edges": [
      {
        "from": "uuid-1",
        "to": "uuid-2",
        "label": "rewards",
        "confidence": 0.96
      }
    ]
  },
  "search_process": {
    "steps": [...],
    "found_terms": [...],
    "nodes_count": 5,
    "edges_count": 13
  }
}
```

---

## 🎯 주요 기능

### 1. 실시간 그래프 업데이트
- 채팅 응답마다 새로운 그래프 데이터 수신
- `currentGraphData` state를 통해 자동 업데이트
- React Flow의 `fitView`로 자동 중심 정렬

### 2. 인터랙티브 조작
```typescript
// 노드 드래그
onNodesChange={onNodesChange}

// 엣지 조작
onEdgesChange={onEdgesChange}

// 노드 클릭
onNodeClick={(event, node) => {
  setSelectedNode(node.data);
  console.log('Clicked:', node);
}}
```

### 3. 신뢰도 기반 스타일링
```typescript
// 신뢰도 0.9 이상: 녹색 + 애니메이션
animated: confidence > 0.9,
style: {
  stroke: confidence > 0.9 ? '#22c55e' : '#eab308',
}
```

### 4. 정보 패널
- **상단 좌측**: 노드/엣지 개수
- **상단 우측**: 선택된 노드 상세 정보
- **하단 우측**: 범례 (신뢰도 색상)
- **좌측 하단**: Controls (줌, 핏뷰)
- **우측 하단**: MiniMap

---

## 🚀 사용 방법

### 1. 서버 시작

**백엔드** (FastAPI):
```bash
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**프론트엔드** (Next.js):
```bash
cd playbook-web
npm run dev
```

### 2. 테스트 질문

브라우저에서 `http://localhost:3000` 접속 후:

```
✅ 추천 질문:
- "클로버는 어디에 쓰나요?"
- "포코숲 리그는 뭐야?"
- "모험 81 챕터 보상이 뭐야?"
```

### 3. 예상 결과

**좌측 (Chat)**:
```
🤖 클로버는 다양한 콘텐츠에서 소비되는 재화입니다.
리그 보상으로도 획득할 수 있어요.

🔍 검색 과정
1. 데이터베이스 조회 ✅
2. 용어 매칭 완료: 클로버 (1개)
3. 그래프 추출 완료: 노드 5개, 관계 13개
```

**우측 (Graph)**:
```
       포코숲 리그
           ↓ [rewards]
        클로버 ←───────┐
         ↓ [consumes]  │
    1차수 포코포코 미션  │
         ↓ [consumes]  │
      이벤트 스테이지───┘
```

---

## 🔧 커스터마이징

### 1. 레이아웃 변경
```typescript
// chat-interface.tsx에서 비율 조정
<Card className="w-2/5">  {/* Chat: 40% → 50% */}
<div className="w-3/5">   {/* Graph: 60% → 50% */}
```

### 2. 그래프 스타일 변경
```typescript
// knowledge-graph.tsx
<ReactFlow
  defaultEdgeOptions={{
    type: 'smoothstep',  // 'straight', 'step', 'smoothstep', 'bezier'
    animated: false,
  }}
  fitViewOptions={{
    padding: 0.2,
    minZoom: 0.5,
    maxZoom: 1.5,
  }}
/>
```

### 3. 노드 레이아웃 알고리즘 변경
```typescript
// 현재: 그리드 배치 (간단)
position: {
  x: (index % 4) * 250,
  y: Math.floor(index / 4) * 150
}

// 대안: dagre, elk 등 레이아웃 라이브러리 사용
import dagre from 'dagre';
```

---

## 📊 성능 최적화

### 1. 대용량 그래프 (100+ 노드)
```typescript
// MiniMap 비활성화
<MiniMap nodeStrokeWidth={3} zoomable pannable />

// Background 간소화
<Background gap={32} size={1} />
```

### 2. 렌더링 최적화
```typescript
// React.memo 사용
const KnowledgeGraph = React.memo(({ data, onNodeClick }) => {
  // ...
});
```

---

## 🐛 트러블슈팅

### 문제 1: 그래프가 표시되지 않음
**원인**: API가 `graph_data`를 반환하지 않음
**해결**:
```bash
# API 응답 확인
curl http://localhost:8000/api/chat | jq '.graph_data'
```

### 문제 2: 노드가 화면 밖으로 나감
**원인**: `fitView`가 작동하지 않음
**해결**:
```typescript
<ReactFlow fitView fitViewOptions={{ padding: 0.3 }} />
```

### 문제 3: 엣지 라벨이 보이지 않음
**원인**: 다크모드에서 흰색 배경
**해결**: 이미 수정됨 (labelBgStyle 적용)

---

## 📚 추가 기능 아이디어

### 1. 그래프 필터링
```typescript
// 신뢰도 슬라이더
<Slider
  min={0}
  max={1}
  step={0.1}
  value={minConfidence}
  onChange={(value) => filterEdges(value)}
/>
```

### 2. 노드 검색
```typescript
// 노드 하이라이트
<Input
  placeholder="노드 검색..."
  onChange={(e) => highlightNode(e.target.value)}
/>
```

### 3. 그래프 저장/내보내기
```typescript
// PNG 내보내기
<Button onClick={() => downloadImage()}>
  그래프 다운로드
</Button>
```

### 4. 히스토리 탐색
```typescript
// 이전 그래프로 돌아가기
const [graphHistory, setGraphHistory] = useState<GraphData[]>([]);
```

---

## 🎓 React Flow 공식 문서

**링크**: https://reactflow.dev/

**주요 섹션**:
- [Examples](https://reactflow.dev/examples) - 다양한 예제
- [API Reference](https://reactflow.dev/api-reference) - 전체 API
- [Custom Nodes](https://reactflow.dev/examples/nodes/custom-node) - 커스텀 노드
- [Layout](https://reactflow.dev/examples/layout/dagre) - 자동 레이아웃

---

## ✨ 현재 시스템 상태

```
✅ FastAPI 백엔드: http://localhost:8000
✅ Next.js 프론트엔드: http://localhost:3000
✅ Graph Visualization: React Flow v11.11.4
✅ Split Screen 레이아웃: 40% / 60%
✅ 다크모드 테마 적용
✅ 실시간 그래프 업데이트
✅ 인터랙티브 조작 가능
✅ 카테고리별 색상 구분
✅ 신뢰도 기반 스타일링
```

---

**질문이나 추가 기능 요청이 있으시면 언제든지 말씀해주세요!**
