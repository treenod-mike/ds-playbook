"""
Chat Feature - Service Layer

채팅 비즈니스 로직
"""
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI

from src.entities.term import TermRepository, find_matching_terms
from src.entities.relation import RelationRepository
from src.core.traversal import SubgraphExtractor

logger = logging.getLogger(__name__)


class ChatService:
    """Chat 서비스 - 비즈니스 로직"""

    def __init__(
        self,
        supabase_client,
        openai_client: OpenAI,
        term_repo: TermRepository,
        relation_repo: RelationRepository,
        subgraph_extractor: SubgraphExtractor
    ):
        """
        Args:
            supabase_client: Supabase 클라이언트
            openai_client: OpenAI 클라이언트
            term_repo: 용어 레포지토리
            relation_repo: 관계 레포지토리
            subgraph_extractor: 서브그래프 추출기
        """
        self.supabase_client = supabase_client
        self.openai_client = openai_client
        self.term_repo = term_repo
        self.relation_repo = relation_repo
        self.subgraph_extractor = subgraph_extractor

    async def handle_chat(
        self,
        user_message: str,
        use_graph: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        채팅 요청 처리

        Args:
            user_message: 사용자 메시지
            use_graph: 그래프 사용 여부
            conversation_history: 대화 히스토리

        Returns:
            응답 데이터 (message, graph_data, search_process)
        """
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
            "traversal_log": []
        }

        if use_graph:
            # Step 1: Load all semantic terms and ontology rules
            search_process["steps"].append({
                "step": 1,
                "name": "데이터베이스 조회",
                "description": "Supabase에서 모든 용어와 온톨로지 룰 로드 중..."
            })

            # Load ALL terms
            terms_result = self.supabase_client.table('playbook_semantic_terms')\
                .select("id, term, category, definition")\
                .execute()

            # Load ontology rules
            rules_result = self.supabase_client.table('playbook_ontology_rules')\
                .select("subject_type, predicate, object_type, description")\
                .execute()

            search_process["steps"].append({
                "step": 2,
                "name": "데이터 로드 완료",
                "description": f"용어 {len(terms_result.data)}개, 온톨로지 룰 {len(rules_result.data)}개 로드"
            })

            # Step 3: Find relevant terms using fuzzy matching
            search_process["steps"].append({
                "step": 3,
                "name": "용어 매칭 (Fuzzy)",
                "description": "질문에서 관련 용어 추출 중 (띄어쓰기/오탈자 보정)..."
            })

            # Use fuzzy matching to find terms
            mentioned_terms = find_matching_terms(
                user_query=user_message,
                all_terms=terms_result.data,
                exact_threshold=0.85,
                fuzzy_threshold=0.65
            )

            # Update search process with found terms
            for term_data in mentioned_terms[:10]:
                search_process["found_terms"].append({
                    "term": term_data['term'],
                    "category": term_data['category']
                })

            # Log matching details
            match_details = []
            for term in mentioned_terms[:5]:
                match_type = term.get('match_type', 'unknown')
                match_conf = term.get('match_confidence', 0.0)
                match_details.append(f"{term['term']}({match_type}:{match_conf:.2f})")

            search_process["steps"].append({
                "step": 4,
                "name": "용어 매칭 완료",
                "description": f"{len(mentioned_terms)}개의 용어 발견: {', '.join(match_details)}"
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

                subgraph = self.subgraph_extractor.extract_subgraph(
                    center_term=center_term,
                    radius=2,
                    min_confidence=0.5
                )

                search_process["nodes_count"] = len(subgraph['nodes'])
                search_process["edges_count"] = len(subgraph['edges'])
                search_process["traversal_log"] = subgraph.get('traversal_log', [])

                # Check if no relations found
                if len(subgraph['edges']) == 0:
                    search_process["steps"].append({
                        "step": 6,
                        "name": "⚠️ 관계 데이터 없음",
                        "description": f"'{center_term}' 용어는 DB에 존재하지만, 연결된 관계가 0개입니다."
                    })

                    return {
                        "message": f"❌ '{center_term}' 용어는 DB에 {len(subgraph['nodes'])}개 인스턴스가 존재하지만, 연결된 관계가 없습니다.\n\n**가능한 원인:**\n- Phase 2에서 이 용어와 관련된 관계가 추출되지 않음\n- LLM이 관계를 생성했지만 온톨로지 룰 검증에서 필터링됨\n\n**해결 방법:**\n1. Phase 2 재실행\n2. 더 구체적인 용어로 검색\n3. 관계가 있는 다른 용어 시도",
                        "search_process": search_process
                    }

                search_process["steps"].append({
                    "step": 6,
                    "name": "그래프 추출 완료",
                    "description": f"노드 {len(subgraph['nodes'])}개, 관계 {len(subgraph['edges'])}개 발견"
                })

                # Transform subgraph data
                transformed_nodes = []
                for node in subgraph['nodes']:
                    transformed_nodes.append({
                        'id': node['id'],
                        'label': node['term'],
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

                # Build reasoning chain
                unique_edges = self._deduplicate_edges(subgraph['edges'], node_map)
                reasoning_chain = self._build_reasoning_chain(unique_edges)

                # Build context for LLM
                graph_context = self._build_graph_context(
                    center_term,
                    rules_result.data,
                    subgraph['nodes'],
                    unique_edges
                )

                step7_description = "온톨로지 룰과 관계 데이터를 기반으로 AI 응답 생성 중..."
                if reasoning_chain:
                    step7_description += f"\n추론 체인: {' | '.join(reasoning_chain)}"

                search_process["steps"].append({
                    "step": 7,
                    "name": "컨텍스트 생성",
                    "description": step7_description
                })

            else:
                # No terms found in DB
                search_process["steps"].append({
                    "step": 5,
                    "name": "❌ 용어를 찾을 수 없음",
                    "description": "질문에서 언급된 용어가 DB에 존재하지 않습니다."
                })

                return {
                    "message": "❌ 질문하신 용어가 DB에 존재하지 않습니다.\n\n**해결 방법:**\n1. 다른 표현으로 시도\n2. DB에 있는 용어 확인\n3. 더 많은 문서 처리",
                    "search_process": search_process
                }

        # Generate AI response
        system_prompt = self._build_system_prompt(graph_context)

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        completion = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )

        response_message = completion.choices[0].message.content

        return {
            "message": response_message,
            "graph_data": graph_data,
            "search_process": search_process
        }

    def _deduplicate_edges(
        self,
        edges: List[Dict[str, Any]],
        node_map: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """엣지 중복 제거"""
        unique_edges = {}
        for edge in edges:
            source_term = node_map.get(edge['source'], edge['source'])
            target_term = node_map.get(edge['target'], edge['target'])
            edge_key = f"{source_term}_{edge['predicate']}_{target_term}"

            if edge_key not in unique_edges or edge['confidence'] > unique_edges[edge_key]['confidence']:
                unique_edges[edge_key] = {
                    'source': source_term,
                    'predicate': edge['predicate'],
                    'target': target_term,
                    'confidence': edge['confidence'],
                    'evidence': edge.get('evidence')
                }
        return unique_edges

    def _build_reasoning_chain(self, unique_edges: Dict[str, Dict[str, Any]]) -> List[str]:
        """추론 체인 생성"""
        reasoning_chain = []
        for edge in list(unique_edges.values())[:5]:
            evidence_suffix = f" [근거: \"{edge['evidence']}\"]" if edge.get('evidence') else ""
            reasoning_chain.append(f"{edge['source']} → [{edge['predicate']}] → {edge['target']}{evidence_suffix}")
        return reasoning_chain

    def _build_graph_context(
        self,
        center_term: str,
        rules: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]],
        unique_edges: Dict[str, Dict[str, Any]]
    ) -> str:
        """그래프 컨텍스트 생성"""
        context = f"\n\n## 지식 그래프 정보\n\n"
        context += f"**중심 개념**: {center_term}\n\n"

        # Ontology rules
        context += "**온톨로지 룰** (추론에 사용 가능한 관계 타입):\n"
        for rule in rules[:15]:
            context += f"- {rule['subject_type']} --[{rule['predicate']}]--> {rule['object_type']}: {rule['description']}\n"

        # Unique nodes
        unique_nodes = {}
        for node in nodes:
            term_key = f"{node['term']}_{node['category']}"
            if term_key not in unique_nodes:
                unique_nodes[term_key] = node

        context += f"\n**관련 개념들** (중복 제거, {len(unique_nodes)}개):\n"
        for node in list(unique_nodes.values())[:15]:
            context += f"- {node['term']} ({node['category']})\n"

        # Relations
        if unique_edges:
            context += f"\n**관계** (실제 데이터에서 추출, 중복 제거, {len(unique_edges)}개):\n"
            for edge in list(unique_edges.values())[:20]:
                evidence_str = f" [근거: \"{edge['evidence']}\"]" if edge.get('evidence') else ""
                context += f"- {edge['source']} → {edge['predicate']} → {edge['target']} (신뢰도: {edge['confidence']:.2f}){evidence_str}\n"

        return context

    def _build_system_prompt(self, graph_context: str) -> str:
        """시스템 프롬프트 생성"""
        if graph_context:
            return f"""당신은 PokoPoko 게임의 지식 그래프를 분석하는 AI 어시스턴트입니다.

아래는 Supabase에서 로드한 지식 그래프 데이터입니다:

{graph_context}

**당신의 역할**:
1. **온톨로지 룰 활용**: 위 온톨로지 룰을 이해하고, 실제 관계 데이터가 어떤 룰에 해당하는지 파악
2. **관계 기반 추론**: 실제 관계 데이터를 분석해서 개념 간 의미를 추론
3. **자연스러운 설명**: 추론한 내용을 사용자가 이해하기 쉽게 풀어서 설명

**답변 방식**:
- 관계 데이터에 기반한 사실만 답변
- 근거(evidence)가 있으면 인용
- 불확실한 내용은 명시
- 이모지 사용 가능 (적절하게)
"""
        else:
            return """당신은 PokoPoko 게임에 대한 질문에 답변하는 AI 어시스턴트입니다.

지식 그래프 데이터가 없으므로 일반적인 대화로 응답하세요."""
