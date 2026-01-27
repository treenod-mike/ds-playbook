"""
FastAPI application for DS-Playbook GraphRAG system
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
from openai import OpenAI

from src.core.loaders.supabase_loader import SupabaseLoader
from src.core.traversal import GraphTraversal, SubgraphExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DS-Playbook GraphRAG API",
    description="Knowledge graph exploration and analysis API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
supabase_loader = None
graph_traversal = None
subgraph_extractor = None
openai_client = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global supabase_loader, graph_traversal, subgraph_extractor, openai_client

    try:
        logger.info("Initializing Supabase connection...")
        supabase_loader = SupabaseLoader()
        graph_traversal = GraphTraversal(supabase_loader.client)
        subgraph_extractor = SubgraphExtractor(supabase_loader.client)
        logger.info("✅ Supabase connection established")

        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_base_url = os.getenv("OPENAI_BASE_URL")

        if openai_api_key:
            openai_client = OpenAI(
                api_key=openai_api_key,
                base_url=openai_base_url if openai_base_url else None
            )
            logger.info(f"✅ OpenAI initialized (base_url: {openai_base_url or 'default'})")
        else:
            logger.warning("⚠️ OPENAI_API_KEY not found - chat endpoint will be unavailable")

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


# Pydantic models
class PathResponse(BaseModel):
    nodes: List[str]
    edges: List[str]
    depth: int
    confidence: float


class ImpactAnalysisRequest(BaseModel):
    source_node: str
    max_depth: int = 3
    min_confidence: float = 0.5


class ImpactAnalysisResponse(BaseModel):
    source: str
    max_depth: int
    impact_map: Dict[int, List[str]]
    total_nodes: int


class SubgraphRequest(BaseModel):
    center_node: str
    radius: int = 2
    min_confidence: float = 0.5


class SubgraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    center: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    use_graph: bool = True


class ChatResponse(BaseModel):
    message: str
    graph_data: Optional[Dict[str, Any]] = None
    search_process: Optional[Dict[str, Any]] = None


# Endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "DS-Playbook GraphRAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "terms": "/api/terms",
            "impact_analysis": "/api/impact-analysis",
            "subgraph": "/api/subgraph",
            "shortest_path": "/api/shortest-path"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        result = supabase_loader.client.table('playbook_semantic_terms')\
            .select("id")\
            .limit(1)\
            .execute()

        return {
            "status": "healthy",
            "supabase": "connected",
            "terms_available": len(result.data) > 0
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/api/terms")
async def get_terms(limit: int = 10, category: Optional[str] = None):
    """Get semantic terms from database"""
    try:
        query = supabase_loader.client.table('playbook_semantic_terms')\
            .select("term, category, definition")

        if category:
            query = query.eq("category", category)

        result = query.limit(limit).execute()

        return {
            "terms": result.data,
            "count": len(result.data)
        }
    except Exception as e:
        logger.error(f"Error fetching terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/impact-analysis", response_model=ImpactAnalysisResponse)
async def impact_analysis(request: ImpactAnalysisRequest):
    """
    Analyze impact range using DFS traversal

    Shows how far a change in the source node can propagate through the graph.
    """
    try:
        logger.info(f"Impact analysis for: {request.source_node}")

        impact_map = graph_traversal.dfs_traversal(
            start_term=request.source_node,
            max_depth=request.max_depth,
            min_confidence=request.min_confidence
        )

        if not impact_map:
            raise HTTPException(
                status_code=404,
                detail=f"Term '{request.source_node}' not found or has no connections"
            )

        total_nodes = sum(len(terms) for terms in impact_map.values())

        return ImpactAnalysisResponse(
            source=request.source_node,
            max_depth=request.max_depth,
            impact_map=impact_map,
            total_nodes=total_nodes
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in impact analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/subgraph", response_model=SubgraphResponse)
async def get_subgraph(request: SubgraphRequest):
    """
    Extract subgraph around a center node

    Returns nodes and edges for visualization.
    """
    try:
        logger.info(f"Extracting subgraph for: {request.center_node}")

        subgraph = subgraph_extractor.extract_subgraph(
            center_term=request.center_node,
            radius=request.radius,
            min_confidence=request.min_confidence
        )

        if not subgraph['nodes']:
            raise HTTPException(
                status_code=404,
                detail=f"Term '{request.center_node}' not found"
            )

        return SubgraphResponse(
            nodes=subgraph['nodes'],
            edges=subgraph['edges'],
            center=request.center_node
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting subgraph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shortest-path")
async def shortest_path(
    start: str,
    end: str,
    max_depth: int = 5,
    min_confidence: float = 0.5
):
    """
    Find shortest path between two terms
    """
    try:
        logger.info(f"Finding path: {start} -> {end}")

        path = graph_traversal.find_shortest_path(
            start_term=start,
            end_term=end,
            max_depth=max_depth,
            min_confidence=min_confidence
        )

        if not path:
            return {
                "found": False,
                "message": f"No path found between '{start}' and '{end}' within {max_depth} hops"
            }

        return {
            "found": True,
            "path": {
                "nodes": path.nodes,
                "edges": path.edges,
                "depth": path.depth,
                "confidence": path.total_confidence
            }
        }
    except Exception as e:
        logger.error(f"Error finding shortest path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with GraphRAG-enhanced knowledge assistant

    Uses OpenAI/LiteLLM to generate natural language responses based on the knowledge graph.
    """
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="Chat service unavailable - OPENAI_API_KEY not configured"
        )

    try:
        user_message = request.messages[-1].content
        logger.info(f"Chat request: {user_message[:100]}...")

        graph_context = ""
        graph_data = None
        search_process = {
            "steps": [],
            "found_terms": [],
            "center_term": None,
            "nodes_count": 0,
            "edges_count": 0,
            "chunks_referenced": [],
            "traversal_log": []  # Add traversal log
        }

        if request.use_graph:
            # Step 1: Load all semantic terms and ontology rules
            search_process["steps"].append({
                "step": 1,
                "name": "데이터베이스 조회",
                "description": "Supabase에서 모든 용어와 온톨로지 룰 로드 중..."
            })

            # Load ALL terms (not just 100)
            terms_result = supabase_loader.client.table('playbook_semantic_terms')\
                .select("id, term, category, definition")\
                .execute()

            # Load ontology rules
            rules_result = supabase_loader.client.table('playbook_ontology_rules')\
                .select("subject_type, predicate, object_type, description")\
                .execute()

            search_process["steps"].append({
                "step": 2,
                "name": "데이터 로드 완료",
                "description": f"용어 {len(terms_result.data)}개, 온톨로지 룰 {len(rules_result.data)}개 로드"
            })

            # Step 3: Find relevant terms using semantic search
            search_process["steps"].append({
                "step": 3,
                "name": "용어 매칭",
                "description": "질문에서 관련 용어 추출 중..."
            })

            mentioned_terms = []
            seen_terms = set()  # Track unique terms
            for term_data in terms_result.data:
                if term_data['term'] in user_message:
                    term_key = f"{term_data['term']}_{term_data['category']}"
                    if term_key not in seen_terms:
                        seen_terms.add(term_key)
                        mentioned_terms.append(term_data)
                        search_process["found_terms"].append({
                            "term": term_data['term'],
                            "category": term_data['category']
                        })

            search_process["steps"].append({
                "step": 4,
                "name": "용어 매칭 완료",
                "description": f"{len(mentioned_terms)}개의 고유 용어 발견: {', '.join(list(set([t['term'] for t in mentioned_terms[:5]])))} ..."
            })

            # If terms found, get subgraph
            if mentioned_terms:
                center_term = mentioned_terms[0]['term']
                search_process["center_term"] = center_term
                logger.info(f"Found relevant term: {center_term}")

                # Step 5: Get subgraph
                search_process["steps"].append({
                    "step": 5,
                    "name": "관계 그래프 탐색",
                    "description": f"'{center_term}' 중심으로 반경 2 단계 그래프 추출 중..."
                })

                subgraph = subgraph_extractor.extract_subgraph(
                    center_term=center_term,
                    radius=2,
                    min_confidence=0.5
                )

                search_process["nodes_count"] = len(subgraph['nodes'])
                search_process["edges_count"] = len(subgraph['edges'])
                search_process["traversal_log"] = subgraph.get('traversal_log', [])

                search_process["steps"].append({
                    "step": 6,
                    "name": "그래프 추출 완료",
                    "description": f"노드 {len(subgraph['nodes'])}개, 관계 {len(subgraph['edges'])}개 발견"
                })

                # Transform subgraph data for frontend (add 'label' field)
                transformed_nodes = []
                for node in subgraph['nodes']:
                    transformed_nodes.append({
                        'id': node['id'],
                        'label': node['term'],  # term → label
                        'category': node['category']
                    })

                transformed_edges = []
                node_map = {n['id']: n['term'] for n in subgraph['nodes']}
                for edge in subgraph['edges']:
                    transformed_edges.append({
                        'from': edge['source'],
                        'to': edge['target'],
                        'label': edge['predicate'],
                        'confidence': edge['confidence']
                    })

                graph_data = {
                    'nodes': transformed_nodes,
                    'edges': transformed_edges
                }

                # Deduplicate edges first for reasoning chain
                unique_edges = {}
                for edge in subgraph['edges']:
                    source_term = node_map.get(edge['source'], edge['source'])
                    target_term = node_map.get(edge['target'], edge['target'])
                    edge_key = f"{source_term}_{edge['predicate']}_{target_term}"

                    # Keep highest confidence if duplicate
                    if edge_key not in unique_edges or edge['confidence'] > unique_edges[edge_key]['confidence']:
                        unique_edges[edge_key] = {
                            'source': source_term,
                            'predicate': edge['predicate'],
                            'target': target_term,
                            'confidence': edge['confidence']
                        }

                # Build reasoning chain for display
                reasoning_chain = []
                for edge in list(unique_edges.values())[:5]:  # Show top 5 reasoning paths
                    reasoning_chain.append(f"{edge['source']} → [{edge['predicate']}] → {edge['target']}")

                # Step 7: Building context for LLM
                step7_description = "온톨로지 룰과 관계 데이터를 기반으로 AI 응답 생성 중..."
                if reasoning_chain:
                    step7_description += f"\n추론 체인: {' | '.join(reasoning_chain)}"

                search_process["steps"].append({
                    "step": 7,
                    "name": "컨텍스트 생성",
                    "description": step7_description
                })

                # Build context for LLM with ontology rules
                graph_context = f"\n\n## 지식 그래프 정보\n\n"
                graph_context += f"**중심 개념**: {center_term}\n\n"

                # Add ontology rules context
                graph_context += "**온톨로지 룰** (추론에 사용 가능한 관계 타입):\n"
                for rule in rules_result.data[:15]:  # Show top 15 rules
                    graph_context += f"- {rule['subject_type']} --[{rule['predicate']}]--> {rule['object_type']}: {rule['description']}\n"

                # Deduplicate nodes by term name
                unique_nodes = {}
                for node in subgraph['nodes']:
                    term_key = f"{node['term']}_{node['category']}"
                    if term_key not in unique_nodes:
                        unique_nodes[term_key] = node

                graph_context += f"\n**관련 개념들** (중복 제거, {len(unique_nodes)}개):\n"
                for node in list(unique_nodes.values())[:15]:  # Show max 15 unique nodes
                    graph_context += f"- {node['term']} ({node['category']})\n"

                if unique_edges:
                    graph_context += f"\n**관계** (실제 데이터에서 추출, 중복 제거, {len(unique_edges)}개):\n"
                    for edge in list(unique_edges.values())[:20]:  # Show max 20 unique edges
                        graph_context += f"- {edge['source']} → {edge['predicate']} → {edge['target']} (신뢰도: {edge['confidence']:.2f})\n"

        # Build system prompt
        if graph_context:
            # Has graph data - use it!
            system_prompt = f"""당신은 PokoPoko 게임의 지식 그래프를 분석하는 AI 어시스턴트입니다.

아래는 Supabase에서 로드한 지식 그래프 데이터입니다:

{graph_context}

**당신의 역할**:
1. **온톨로지 룰 활용**: 위 온톨로지 룰을 이해하고, 실제 관계 데이터가 어떤 룰에 해당하는지 파악
2. **관계 기반 추론**: 실제 관계 데이터를 분석해서 개념 간 의미를 추론
3. **자연스러운 설명**: 추론한 내용을 사용자가 이해하기 쉽게 풀어서 설명

**답변 방식**:

1. **개념 설명**:
   - 질문받은 개념이 무엇인지 명확히 설명
   - 카테고리(Content/GameObject/Resource 등) 정보 활용

2. **온톨로지 기반 추론**:
   - 실제 관계 데이터를 온톨로지 룰과 매칭
   - 예: "스테이지 --[contains]--> 미션" 관계가 있다면
     - 온톨로지 룰: "content --[contains]--> content"
     - 추론: "스테이지는 여러 미션을 포함하는 상위 콘텐츠 구조"

3. **신뢰도 고려**:
   - 신뢰도가 높은(0.8 이상) 관계를 우선적으로 활용
   - 낮은 신뢰도는 "...일 가능성이 있어요" 형태로 표현

4. **맥락 제공**:
   - 게임 플레이 관점에서 설명
   - 관련 개념들을 자연스럽게 연결
   - "이것은 ...를 통해 ...하는 역할을 합니다"

5. **데이터 부족 시**:
   - 관계가 0개면 솔직하게: "현재 지식 그래프에 관계 데이터가 없어요"
   - 온톨로지 룰로 추론 가능한 내용만 간단히 언급

**중요**:
- 관계를 나열하지 말고, 의미를 추론해서 설명하세요
- 온톨로지 룰은 추론의 근거로만 사용 (직접 언급하지 않아도 됨)
- 자연스럽고 이해하기 쉬운 설명을 목표로 하세요
"""
        else:
            # No graph data
            system_prompt = """당신은 PokoPoko 게임에 대한 AI 어시스턴트입니다.

죄송하지만 현재 질문하신 내용에 대한 지식 그래프 정보가 충분하지 않네요.

다음과 같이 답변하세요:
- 짧게 사과하고
- 현재 답변 가능한 주제를 안내: "스테이지, 미션, 그룹 폭탄모으기, 여행 동호회 등에 대해서는 답변할 수 있어요!"
- 자연스럽고 친근하게
"""

        # Prepare messages for OpenAI
        openai_messages = [{"role": "system", "content": system_prompt}]
        for msg in request.messages:
            if msg.role in ["user", "assistant"]:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Call OpenAI API (or LiteLLM proxy)
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            max_tokens=1024,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content

        return ChatResponse(
            message=assistant_message,
            graph_data=graph_data,
            search_process=search_process
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
