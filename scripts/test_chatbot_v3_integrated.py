#!/usr/bin/env python3
"""
v3.0 GraphRAG 챗봇 (RAG Answer Generator 통합)
- test_chatbot_v2.py + rag_answer_generator.py 통합
- Evidence-based 답변 생성
- XML 구조화된 컨텍스트
- 6단계 추론 과정 시각화 유지
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.core.generators.rag_answer_generator import (
    RAGContextFormatter,
    RAGAnswerGenerator,
    SearchResult,
    GraphRelation
)
from supabase import create_client
from openai import OpenAI
from collections import defaultdict
import json

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class GraphRAGChatbotV3:
    """GraphRAG 기반 대화형 챗봇 v3.0 (RAG Generator 통합)"""

    def __init__(self):
        """초기화"""
        print(f"\n{Colors.HEADER}{'='*70}")
        print("PokoPoko v3.0 GraphRAG 챗봇 (Evidence-based Answer Generation)")
        print(f"{'='*70}{Colors.ENDC}\n")

        # Supabase 연결
        print("📡 Supabase 연결 중...")
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        print(f"{Colors.OKGREEN}✅ Supabase 연결 완료{Colors.ENDC}\n")

        # OpenAI 연결
        print("🤖 OpenAI 연결 중...")
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", None)
        )
        print(f"{Colors.OKGREEN}✅ OpenAI 연결 완료{Colors.ENDC}\n")

        # RAG 컴포넌트 초기화
        self.formatter = RAGContextFormatter()
        self.generator = RAGAnswerGenerator(self.openai_client)

        # 대화 히스토리
        self.conversation_history = []
        self.context_terms = set()  # 대화에서 언급된 용어들

        # 데이터 로드
        self._load_ontology_data()

    def _load_ontology_data(self):
        """온톨로지 데이터 로드"""
        print("📚 온톨로지 데이터 로드 중...")

        # 모든 용어 로드
        terms_result = self.supabase.table('playbook_semantic_terms')\
            .select("id, term, category, definition")\
            .execute()
        self.all_terms = terms_result.data
        self.term_map = {t['term']: t for t in self.all_terms}

        # 온톨로지 룰 로드
        rules_result = self.supabase.table('playbook_ontology_rules')\
            .select("subject_type, predicate, object_type, description")\
            .execute()
        self.ontology_rules = rules_result.data

        print(f"{Colors.OKGREEN}✅ 용어 {len(self.all_terms)}개, 온톨로지 룰 {len(self.ontology_rules)}개 로드{Colors.ENDC}\n")

    def find_related_terms(self, user_message):
        """사용자 메시지에서 관련 용어 추출"""
        mentioned_terms = []
        seen_terms = set()

        for term_data in self.all_terms:
            if term_data['term'] in user_message:
                term_key = f"{term_data['term']}_{term_data['category']}"
                if term_key not in seen_terms:
                    seen_terms.add(term_key)
                    mentioned_terms.append(term_data)
                    self.context_terms.add(term_data['term'])

        return mentioned_terms

    def get_subgraph(self, center_term, radius=2):
        """중심 용어 기반 서브그래프 추출 (hop 경로 추적)"""
        # 중심 용어의 모든 인스턴스 가져오기
        center_terms = self.supabase.table('playbook_semantic_terms')\
            .select("id, term, category")\
            .eq("term", center_term)\
            .execute()

        if not center_terms.data:
            return {
                "nodes": [],
                "edges": [],
                "reasoning_chain": [],
                "hop_paths": [],
                "traversal_log": [],
                "chunks": []
            }

        center_ids = [t['id'] for t in center_terms.data]

        # BFS로 관계 탐색 (hop 경로 추적)
        visited_nodes = {}
        visited_edges = {}
        hop_paths = []
        traversal_log = []

        queue = [(center_id, 0, [center_term]) for center_id in center_ids]
        hop_count = {0: 0, 1: 0, 2: 0}

        while queue:
            current_id, depth, path = queue.pop(0)

            if depth >= radius:
                continue

            # Outgoing edges (source) - evidence 정보 포함
            outgoing = self.supabase.table('playbook_semantic_relations')\
                .select("id, source_term_id, target_term_id, predicate, confidence, evidence, evidence_chunk_id")\
                .eq("source_term_id", current_id)\
                .gte("confidence", 0.5)\
                .execute()

            for edge in outgoing.data:
                edge_key = f"{edge['source_term_id']}_{edge['predicate']}_{edge['target_term_id']}"
                if edge_key not in visited_edges:
                    visited_edges[edge_key] = edge
                    hop_count[depth + 1] += 1

                    # Get target term name
                    target_node = self.supabase.table('playbook_semantic_terms')\
                        .select("term, category")\
                        .eq("id", edge['target_term_id'])\
                        .limit(1)\
                        .execute()

                    if target_node.data:
                        target_term = target_node.data[0]['term']
                        new_path = path + [target_term]

                        hop_paths.append({
                            "hop": depth + 1,
                            "path": " → ".join(new_path),
                            "predicate": edge['predicate'],
                            "confidence": edge['confidence']
                        })

                        queue.append((edge['target_term_id'], depth + 1, new_path))

            # Incoming edges (target) - evidence 정보 포함
            incoming = self.supabase.table('playbook_semantic_relations')\
                .select("id, source_term_id, target_term_id, predicate, confidence, evidence, evidence_chunk_id")\
                .eq("target_term_id", current_id)\
                .gte("confidence", 0.5)\
                .execute()

            for edge in incoming.data:
                edge_key = f"{edge['source_term_id']}_{edge['predicate']}_{edge['target_term_id']}"
                if edge_key not in visited_edges:
                    visited_edges[edge_key] = edge
                    hop_count[depth + 1] += 1

                    # Get source term name
                    source_node = self.supabase.table('playbook_semantic_terms')\
                        .select("term, category")\
                        .eq("id", edge['source_term_id'])\
                        .limit(1)\
                        .execute()

                    if source_node.data:
                        source_term = source_node.data[0]['term']
                        new_path = path + [source_term]

                        hop_paths.append({
                            "hop": depth + 1,
                            "path": " → ".join(new_path),
                            "predicate": edge['predicate'],
                            "confidence": edge['confidence']
                        })

                        queue.append((edge['source_term_id'], depth + 1, new_path))

        # Traversal log
        traversal_log = [
            f"Hop 0 (시작): {center_term}",
            f"Hop 1: {hop_count[1]}개 관계 발견",
            f"Hop 2: {hop_count[2]}개 관계 발견"
        ]

        # 노드 정보 가져오기
        all_node_ids = set()
        for edge in visited_edges.values():
            all_node_ids.add(edge['source_term_id'])
            all_node_ids.add(edge['target_term_id'])

        if not all_node_ids:
            return {
                "nodes": [],
                "edges": [],
                "reasoning_chain": [],
                "hop_paths": [],
                "traversal_log": traversal_log,
                "chunks": []
            }

        nodes_result = self.supabase.table('playbook_semantic_terms')\
            .select("id, term, category, source_chunks")\
            .in_("id", list(all_node_ids))\
            .execute()

        node_map = {n['id']: n for n in nodes_result.data}

        # [추가] 1. 수집된 엣지들에서 evidence_chunk_id 추출
        chunk_ids_from_evidence = set()
        for edge in visited_edges.values():
            if edge.get('evidence_chunk_id'):
                chunk_ids_from_evidence.add(edge['evidence_chunk_id'])

        # [추가] 2. 실제 청크 텍스트 조회
        evidence_map = {}
        if chunk_ids_from_evidence:
            try:
                chunks_result = self.supabase.table('playbook_chunks')\
                    .select("id, content, metadata, doc_id")\
                    .in_("id", list(chunk_ids_from_evidence))\
                    .execute()

                for c in chunks_result.data:
                    # 메타데이터에서 제목 추출 시도
                    title = c.get('metadata', {}).get('title', 'Unknown Doc') if isinstance(c.get('metadata'), dict) else 'Unknown Doc'
                    # 내용 미리보기 (100자)
                    content_preview = c['content'][:100] + "..." if len(c['content']) > 100 else c['content']
                    evidence_map[str(c['id'])] = f"[{title}] {content_preview}"
            except Exception as e:
                # 청크 조회 실패해도 계속 진행
                print(f"   ⚠️ Evidence 청크 조회 실패: {e}")

        # [수정] 3. Build reasoning chain with evidence text
        unique_edges = {}
        for edge in visited_edges.values():
            source_term = node_map.get(edge['source_term_id'], {}).get('term', '')
            target_term = node_map.get(edge['target_term_id'], {}).get('term', '')

            if source_term and target_term:
                edge_key = f"{source_term}_{edge['predicate']}_{target_term}"
                if edge_key not in unique_edges or edge['confidence'] > unique_edges[edge_key]['confidence']:
                    # Evidence 텍스트 매핑
                    evidence_text = ""
                    if edge.get('evidence'):
                        # DB에 evidence 텍스트가 있으면 사용
                        evidence_text = edge['evidence']
                    elif edge.get('evidence_chunk_id'):
                        # 청크에서 조회한 텍스트 사용
                        evidence_text = evidence_map.get(str(edge['evidence_chunk_id']), "")

                    unique_edges[edge_key] = {
                        'source': source_term,
                        'predicate': edge['predicate'],
                        'target': target_term,
                        'confidence': edge['confidence'],
                        'evidence_text': evidence_text,  # LLM에게 전달
                        'evidence_chunk_id': edge.get('evidence_chunk_id')
                    }

        reasoning_chain = [
            f"{e['source']} → [{e['predicate']}] → {e['target']} (신뢰도: {e['confidence']:.2f})"
            for e in sorted(unique_edges.values(), key=lambda x: x['confidence'], reverse=True)[:10]
        ]

        # 관련 청크 수집 (Vector Search 대신)
        chunks = []
        collected_chunk_ids = set()
        for node in nodes_result.data[:5]:  # 상위 5개 노드
            if node.get('source_chunks'):
                for chunk_id in node['source_chunks'][:2]:  # 노드당 2개 청크
                    if chunk_id not in collected_chunk_ids:
                        collected_chunk_ids.add(chunk_id)
                        chunks.append(chunk_id)

        return {
            "nodes": nodes_result.data,
            "edges": list(visited_edges.values()),
            "unique_edges": list(unique_edges.values()),
            "reasoning_chain": reasoning_chain,
            "hop_paths": sorted(hop_paths, key=lambda x: (x['hop'], -x['confidence']))[:15],
            "traversal_log": traversal_log,
            "chunks": chunks
        }

    def _convert_chunks_to_search_results(self, chunk_ids):
        """청크 ID 목록을 SearchResult 객체 리스트로 변환"""
        if not chunk_ids:
            return []

        results = []
        for chunk_id in chunk_ids[:5]:  # 최대 5개
            chunk_result = self.supabase.table('playbook_chunks')\
                .select("chunk_id, doc_id, content")\
                .eq("chunk_id", chunk_id)\
                .limit(1)\
                .execute()

            if chunk_result.data:
                chunk = chunk_result.data[0]

                # 문서 제목 가져오기
                doc_result = self.supabase.table('playbook_documents')\
                    .select("title")\
                    .eq("doc_id", chunk['doc_id'])\
                    .limit(1)\
                    .execute()

                doc_title = doc_result.data[0]['title'] if doc_result.data else "Unknown"

                results.append(SearchResult(
                    chunk_id=chunk['chunk_id'],
                    doc_id=chunk['doc_id'],
                    doc_title=doc_title,
                    content=chunk['content'],
                    similarity=0.85  # 시뮬레이션 (실제로는 임베딩 유사도)
                ))

        return results

    def _convert_edges_to_graph_relations(self, subgraph):
        """서브그래프의 edges를 GraphRelation 객체 리스트로 변환 (evidence 포함)"""
        relations = []

        # unique_edges 사용 (중복 제거된 관계)
        for edge in subgraph.get('unique_edges', [])[:10]:  # 최대 10개
            relations.append(GraphRelation(
                source=edge['source'],
                predicate=edge['predicate'],
                target=edge['target'],
                confidence=edge['confidence'],
                evidence=edge.get('evidence_text', '')  # Evidence 텍스트 포함
            ))

        return relations

    def chat(self, user_message):
        """대화 처리 (v3.0: RAG Generator 통합)"""
        print(f"\n{Colors.HEADER}{'='*70}")
        print(f"[검색 및 추론 프로세스]")
        print(f"{'='*70}{Colors.ENDC}\n")

        # 1. 관련 용어 추출
        print(f"{Colors.OKCYAN}1️⃣ 용어 매칭 단계{Colors.ENDC}")
        print(f"   사용자 질문: \"{user_message}\"")
        mentioned_terms = self.find_related_terms(user_message)

        if not mentioned_terms:
            print(f"   {Colors.WARNING}⚠️ 관련 용어를 찾을 수 없습니다.{Colors.ENDC}")
            print(f"\n{Colors.FAIL}❌ 질문하신 용어가 DB에 존재하지 않습니다.{Colors.ENDC}")
            print("다른 표현으로 시도해보세요 (예: '스테이지', '미션', '클로버' 등)\n")
            return

        print(f"   {Colors.OKGREEN}✅ {len(mentioned_terms)}개 용어 발견:{Colors.ENDC}")
        for term in mentioned_terms[:5]:
            print(f"      - {term['term']} ({term['category']})")
        print()

        # 2. 서브그래프 추출
        center_term = mentioned_terms[0]['term']
        print(f"{Colors.OKCYAN}2️⃣ 그래프 탐색 단계 (BFS){Colors.ENDC}")
        print(f"   중심 용어: {center_term}")
        print(f"   탐색 반경: 2-hop")

        subgraph = self.get_subgraph(center_term, radius=2)

        # Traversal log 출력
        print(f"\n   {Colors.HEADER}[그래프 탐색 경로]{Colors.ENDC}")
        for log in subgraph['traversal_log']:
            print(f"   {log}")

        print(f"\n   {Colors.OKGREEN}✅ 총 노드 {len(subgraph['nodes'])}개, 관계 {len(subgraph['edges'])}개 발견{Colors.ENDC}\n")

        if len(subgraph['edges']) == 0:
            print(f"   {Colors.WARNING}⚠️ '{center_term}' 용어는 존재하지만 연결된 관계가 없습니다.{Colors.ENDC}")
            print("   Phase 2를 재실행하거나 다른 용어를 시도해보세요.\n")
            return

        # 3. Hop 경로 시각화
        print(f"{Colors.OKCYAN}3️⃣ Hop 경로 분석{Colors.ENDC}")

        hop1_paths = [p for p in subgraph['hop_paths'] if p['hop'] == 1]
        hop2_paths = [p for p in subgraph['hop_paths'] if p['hop'] == 2]

        if hop1_paths:
            print(f"\n   {Colors.HEADER}[Hop 1 경로] (1단계 관계, {len(hop1_paths)}개){Colors.ENDC}")
            for i, path_info in enumerate(hop1_paths[:5], 1):
                print(f"   {i}. {path_info['path']}")
                print(f"      └─ Predicate: {path_info['predicate']} (신뢰도: {path_info['confidence']:.2f})")

        if hop2_paths:
            print(f"\n   {Colors.HEADER}[Hop 2 경로] (2단계 관계, {len(hop2_paths)}개){Colors.ENDC}")
            for i, path_info in enumerate(hop2_paths[:5], 1):
                print(f"   {i}. {path_info['path']}")
                print(f"      └─ Predicate: {path_info['predicate']} (신뢰도: {path_info['confidence']:.2f})")

        # 4. 추론 체인 (온톨로지 기반)
        print(f"\n{Colors.OKCYAN}4️⃣ 온톨로지 기반 추론 체인{Colors.ENDC}")
        if subgraph['reasoning_chain']:
            print(f"   {Colors.HEADER}[Top 5 추론 경로]{Colors.ENDC}")
            for i, chain in enumerate(subgraph['reasoning_chain'][:5], 1):
                print(f"   {i}. {chain}")
        print()

        # 5. 컨텍스트 생성 (RAG Formatter 사용)
        print(f"{Colors.OKCYAN}5️⃣ RAG 컨텍스트 생성 (XML 구조){Colors.ENDC}")

        # 청크 수집
        vector_results = self._convert_chunks_to_search_results(subgraph['chunks'])

        # 그래프 관계 변환
        graph_relations = self._convert_edges_to_graph_relations(subgraph)

        context_stats = {
            "대화 맥락 용어": len(self.context_terms),
            "온톨로지 룰": len(self.ontology_rules),
            "청크 수": len(vector_results),
            "그래프 관계": len(graph_relations)
        }

        print(f"   {Colors.OKGREEN}✅ 컨텍스트 요소:{Colors.ENDC}")
        for key, value in context_stats.items():
            print(f"      - {key}: {value}개")
        print()

        # 6. 답변 생성 (RAG Generator 사용)
        print(f"{Colors.OKCYAN}6️⃣ GPT-4 답변 생성 (Evidence-based){Colors.ENDC}")
        print(f"   모델: gpt-4o")
        print(f"   온톨로지 룰 기반 추론 활성화")
        print(f"   Temperature: 0.3 (보수적 생성)")
        print(f"   대화 히스토리: {len(self.conversation_history) // 2}턴 유지\n")

        result = self.generator.generate_answer(
            query=user_message,
            vector_results=vector_results,
            graph_relations=graph_relations,
            ontology_rules=self.ontology_rules,
            center_term=center_term,
            temperature=0.3
        )

        if not result["success"]:
            print(f"{Colors.FAIL}❌ 답변 생성 실패: {result['error']}{Colors.ENDC}\n")
            return

        assistant_message = result["answer"]

        # 대화 히스토리 업데이트
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})

        # 7. 최종 답변 및 근거
        print(f"{Colors.HEADER}{'='*70}")
        print(f"[최종 답변 및 근거]")
        print(f"{'='*70}{Colors.ENDC}\n")

        print(f"{Colors.BOLD}[AI 어시스턴트]{Colors.ENDC}\n")
        print(assistant_message)

        print(f"\n{Colors.HEADER}[답변 근거]{Colors.ENDC}")
        metadata = result["metadata"]
        print(f"  - 사용된 청크: {metadata['num_chunks']}개")
        print(f"  - 사용된 관계: {metadata['num_relations']}개")
        print(f"  - 탐색 깊이: 2-hop")
        print(f"  - 사용 토큰: {metadata['tokens_used']}")
        print(f"  - 대화 컨텍스트: {', '.join(list(self.context_terms)[-3:])}" if len(self.context_terms) > 1 else "  - 대화 컨텍스트: 없음")

        print(f"\n{Colors.BOLD}{'━'*70}{Colors.ENDC}\n")

    def run(self):
        """대화형 루프 실행"""
        print(f"{Colors.HEADER}💬 대화를 시작합니다. 종료하려면 'exit' 또는 'quit'를 입력하세요.{Colors.ENDC}\n")

        # 환영 메시지
        print(f"{Colors.OKGREEN}안녕하세요! PokoPoko 게임의 지식 그래프 어시스턴트입니다.{Colors.ENDC}")
        print(f"{Colors.OKGREEN}게임 메카닉, 이벤트, UX, 비즈니스 로직에 대해 물어보세요!{Colors.ENDC}")
        print(f"{Colors.WARNING}v3.0: Evidence-based 답변 생성 + XML 구조화된 컨텍스트{Colors.ENDC}\n")

        while True:
            try:
                # 사용자 입력
                user_input = input(f"{Colors.OKCYAN}You: {Colors.ENDC}").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', '종료']:
                    print(f"\n{Colors.OKGREEN}대화를 종료합니다. 감사합니다!{Colors.ENDC}\n")
                    break

                # 특수 명령어
                if user_input.lower() == 'history':
                    print(f"\n{Colors.HEADER}[대화 히스토리]{Colors.ENDC}")
                    for i, msg in enumerate(self.conversation_history, 1):
                        role = "사용자" if msg['role'] == 'user' else "AI"
                        print(f"{i}. [{role}] {msg['content'][:50]}...")
                    print()
                    continue

                if user_input.lower() == 'context':
                    print(f"\n{Colors.HEADER}[대화 컨텍스트 용어]{Colors.ENDC}")
                    print(f"{', '.join(self.context_terms)}\n")
                    continue

                # 대화 처리
                self.chat(user_input)

            except KeyboardInterrupt:
                print(f"\n\n{Colors.OKGREEN}대화를 종료합니다. 감사합니다!{Colors.ENDC}\n")
                break
            except Exception as e:
                print(f"\n{Colors.FAIL}❌ 오류 발생: {e}{Colors.ENDC}\n")


def main():
    """메인 함수"""
    chatbot = GraphRAGChatbotV3()
    chatbot.run()


if __name__ == "__main__":
    main()
