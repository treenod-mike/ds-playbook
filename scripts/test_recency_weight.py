#!/usr/bin/env python3
"""
Test script for recency weight calculation

최신성 가중치 계산 함수 테스트
"""
import sys
sys.path.insert(0, '/Users/mike/Desktop/playbook_nexus')

from datetime import datetime, timedelta, timezone

# Import the function
from src.core.processors.ontology_builder import calculate_recency_weight

print("=" * 70)
print("📅 최신성 가중치 계산 테스트")
print("=" * 70)
print()

now = datetime.now(timezone.utc)

test_cases = [
    ("1주일 전", now - timedelta(days=7)),
    ("1개월 전", now - timedelta(days=30)),
    ("2개월 전", now - timedelta(days=60)),
    ("3개월 전", now - timedelta(days=90)),
    ("6개월 전", now - timedelta(days=180)),
    ("9개월 전", now - timedelta(days=270)),
    ("1년 전", now - timedelta(days=365)),
    ("2년 전", now - timedelta(days=730)),
    ("5년 전", now - timedelta(days=1825)),
]

print("테스트 케이스:")
print("-" * 70)
print(f"{'기간':<15} {'날짜':<20} {'가중치':<10} {'효과'}")
print("-" * 70)

for label, date in test_cases:
    date_str = date.isoformat()
    weight = calculate_recency_weight(date_str)

    # 0.8 confidence 기준 효과
    base_conf = 0.8
    weighted_conf = min(base_conf * weight, 1.0)
    boost_pct = (weighted_conf - base_conf) / base_conf * 100 if weight > 1.0 else 0

    effect = f"+{boost_pct:.0f}%" if boost_pct > 0 else "기본"

    print(f"{label:<15} {date.strftime('%Y-%m-%d'):<20} {weight:<10.2f} {effect}")

print()
print("=" * 70)
print("💡 예상 효과 (confidence 0.8 기준)")
print("=" * 70)
print()

example_relations = [
    ("클로버", "consumes", "스테이지", 0.8, 7),    # 1주일 전
    ("폭탄", "clears", "블록", 0.8, 60),           # 2개월 전
    ("체리", "unlocks", "컨텐츠", 0.8, 400),       # 1년+ 전
]

print("문서별 관계 예시:")
print("-" * 70)

for source, pred, target, conf, days_old in example_relations:
    doc_date = now - timedelta(days=days_old)
    weight = calculate_recency_weight(doc_date.isoformat())
    weighted_conf = min(conf * weight, 1.0)

    print(f"\n'{source}' -{pred}-> '{target}'")
    print(f"  문서 날짜: {doc_date.strftime('%Y-%m-%d')} ({days_old}일 전)")
    print(f"  기본 confidence: {conf:.2f}")
    print(f"  가중치: {weight:.2f}x")
    print(f"  최종 confidence: {weighted_conf:.2f} {'✨' if weighted_conf > conf else ''}")

print()
print("=" * 70)
print("✅ 테스트 완료")
print("=" * 70)
