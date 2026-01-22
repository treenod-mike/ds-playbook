"""
Document classification rules for Confluence pages
"""
import re
from typing import List
from dataclasses import dataclass


@dataclass
class ClassificationRule:
    """Rule for classifying documents"""
    category: str
    keywords: List[str]
    title_patterns: List[str]
    priority: int = 0


class DocumentClassifier:
    """Classify Confluence documents into categories"""

    def __init__(self):
        self.rules = self._define_rules()

    def _define_rules(self) -> List[ClassificationRule]:
        """Define classification rules"""
        return [
            # Experiment-related documents
            ClassificationRule(
                category="experiment",
                keywords=[
                    "실험", "experiment", "a/b test", "abtest", "테스트",
                    "variant", "control", "treatment", "hypothesis"
                ],
                title_patterns=[r"실험.*설계", r"A/B.*테스트", r"EXP[-_]?\d+"],
                priority=10
            ),

            # Economy/Monetization documents
            ClassificationRule(
                category="economy",
                keywords=[
                    "경제", "economy", "monetization", "수익화", "가격",
                    "pricing", "revenue", "매출", "구매", "상품"
                ],
                title_patterns=[r"경제.*시스템", r"수익.*모델", r"가격.*정책"],
                priority=9
            ),

            # Analytics/Data documents
            ClassificationRule(
                category="analytics",
                keywords=[
                    "분석", "analytics", "데이터", "data", "지표", "metric",
                    "dashboard", "대시보드", "리포트", "report"
                ],
                title_patterns=[r"데이터.*분석", r"지표.*정의"],
                priority=8
            ),

            # Game Design documents
            ClassificationRule(
                category="game_design",
                keywords=[
                    "게임", "game", "디자인", "design", "밸런스", "balance",
                    "레벨", "level", "콘텐츠", "content"
                ],
                title_patterns=[r"게임.*디자인", r"밸런스.*설계"],
                priority=7
            ),

            # Product/Feature documents
            ClassificationRule(
                category="product",
                keywords=[
                    "제품", "product", "기능", "feature", "요구사항",
                    "requirement", "스펙", "spec", "기획"
                ],
                title_patterns=[r"제품.*기획", r"기능.*명세", r"PRD"],
                priority=6
            ),

            # General/Uncategorized (lowest priority)
            ClassificationRule(
                category="general",
                keywords=[],
                title_patterns=[],
                priority=0
            ),
        ]

    def classify(self, title: str, content: str) -> str:
        """
        Classify a document based on title and content

        Args:
            title: Document title
            content: Document content

        Returns:
            Category name
        """
        # Normalize text for matching
        title_lower = title.lower()
        content_lower = content.lower()[:1000]  # Only check first 1000 chars

        best_match = None
        best_score = -1

        for rule in self.rules:
            score = 0

            # Check title patterns (highest weight)
            for pattern in rule.title_patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    score += 10

            # Check keywords in title (medium weight)
            title_keyword_matches = sum(
                1 for keyword in rule.keywords if keyword in title_lower
            )
            score += title_keyword_matches * 5

            # Check keywords in content (lower weight)
            content_keyword_matches = sum(
                1 for keyword in rule.keywords if keyword in content_lower
            )
            score += content_keyword_matches * 1

            # Add priority bonus
            score += rule.priority

            # Update best match
            if score > best_score:
                best_score = score
                best_match = rule.category

        # If no meaningful match found, return general
        if best_score <= 0:
            return "general"

        return best_match or "general"


# Singleton instance
classifier = DocumentClassifier()


def classify_document(title: str, content: str) -> str:
    """
    Convenience function to classify a document

    Args:
        title: Document title
        content: Document content

    Returns:
        Category name
    """
    return classifier.classify(title, content)
