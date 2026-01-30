#!/usr/bin/env python3
"""
v3.0 통합 테스트 스크립트 (비대화형)

test_chatbot_v3_integrated.py가 올바르게 작동하는지 테스트합니다.
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

# Color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def test_v3_components():
    """v3.0 핵심 컴포넌트 테스트"""
    print(f"\n{Colors.HEADER}{'='*70}")
    print("v3.0 Integration Test - Component Verification")
    print(f"{'='*70}{Colors.ENDC}\n")

    # 1. Supabase 연결
    print(f"{Colors.OKCYAN}1️⃣ Supabase 연결 테스트{Colors.ENDC}")
    try:
        supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        print(f"   {Colors.OKGREEN}✅ 연결 성공{Colors.ENDC}\n")
    except Exception as e:
        print(f"   {Colors.FAIL}❌ 연결 실패: {e}{Colors.ENDC}\n")
        return

    # 2. OpenAI 연결
    print(f"{Colors.OKCYAN}2️⃣ OpenAI 연결 테스트{Colors.ENDC}")
    try:
        openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", None)
        )
        print(f"   {Colors.OKGREEN}✅ 연결 성공{Colors.ENDC}\n")
    except Exception as e:
        print(f"   {Colors.FAIL}❌ 연결 실패: {e}{Colors.ENDC}\n")
        return

    # 3. 데이터베이스 상태 확인
    print(f"{Colors.OKCYAN}3️⃣ 데이터베이스 상태 확인{Colors.ENDC}")
    try:
        doc_count = supabase.table('playbook_documents').select("id", count='exact').execute()
        chunk_count = supabase.table('playbook_chunks').select("id", count='exact').execute()
        term_count = supabase.table('playbook_semantic_terms').select("id", count='exact').execute()
        rel_count = supabase.table('playbook_semantic_relations').select("source_term_id", count='exact').execute()
        rule_count = supabase.table('playbook_ontology_rules').select("id", count='exact').execute()

        print(f"   - Documents: {doc_count.count} rows")
        print(f"   - Chunks: {chunk_count.count} rows")
        print(f"   - Terms: {term_count.count} rows")
        print(f"   - Relations: {rel_count.count} rows")
        print(f"   - Ontology Rules: {rule_count.count} rows")

        if doc_count.count == 0 or chunk_count.count == 0:
            print(f"   {Colors.WARNING}⚠️ 데이터가 없습니다. Phase 1을 실행하세요: bash run_phase1_test.sh{Colors.ENDC}\n")
            return
        else:
            print(f"   {Colors.OKGREEN}✅ 데이터 존재{Colors.ENDC}\n")

    except Exception as e:
        print(f"   {Colors.FAIL}❌ 데이터 조회 실패: {e}{Colors.ENDC}\n")
        return

    # 4. RAGContextFormatter 테스트
    print(f"{Colors.OKCYAN}4️⃣ RAGContextFormatter 테스트{Colors.ENDC}")
    try:
        formatter = RAGContextFormatter()

        # 샘플 데이터
        vector_results = [
            SearchResult(
                chunk_id=1,
                doc_id=1,
                doc_title="Test Document",
                content="This is a test content.",
                similarity=0.95
            )
        ]

        graph_relations = [
            GraphRelation(
                source="Test Source",
                predicate="test_relation",
                target="Test Target",
                confidence=0.90,
                evidence="Test evidence"
            )
        ]

        ontology_rules = [
            {
                "subject_type": "mechanic",
                "predicate": "balances",
                "object_type": "condition",
                "description": "Test rule"
            }
        ]

        context = formatter.build_full_context(
            query="Test query?",
            vector_results=vector_results,
            graph_relations=graph_relations,
            ontology_rules=ontology_rules,
            center_term="Test"
        )

        # XML 구조 검증 (기본 구조만 확인)
        if "<Context>" in context and "</Context>" in context:
            print(f"   {Colors.OKGREEN}✅ XML 컨텍스트 생성 성공{Colors.ENDC}\n")
        else:
            print(f"   {Colors.FAIL}❌ XML 구조 오류{Colors.ENDC}\n")
            print(context[:500])
            return

    except Exception as e:
        print(f"   {Colors.FAIL}❌ Context Formatter 실패: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        return

    # 5. RAGAnswerGenerator 테스트 (실제 데이터)
    print(f"{Colors.OKCYAN}5️⃣ RAGAnswerGenerator 테스트 (실제 데이터){Colors.ENDC}")

    # 실제 용어 검색
    terms_result = supabase.table('playbook_semantic_terms')\
        .select("id, term, category")\
        .limit(5)\
        .execute()

    if not terms_result.data:
        print(f"   {Colors.WARNING}⚠️ 용어가 없습니다{Colors.ENDC}\n")
        return

    print(f"   사용 가능한 용어 (샘플 5개):")
    for term_data in terms_result.data:
        print(f"     - {term_data['term']} ({term_data['category']})")
    print()

    # 첫 번째 용어로 테스트
    test_term = terms_result.data[0]
    test_query = f"{test_term['term']}가 뭐야?"

    print(f"   테스트 질문: \"{test_query}\"")
    print(f"   중심 용어: {test_term['term']} ({test_term['category']})\n")

    # 청크 검색
    chunks_result = supabase.table('playbook_chunks')\
        .select("id, doc_id, content")\
        .ilike("content", f"%{test_term['term']}%")\
        .limit(3)\
        .execute()

    vector_results = []
    for chunk in chunks_result.data:
        doc_result = supabase.table('playbook_documents')\
            .select("title")\
            .eq("id", chunk['doc_id'])\
            .limit(1)\
            .execute()

        doc_title = doc_result.data[0]['title'] if doc_result.data else "Unknown"

        vector_results.append(SearchResult(
            chunk_id=str(chunk['id']),  # UUID to string
            doc_id=chunk['doc_id'],  # TEXT
            doc_title=doc_title,
            content=chunk['content'][:200],
            similarity=0.90
        ))

    print(f"   {Colors.OKGREEN}✅ {len(vector_results)}개 청크 발견{Colors.ENDC}")

    # 관계 검색
    relations_result = supabase.table('playbook_semantic_relations')\
        .select("source_term_id, target_term_id, predicate, confidence")\
        .eq("source_term_id", test_term['id'])\
        .gte("confidence", 0.7)\
        .limit(5)\
        .execute()

    graph_relations = []
    for rel in relations_result.data:
        target_result = supabase.table('playbook_semantic_terms')\
            .select("term")\
            .eq("id", rel['target_term_id'])\
            .limit(1)\
            .execute()

        if target_result.data:
            target_term = target_result.data[0]['term']
            graph_relations.append(GraphRelation(
                source=test_term['term'],
                predicate=rel['predicate'],
                target=target_term,
                confidence=rel['confidence']
            ))

    print(f"   {Colors.OKGREEN}✅ {len(graph_relations)}개 관계 발견{Colors.ENDC}")

    # 온톨로지 룰
    rules_result = supabase.table('playbook_ontology_rules')\
        .select("subject_type, predicate, object_type, description")\
        .limit(10)\
        .execute()

    ontology_rules = rules_result.data
    print(f"   {Colors.OKGREEN}✅ {len(ontology_rules)}개 온톨로지 룰 로드{Colors.ENDC}\n")

    # 답변 생성
    print(f"{Colors.OKCYAN}6️⃣ GPT-4o 답변 생성{Colors.ENDC}")
    try:
        generator = RAGAnswerGenerator(openai_client)

        result = generator.generate_answer(
            query=test_query,
            vector_results=vector_results,
            graph_relations=graph_relations,
            ontology_rules=ontology_rules,
            center_term=test_term['term'],
            temperature=0.3
        )

        if result["success"]:
            print(f"   {Colors.OKGREEN}✅ 답변 생성 성공{Colors.ENDC}\n")

            print(f"{Colors.HEADER}{'='*70}")
            print("[생성된 답변]")
            print(f"{'='*70}{Colors.ENDC}\n")
            print(result["answer"])

            print(f"\n{Colors.HEADER}{'='*70}")
            print("[메타데이터]")
            print(f"{'='*70}{Colors.ENDC}")
            metadata = result["metadata"]
            print(f"  - 모델: {metadata['model']}")
            print(f"  - Temperature: {metadata['temperature']}")
            print(f"  - 사용 토큰: {metadata['tokens_used']}")
            print(f"  - 청크 수: {metadata['num_chunks']}")
            print(f"  - 관계 수: {metadata['num_relations']}")
            print(f"  - 룰 수: {metadata['num_rules']}")

            # 답변 품질 검증
            print(f"\n{Colors.HEADER}{'='*70}")
            print("[답변 품질 검증]")
            print(f"{'='*70}{Colors.ENDC}")

            answer_text = result["answer"]
            has_citation = "[Source:" in answer_text or "[Chunk:" in answer_text
            has_structure = "##" in answer_text
            has_context_only = "현재 문서" not in answer_text or len(vector_results) > 0

            print(f"  - 출처 표기 존재: {'✅' if has_citation else '❌'} {has_citation}")
            print(f"  - 구조화된 답변: {'✅' if has_structure else '❌'} {has_structure}")
            print(f"  - 컨텍스트 기반: {'✅' if has_context_only else '⚠️'} {has_context_only}")

            if has_citation and has_structure:
                print(f"\n{Colors.OKGREEN}{'='*70}")
                print("✅ v3.0 Integration Test PASSED")
                print(f"{'='*70}{Colors.ENDC}\n")
            else:
                print(f"\n{Colors.WARNING}{'='*70}")
                print("⚠️ 답변이 생성되었지만 품질 검증에서 일부 항목이 누락되었습니다")
                print(f"{'='*70}{Colors.ENDC}\n")

        else:
            print(f"   {Colors.FAIL}❌ 답변 생성 실패: {result['error']}{Colors.ENDC}\n")

    except Exception as e:
        print(f"   {Colors.FAIL}❌ 답변 생성 오류: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_v3_components()
