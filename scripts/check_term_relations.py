#!/usr/bin/env python3
"""
용어의 관계 데이터 확인 스크립트
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from supabase import create_client

def check_term_relations(term_name: str):
    """Check all instances of a term and their relations"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    print(f"\n{'='*70}")
    print(f"Checking term: '{term_name}'")
    print(f"{'='*70}\n")

    # Get all terms with this name
    terms_result = client.table(Config.TABLE_SEMANTIC)\
        .select("id, term, category, doc_id, frequency, confidence")\
        .eq("term", term_name)\
        .execute()

    if not terms_result.data:
        print(f"❌ No term found with name '{term_name}'")
        return

    print(f"Found {len(terms_result.data)} instance(s) of '{term_name}':\n")

    for idx, term in enumerate(terms_result.data, 1):
        print(f"Instance {idx}:")
        print(f"  - ID: {term['id']}")
        print(f"  - Category: {term.get('category', 'N/A')}")
        print(f"  - Doc ID: {term.get('doc_id', 'N/A')}")
        print(f"  - Frequency: {term.get('frequency', 'N/A')}")
        print(f"  - Confidence: {term.get('confidence', 'N/A')}")

        term_id = term['id']

        # Check outgoing relations
        out_rels = client.table(Config.TABLE_RELATIONS)\
            .select("predicate, target_term_id, confidence, relation_type, weight")\
            .eq("source_term_id", term_id)\
            .execute()

        # Check incoming relations
        in_rels = client.table(Config.TABLE_RELATIONS)\
            .select("predicate, source_term_id, confidence, relation_type, weight")\
            .eq("target_term_id", term_id)\
            .execute()

        print(f"  - Outgoing relations: {len(out_rels.data)}")
        if out_rels.data:
            for rel in out_rels.data[:3]:  # Show first 3
                target = client.table(Config.TABLE_SEMANTIC)\
                    .select("term")\
                    .eq("id", rel['target_term_id'])\
                    .limit(1)\
                    .execute()
                target_term = target.data[0]['term'] if target.data else 'Unknown'
                rel_type = rel.get('relation_type', 'N/A')
                weight = rel.get('weight', 'N/A')
                print(f"      → [{rel['predicate']}] → {target_term} ({rel_type}, weight={weight}, conf={rel['confidence']:.2f})")
            if len(out_rels.data) > 3:
                print(f"      ... and {len(out_rels.data) - 3} more")

        print(f"  - Incoming relations: {len(in_rels.data)}")
        if in_rels.data:
            for rel in in_rels.data[:3]:  # Show first 3
                source = client.table(Config.TABLE_SEMANTIC)\
                    .select("term")\
                    .eq("id", rel['source_term_id'])\
                    .limit(1)\
                    .execute()
                source_term = source.data[0]['term'] if source.data else 'Unknown'
                rel_type = rel.get('relation_type', 'N/A')
                weight = rel.get('weight', 'N/A')
                print(f"      {source_term} → [{rel['predicate']}] ({rel_type}, weight={weight}, conf={rel['confidence']:.2f})")
            if len(in_rels.data) > 3:
                print(f"      ... and {len(in_rels.data) - 3} more")

        print()

    print(f"{'='*70}\n")


def check_default_term():
    """Check if there's a 'default' term being returned"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    # Check for '그룹' term
    print(f"\n{'='*70}")
    print(f"Checking '그룹' term (suspected default)")
    print(f"{'='*70}\n")

    check_term_relations("그룹")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        term = sys.argv[1]
        check_term_relations(term)
    else:
        print("Usage: python3 scripts/check_term_relations.py <term_name>")
        print("\nExamples:")
        print("  python3 scripts/check_term_relations.py 클로버")
        print("  python3 scripts/check_term_relations.py 스테이지")
        print("  python3 scripts/check_term_relations.py 그룹")

        # Check common terms
        print("\n\nChecking common terms...")
        check_default_term()
        check_term_relations("클로버")
        check_term_relations("스테이지")
