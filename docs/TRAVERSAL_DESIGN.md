# Graph Traversal 설계 문서

## 개요

Playbook Nexus GraphRAG 시스템의 지식 그래프 탐색(Knowledge Graph Traversal) 기능 설계 문서입니다.

**작성일**: 2025-01-22
**버전**: v1.0

---

## 목적

현재 시스템은 지식 그래프를 **구축**하는 기능(Phase 1 + Phase 2)만 제공합니다.
Traversal 기능을 추가하여 구축된 그래프를 **활용**할 수 있도록 합니다.

### 주요 사용 사례

1. **경로 탐색**: "A에서 B로 가는 최단 경로는?"
2. **영향 분석**: "난이도 상향이 최종적으로 어디까지 영향을 주는가?"
3. **관계 추론**: "두 개념 사이의 연결고리는?"
4. **서브그래프 추출**: "특정 메카닉과 관련된 모든 것"

---

## 현재 시스템 구조

### DB 스키마 (v1.4)

```sql
-- 지식 그래프 핵심 테이블
playbook_semantic_relations (
    id UUID PRIMARY KEY,
    source_term_id UUID NOT NULL,      -- 출발 노드
    target_term_id UUID NOT NULL,      -- 도착 노드
    predicate TEXT NOT NULL,            -- 관계 타입 (triggers, clears, ...)
    confidence FLOAT DEFAULT 1.0,       -- 신뢰도
    evidence TEXT,                      -- 근거 텍스트
    occurrence_count INT DEFAULT 1,     -- RL: 관찰 횟수
    last_verified_at TIMESTAMP,         -- RL: 마지막 검증 시각
)
```

### 인덱스 현황

```sql
✅ idx_playbook_rel_source (source_term_id)
✅ idx_playbook_rel_target (target_term_id)
✅ idx_playbook_rel_predicate (predicate)
✅ idx_playbook_rel_source_pred (source_term_id, predicate)
✅ idx_playbook_rel_target_pred (target_term_id, predicate)
```

**평가**: Traversal에 필요한 인덱스가 모두 준비되어 있음 ✅

---

## 구현 우선순위

### Phase A: 우선 구현 (현재 진행)

**목표**: 기본적인 그래프 탐색 및 시각화 지원

1. **BFS (너비 우선 탐색)** - 최단 경로 찾기
   - 사용 사례: "더블폭탄이 어떤 자원 획득으로 이어지는가?"
   - 알고리즘: 너비 우선 탐색 (Breadth-First Search)
   - 복잡도: O(V + E)

2. **Subgraph 추출** - 특정 노드 주변 서브그래프
   - 사용 사례: "특정 메카닉과 관련된 모든 것을 보여줘"
   - 알고리즘: 반경 기반 BFS
   - 복잡도: O(r * E) where r = radius

### Phase B: 다음 단계 (분석 고도화)

3. **DFS (깊이 우선 탐색)** - 영향 범위 분석
4. **양방향 탐색** - 관계 추론 최적화
5. **PostgreSQL Recursive CTE** - DB 레벨 탐색 (성능 비교)

### Phase C: 고급 기능 (향후)

6. **PageRank** - 노드 중요도 계산
7. **Community Detection** - 클러스터링
8. **Path Ranking** - 경로 중요도 평가

---

## Phase A 상세 설계

### 1. BFS Traversal

#### 입력 파라미터

```python
def bfs_traversal(
    start_term: str,                    # 시작 용어 (예: "더블폭탄")
    target_category: Optional[str],     # 목표 카테고리 (예: "resource")
    max_depth: int = 5,                 # 최대 탐색 깊이
    min_confidence: float = 0.5         # 최소 신뢰도 필터
) -> List[TraversalPath]
```

#### 반환 데이터 구조

```python
@dataclass
class TraversalPath:
    nodes: List[str]           # ['더블폭탄', '블록', '스테이지클리어', '체리']
    edges: List[str]           # ['clears', 'enables', 'rewards']
    depth: int                 # 3
    total_confidence: float    # 0.85 (경로상 모든 edge 신뢰도의 곱)
```

#### 알고리즘 흐름

```
1. 시작 노드 ID 조회 (playbook_semantic_terms)
2. BFS 큐 초기화: [(start_id, [start_term], [], 0, 1.0)]
3. While 큐가 비지 않음:
   a. 현재 노드 dequeue
   b. 깊이 제한 체크
   c. 현재 노드에서 나가는 엣지 조회 (source_term_id 인덱스 사용)
   d. 각 엣지에 대해:
      - 신뢰도 필터링 (>= min_confidence)
      - 방문 체크 (순환 방지)
      - 목표 카테고리 도달 시 경로 저장
      - 큐에 추가
4. 경로 리스트를 신뢰도 순으로 정렬하여 반환
```

#### 성능 고려사항

- **인덱스 활용**: `idx_playbook_rel_source_pred` 사용으로 O(1) 엣지 조회
- **Early Termination**: 목표 카테고리 발견 시 해당 깊이만 완료 후 종료
- **메모리 제한**: max_depth로 탐색 공간 제한

### 2. Subgraph 추출

#### 입력 파라미터

```python
def extract_subgraph(
    center_term: str,                   # 중심 용어
    radius: int = 2,                    # 탐색 반경
    predicates: Optional[List[str]] = None  # 포함할 관계 타입 (None=전체)
) -> Dict
```

#### 반환 데이터 구조

```python
{
    'nodes': [
        {'id': 'uuid-1', 'term': '더블폭탄', 'category': 'gameobject'},
        {'id': 'uuid-2', 'term': '블록', 'category': 'gameobject'},
        ...
    ],
    'edges': [
        {
            'source': 'uuid-1',
            'target': 'uuid-2',
            'predicate': 'clears',
            'confidence': 0.95
        },
        ...
    ]
}
```

**용도**: 프론트엔드 시각화 라이브러리(D3.js, Cytoscape.js)에 직접 사용 가능

#### 알고리즘 흐름

```
1. 중심 노드 ID 조회
2. BFS로 반경 내 모든 노드 수집
3. 수집된 노드 간의 모든 엣지 조회
4. 노드 + 엣지를 JSON 형태로 반환
```

---

## 데이터베이스 지원

### PostgreSQL Recursive CTE 함수

Python 구현 외에 DB 레벨 탐색도 지원합니다:

```sql
CREATE OR REPLACE FUNCTION traverse_graph(
    start_term_name TEXT,
    max_depth INT DEFAULT 5,
    min_confidence FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    path TEXT[],
    relationships TEXT[],
    depth INT,
    final_term TEXT,
    final_category TEXT
)
```

**장점**:
- 네트워크 오버헤드 감소
- PostgreSQL 쿼리 최적화 활용
- 대규모 그래프에서 성능 우수

**단점**:
- 복잡한 로직 구현 어려움
- 디버깅 복잡

**전략**: Python 구현을 우선하고, 성능 이슈 발생 시 SQL로 포팅

---

## 기존 시스템과의 통합

### 파일 구조

```
src/
├── core/
│   ├── processors/          # 기존
│   │   ├── confluence_processor.py
│   │   ├── semantic_processor.py
│   │   └── ontology_builder.py
│   ├── loaders/             # 기존
│   │   └── supabase_loader.py
│   ├── rules/               # 기존
│   │   └── ontology_rules.py
│   └── traversal/           # 🆕 추가
│       ├── __init__.py
│       ├── graph_traversal.py      # BFS, DFS, 양방향 탐색
│       └── subgraph_extractor.py   # Subgraph 추출
└── shared/                  # 기존
    ├── config.py
    └── utils.py
```

### Import 경로

```python
# 새로운 Traversal 기능
from src.core.traversal.graph_traversal import GraphTraversal
from src.core.traversal.subgraph_extractor import SubgraphExtractor

# 기존 기능과 함께 사용
from src.core.loaders.supabase_loader import SupabaseLoader

# 사용 예시
supabase = SupabaseLoader()
traversal = GraphTraversal(supabase.client)
paths = traversal.bfs_traversal("더블폭탄", "resource")
```

### 의존성 확인

- ✅ **SupabaseLoader**: 기존 클래스 재사용
- ✅ **Config**: 기존 설정 재사용 (SUPABASE_URL, SUPABASE_KEY)
- ✅ **테이블명 상수**: Config에서 가져오기
- ⚠️ **새 의존성 없음**: 순수 Python + 기존 supabase-py

---

## 테스트 계획

### 단위 테스트

```python
# tests/unit/test_traversal.py
def test_bfs_single_hop():
    """1단계 관계 찾기"""
    paths = traversal.bfs_traversal("A", max_depth=1)
    assert len(paths) > 0
    assert paths[0].depth == 1

def test_bfs_with_confidence_filter():
    """신뢰도 필터링"""
    paths = traversal.bfs_traversal("A", min_confidence=0.8)
    for path in paths:
        assert path.total_confidence >= 0.8
```

### 통합 테스트

```python
# tests/integration/test_traversal_integration.py
def test_real_graph_traversal():
    """실제 DB 데이터로 탐색"""
    # 실제 존재하는 용어로 테스트
    paths = traversal.bfs_traversal(
        start_term="실제용어",
        target_category="resource",
        max_depth=3
    )
    assert len(paths) > 0
```

---

## 예상 사용 시나리오

### 시나리오 1: 게임 기획 분석

**질문**: "더블폭탄이 최종적으로 어떤 재화 획득으로 이어지는가?"

```python
traversal = GraphTraversal(supabase.client)
paths = traversal.bfs_traversal(
    start_term="더블폭탄",
    target_category="resource",
    max_depth=4,
    min_confidence=0.7
)

for i, path in enumerate(paths[:3], 1):
    print(f"\n{i}. 경로 (신뢰도: {path.total_confidence:.2f})")
    print("   " + " -> ".join(path.nodes))
    print("   관계: " + " -> ".join(path.edges))
```

**출력**:
```
1. 경로 (신뢰도: 0.85)
   더블폭탄 -> 블록 -> 스테이지클리어 -> 체리
   관계: clears -> enables -> rewards

2. 경로 (신뢰도: 0.72)
   더블폭탄 -> 특수블록 -> 보너스 -> 다이아
   관계: clears -> triggers -> rewards
```

### 시나리오 2: 시각화 준비

**질문**: "특정 메카닉 주변 생태계 보기"

```python
extractor = SubgraphExtractor(supabase.client)
subgraph = extractor.extract_subgraph(
    center_term="4매치",
    radius=2,
    predicates=["triggers", "clears", "synergizes_with"]
)

# 프론트엔드로 전달
return JSONResponse(subgraph)
```

**프론트엔드에서**:
```javascript
// D3.js로 시각화
const graph = await fetch('/api/subgraph?term=4매치&radius=2');
renderGraph(graph.nodes, graph.edges);
```

---

## 성능 최적화 전략

### 1단계: 인덱스 활용 (이미 준비됨)
- ✅ `idx_playbook_rel_source_pred` 사용

### 2단계: 캐싱 (향후)
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _get_term_id(self, term: str) -> Optional[str]:
    """용어 ID 조회 결과 캐싱"""
    ...
```

### 3단계: 배치 쿼리 (대규모 그래프)
```python
# 여러 노드의 엣지를 한 번에 조회
edge_ids = [id1, id2, id3, ...]
edges = supabase.table('relations')\
    .select('*')\
    .in_('source_term_id', edge_ids)\
    .execute()
```

---

## 변경 이력

- **v1.0 (2025-01-22)**: 초안 작성
  - BFS, Subgraph 추출 설계
  - 구현 우선순위 정의
  - 기존 시스템과의 통합 계획

---

## 참고 자료

- [NetworkX Documentation](https://networkx.org/documentation/stable/reference/algorithms/traversal.html)
- [PostgreSQL Recursive Queries](https://www.postgresql.org/docs/current/queries-with.html)
- [Graph Algorithms (Neo4j)](https://neo4j.com/docs/graph-data-science/current/algorithms/)
