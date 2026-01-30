#!/usr/bin/env python3
"""
v2.0 GraphRAG 챗봇 테스트 스크립트
- 웹 플랫폼과 동일한 구조
- 대화 컨텍스트 유지
- 관계 그래프 기반 답변 생성
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
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

class GraphRAGChatbot:
    """GraphRAG 기반 대화형 챗봇"""

    def __init__(self):
        """초기화"""
        print(f"\n{Colors.HEADER}{'='*70}")
        print("PokoPoko v2.0 GraphRAG 챗봇 테스트")
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

        # 대화 히스토리
        self.conversation_history = []
        self.context_terms = set()  # 대화에서 언급된 용어들
        self.context_graph = {"nodes": [], "edges": []}  # 누적 그래프

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
                "traversal_log": []
            }

        center_ids = [t['id'] for t in center_terms.data]

        # BFS로 관계 탐색 (hop 경로 추적)
        visited_nodes = {}
        visited_edges = {}
        hop_paths = []  # 각 hop 경로 저장
        traversal_log = []  # 탐색 로그

        queue = [(center_id, 0, [center_term]) for center_id in center_ids]  # (id, depth, path)

        hop_count = {0: 0, 1: 0, 2: 0}

        while queue:
            current_id, depth, path = queue.pop(0)

            if depth >= radius:
                continue

            # Outgoing edges (source)
            outgoing = self.supabase.table('playbook_semantic_relations')\
                .select("id, source_term_id, target_term_id, predicate, confidence")\
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

                        # Record hop path
                        hop_paths.append({
                            "hop": depth + 1,
                            "path": " → ".join(new_path),
                            "predicate": edge['predicate'],
                            "confidence": edge['confidence']
                        })

                        queue.append((edge['target_term_id'], depth + 1, new_path))

            # Incoming edges (target)
            incoming = self.supabase.table('playbook_semantic_relations')\
                .select("id, source_term_id, target_term_id, predicate, confidence")\
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

                        # Record hop path
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
                "traversal_log": traversal_log
            }

        nodes_result = self.supabase.table('playbook_semantic_terms')\
            .select("id, term, category")\
            .in_("id", list(all_node_ids))\
            .execute()

        node_map = {n['id']: n for n in nodes_result.data}

        # Build reasoning chain
        unique_edges = {}
        for edge in visited_edges.values():
            source_term = node_map.get(edge['source_term_id'], {}).get('term', '')
            target_term = node_map.get(edge['target_term_id'], {}).get('term', '')

            if source_term and target_term:
                edge_key = f"{source_term}_{edge['predicate']}_{target_term}"
                if edge_key not in unique_edges or edge['confidence'] > unique_edges[edge_key]['confidence']:
                    unique_edges[edge_key] = {
                        'source': source_term,
                        'predicate': edge['predicate'],
                        'target': target_term,
                        'confidence': edge['confidence']
                    }

        reasoning_chain = [
            f"{e['source']} → [{e['predicate']}] → {e['target']} (신뢰도: {e['confidence']:.2f})"
            for e in sorted(unique_edges.values(), key=lambda x: x['confidence'], reverse=True)[:10]
        ]

        return {
            "nodes": nodes_result.data,
            "edges": list(visited_edges.values()),
            "unique_edges": list(unique_edges.values()),
            "reasoning_chain": reasoning_chain,
            "hop_paths": sorted(hop_paths, key=lambda x: (x['hop'], -x['confidence']))[:15],  # Top 15 paths
            "traversal_log": traversal_log
        }

    def build_graph_context(self, mentioned_terms, subgraph):
        """그래프 기반 컨텍스트 생성"""
        if not mentioned_terms:
            return ""

        center_term = mentioned_terms[0]['term']

        context = f"\n\n## 🎯 지식 그래프 정보\n\n"
        context += f"**중심 개념**: {center_term}\n\n"

        # 1. 대화 컨텍스트 (이전에 언급된 용어들)
        if len(self.context_terms) > 1:
            context += f"**대화 맥락** (이전 언급 용어):\n"
            for term in list(self.context_terms)[-5:]:  # 최근 5개
                if term in self.term_map:
                    t = self.term_map[term]
                    context += f"- {term} ({t['category']})\n"
            context += "\n"

        # 2. 온톨로지 룰 (샘플)
        context += "**온톨로지 룰** (추론 가능한 관계 타입):\n"
        for rule in self.ontology_rules[:15]:
            context += f"- {rule['subject_type']} --[{rule['predicate']}]--> {rule['object_type']}: {rule['description']}\n"

        # 3. 관련 개념들
        unique_nodes = {}
        for node in subgraph['nodes']:
            term_key = f"{node['term']}_{node['category']}"
            if term_key not in unique_nodes:
                unique_nodes[term_key] = node

        context += f"\n**관련 개념들** (중복 제거, {len(unique_nodes)}개):\n"
        for node in list(unique_nodes.values())[:15]:
            context += f"- {node['term']} ({node['category']})\n"

        # 4. 실제 관계
        if subgraph['unique_edges']:
            context += f"\n**관계** (실제 데이터, 중복 제거, {len(subgraph['unique_edges'])}개):\n"
            for edge in subgraph['unique_edges'][:20]:
                context += f"- {edge['source']} → {edge['predicate']} → {edge['target']} (신뢰도: {edge['confidence']:.2f})\n"

        # 5. 추론 체인 (가독성 높은 형태)
        if subgraph['reasoning_chain']:
            context += f"\n**추론 체인** (Top 5):\n"
            for chain in subgraph['reasoning_chain'][:5]:
                context += f"  {chain}\n"

        return context

    def generate_system_prompt(self, graph_context):
        """시스템 프롬프트 생성"""
        if graph_context:
            return f"""당신은 PokoPoko 게임의 지식 그래프를 분석하는 AI 어시스턴트입니다.

아래는 Supabase에서 로드한 지식 그래프 데이터입니다:

{graph_context}

**당신의 역할**:

1. **대화 맥락 유지**:
   - 이전 대화에서 언급된 용어들을 기억하고 연결
   - 사용자가 "그럼", "그거", "그것" 등 지시어를 사용하면 대화 맥락에서 추론
   - 자연스러운 대화 흐름 유지

2. **온톨로지 기반 추론**:
   - 실제 관계 데이터를 온톨로지 룰과 매칭하여 의미 파악
   - 예: "동적 난이도 --[balances]--> 유저 실력"
     → "동적 난이도는 유저 실력에 맞춰 균형을 맞춥니다"

3. **관계 체인 활용**:
   - 여러 관계를 연결하여 심층적인 인사이트 제공
   - 예: "동적 난이도 → maintains → 몰입 → boosts → 리텐션"
     → "동적 난이도가 몰입을 유지하고, 이는 리텐션 향상으로 이어집니다"

4. **자연스러운 설명**:
   - 관계를 나열하지 말고, 의미를 추론해서 풀어서 설명
   - 게임 플레이 관점에서 실용적인 답변
   - 신뢰도가 높은(0.8+) 관계 우선 활용

5. **대화형 응답**:
   - 짧고 명확하게 (2-4문장)
   - 필요시 추가 질문 유도: "~에 대해 더 알고 싶으신가요?"
   - 친근하고 자연스러운 톤

**중요**:
- 기술적인 용어(predicate, confidence 등)는 사용자에게 노출하지 마세요
- 온톨로지 룰은 추론의 근거로만 사용 (직접 언급 X)
- 데이터가 부족하면 솔직하게: "현재 그래프에 관계가 없네요"
"""
        else:
            return """당신은 PokoPoko 게임에 대한 AI 어시스턴트입니다.

현재 질문하신 내용에 대한 지식 그래프 정보가 없습니다.

답변 방식:
- 짧게 사과하고
- 답변 가능한 주제 안내 (예: "스테이지, 미션, 클로버 등에 대해서는 답변할 수 있어요!")
- 친근하고 자연스럽게
"""

    def chat(self, user_message):
        """대화 처리 (상세 추론 과정 포함)"""
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

        # 5. 그래프 컨텍스트 생성
        print(f"{Colors.OKCYAN}5️⃣ LLM 컨텍스트 생성{Colors.ENDC}")
        graph_context = self.build_graph_context(mentioned_terms, subgraph)

        context_stats = {
            "대화 맥락 용어": len(self.context_terms),
            "온톨로지 룰": len(self.ontology_rules),
            "관련 개념": len(subgraph['nodes']),
            "실제 관계": len(subgraph['unique_edges'])
        }

        print(f"   {Colors.OKGREEN}✅ 컨텍스트 요소:{Colors.ENDC}")
        for key, value in context_stats.items():
            print(f"      - {key}: {value}개")
        print()

        # 6. LLM 호출
        print(f"{Colors.OKCYAN}6️⃣ GPT-4 응답 생성{Colors.ENDC}")
        print(f"   모델: gpt-4o")
        print(f"   온톨로지 룰 기반 추론 활성화")
        print(f"   대화 히스토리: {len(self.conversation_history) // 2}턴 유지\n")

        system_prompt = self.generate_system_prompt(graph_context)

        messages = [{"role": "system", "content": system_prompt}]

        # 대화 히스토리 추가 (최근 5턴)
        for msg in self.conversation_history[-10:]:  # 최근 5턴 (user+assistant = 10개)
            messages.append(msg)

        # 현재 사용자 메시지
        messages.append({"role": "user", "content": user_message})

        # OpenAI API 호출
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content

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
        print(f"  - 사용된 관계: {len(subgraph['unique_edges'])}개")
        print(f"  - 탐색 깊이: 2-hop")
        print(f"  - 최고 신뢰도 관계: {subgraph['unique_edges'][0]['confidence']:.2f}" if subgraph['unique_edges'] else "  - N/A")
        print(f"  - 대화 컨텍스트: {', '.join(list(self.context_terms)[-3:])}" if len(self.context_terms) > 1 else "  - 없음")

        print(f"\n{Colors.BOLD}{'━'*70}{Colors.ENDC}\n")

    def run(self):
        """대화형 루프 실행"""
        print(f"{Colors.HEADER}💬 대화를 시작합니다. 종료하려면 'exit' 또는 'quit'를 입력하세요.{Colors.ENDC}\n")

        # 환영 메시지
        print(f"{Colors.OKGREEN}안녕하세요! PokoPoko 게임의 지식 그래프 어시스턴트입니다.{Colors.ENDC}")
        print(f"{Colors.OKGREEN}게임 메카닉, 이벤트, UX, 비즈니스 로직에 대해 물어보세요!{Colors.ENDC}\n")

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
    chatbot = GraphRAGChatbot()
    chatbot.run()

if __name__ == "__main__":
    main()
