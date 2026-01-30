#!/usr/bin/env python3
"""
RAG 답변 생성 테스트 스크립트

Context Formatter와 Answer Generator를 실제 Supabase 데이터로 테스트합니다.
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.core.generators.rag_answer_generator import (
    RAGAnswerGenerator,
    RAGContextFormatter,
    SearchResult,
    GraphRelation
)
from supabase import create_client
from openai import OpenAI

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


def test_context_formatter():
    """Context Formatter 테스트"""
    print(f"\n{Colors.HEADER}{'='*70}")
    print("1. Context Formatter 테스트")
    print(f"{'='*70}{Colors.ENDC}\n")

    formatter = RAGContextFormatter()

    # 예시 데이터
    vector_results = [
        SearchResult(
            chunk_id=123,
            doc_id=5,
            doc_title="155레벨 기획서",
            content="동적 난이도 시스템은 유저의 실력 수준에 맞춰 자동으로 난이도를 조절합니다.",
            similarity=0.92
        ),
        SearchResult(
            chunk_id=456,
            doc_id=8,
            doc_title="UX 개선 방안",
            content="적절한 난이도 밸런스는 유저의 좌절감을 줄이고 성취감을 높입니다.",
            similarity=0.85
        )
    ]

    graph_relations = [
        GraphRelation(
            source="동적 난이도",
            predicate="balances",
            target="유저 실력",
            confidence=0.95,
            evidence="유저 실력에 맞춘"
        ),
        GraphRelation(
            source="동적 난이도",
            predicate="relieves",
            target="좌절감",
            confidence=0.90,
            evidence="좌절감을 줄이고"
        )
    ]

    ontology_rules = [
        {
            "subject_type": "mechanic",
            "predicate": "balances",
            "object_type": "condition",
            "description": "메카닉이 조건/상태 균형 맞춤"
        }
    ]

    # Full Context 생성
    context = formatter.build_full_context(
        query="동적 난이도가 뭐야?",
        vector_results=vector_results,
        graph_relations=graph_relations,
        ontology_rules=ontology_rules,
        center_term="동적 난이도"
    )

    print(f"{Colors.OKCYAN}생성된 컨텍스트:{Colors.ENDC}\n")
    print(context)
    print(f"\n{Colors.OKGREEN}✅ Context Formatter 정상 작동{Colors.ENDC}\n")


def test_with_real_data(query: str):
    """실제 Supabase 데이터로 답변 생성 테스트"""
    print(f"\n{Colors.HEADER}{'='*70}")
    print("2. 실제 데이터 기반 답변 생성 테스트")
    print(f"{'='*70}{Colors.ENDC}\n")

    # Supabase 연결
    print(f"{Colors.OKCYAN}📡 Supabase 연결 중...{Colors.ENDC}")
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    print(f"{Colors.OKGREEN}✅ 연결 완료{Colors.ENDC}\n")

    # OpenAI 연결
    print(f"{Colors.OKCYAN}🤖 OpenAI 연결 중...{Colors.ENDC}")
    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", None)
    )
    print(f"{Colors.OKGREEN}✅ 연결 완료{Colors.ENDC}\n")

    # 1. 질문에서 용어 추출
    print(f"{Colors.OKCYAN}1️⃣ 질문 분석: \"{query}\"{Colors.ENDC}")

    # 간단히 키워드 매칭 (실제로는 semantic search 필요)
    terms_result = supabase.table('playbook_semantic_terms')\
        .select("id, term, category")\
        .execute()

    mentioned_terms = []
    for term_data in terms_result.data:
        if term_data['term'] in query:
            mentioned_terms.append(term_data)

    if not mentioned_terms:
        print(f"{Colors.WARNING}⚠️ 관련 용어를 찾을 수 없습니다.{Colors.ENDC}\n")
        return

    center_term = mentioned_terms[0]['term']
    print(f"   중심 용어: {center_term} ({mentioned_terms[0]['category']})\n")

    # 2. Vector Search 시뮬레이션 (실제로는 embedding search)
    print(f"{Colors.OKCYAN}2️⃣ Vector Search (청크 검색){Colors.ENDC}")

    chunks_result = supabase.table('playbook_chunks')\
        .select("chunk_id, doc_id, content")\
        .ilike("content", f"%{center_term}%")\
        .limit(3)\
        .execute()

    vector_results = []
    for chunk in chunks_result.data:
        # 문서 제목 가져오기
        doc_result = supabase.table('playbook_documents')\
            .select("title")\
            .eq("doc_id", chunk['doc_id'])\
            .limit(1)\
            .execute()

        doc_title = doc_result.data[0]['title'] if doc_result.data else "Unknown"

        vector_results.append(SearchResult(
            chunk_id=chunk['chunk_id'],
            doc_id=chunk['doc_id'],
            doc_title=doc_title,
            content=chunk['content'][:200] + "...",  # 일부만 표시
            similarity=0.90  # 시뮬레이션
        ))

    print(f"   {Colors.OKGREEN}✅ {len(vector_results)}개 청크 발견{Colors.ENDC}\n")

    # 3. Graph Traversal
    print(f"{Colors.OKCYAN}3️⃣ Graph Traversal (관계 검색){Colors.ENDC}")

    center_id = mentioned_terms[0]['id']

    # Outgoing relations
    relations_result = supabase.table('playbook_semantic_relations')\
        .select("source_term_id, target_term_id, predicate, confidence")\
        .eq("source_term_id", center_id)\
        .gte("confidence", 0.5)\
        .limit(5)\
        .execute()

    graph_relations = []
    for rel in relations_result.data:
        # Target term 가져오기
        target_result = supabase.table('playbook_semantic_terms')\
            .select("term")\
            .eq("id", rel['target_term_id'])\
            .limit(1)\
            .execute()

        if target_result.data:
            target_term = target_result.data[0]['term']
            graph_relations.append(GraphRelation(
                source=center_term,
                predicate=rel['predicate'],
                target=target_term,
                confidence=rel['confidence']
            ))

    print(f"   {Colors.OKGREEN}✅ {len(graph_relations)}개 관계 발견{Colors.ENDC}\n")

    # 4. Ontology Rules
    print(f"{Colors.OKCYAN}4️⃣ Ontology Rules 로드{Colors.ENDC}")

    rules_result = supabase.table('playbook_ontology_rules')\
        .select("subject_type, predicate, object_type, description")\
        .limit(10)\
        .execute()

    ontology_rules = rules_result.data
    print(f"   {Colors.OKGREEN}✅ {len(ontology_rules)}개 룰 로드{Colors.ENDC}\n")

    # 5. 답변 생성
    print(f"{Colors.OKCYAN}5️⃣ GPT-4 답변 생성{Colors.ENDC}")
    print(f"   모델: gpt-4o")
    print(f"   Temperature: 0.3 (보수적 생성)\n")

    generator = RAGAnswerGenerator(openai_client)

    result = generator.generate_answer(
        query=query,
        vector_results=vector_results,
        graph_relations=graph_relations,
        ontology_rules=ontology_rules,
        center_term=center_term,
        temperature=0.3
    )

    # 6. 결과 출력
    if result["success"]:
        print(f"{Colors.HEADER}{'='*70}")
        print("[생성된 답변]")
        print(f"{'='*70}{Colors.ENDC}\n")

        print(result["answer"])

        print(f"\n{Colors.HEADER}{'='*70}")
        print("[메타데이터]")
        print(f"{'='*70}{Colors.ENDC}")
        metadata = result["metadata"]
        print(f"  - 모델: {metadata['model']}")
        print(f"  - 사용 토큰: {metadata['tokens_used']}")
        print(f"  - 청크 수: {metadata['num_chunks']}")
        print(f"  - 관계 수: {metadata['num_relations']}")
        print(f"  - 룰 수: {metadata['num_rules']}")

        print(f"\n{Colors.OKGREEN}✅ 답변 생성 성공{Colors.ENDC}\n")

        # Context 확인 옵션
        show_context = input(f"{Colors.OKCYAN}생성된 컨텍스트를 확인하시겠습니까? (y/n): {Colors.ENDC}").strip().lower()
        if show_context == 'y':
            print(f"\n{Colors.HEADER}{'='*70}")
            print("[LLM에게 제공된 컨텍스트]")
            print(f"{'='*70}{Colors.ENDC}\n")
            print(result["context"])
    else:
        print(f"{Colors.FAIL}❌ 답변 생성 실패: {result['error']}{Colors.ENDC}\n")


def main():
    """메인 함수"""
    print(f"\n{Colors.HEADER}{'='*70}")
    print("RAG 답변 생성 시스템 테스트")
    print(f"{'='*70}{Colors.ENDC}\n")

    # 1. Context Formatter 테스트
    test_context_formatter()

    # 2. 실제 데이터 테스트
    print(f"{Colors.OKCYAN}실제 데이터로 테스트할 질문을 입력하세요:{Colors.ENDC}")
    print(f"{Colors.WARNING}(예: \"동적 난이도가 뭐야?\", \"클로버는 어디에 쓰이나요?\"){Colors.ENDC}")

    query = input(f"{Colors.OKCYAN}질문: {Colors.ENDC}").strip()

    if query:
        test_with_real_data(query)
    else:
        print(f"{Colors.WARNING}질문이 입력되지 않아 기본 테스트만 실행했습니다.{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
