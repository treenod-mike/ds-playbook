"""Entities Layer - Business Entities

FSD 2.1 Entities Layer:
- 비즈니스 엔티티 정의
- 데이터 접근 레이어 (Repository)
- 엔티티별 유틸리티
"""
from .message import ChatMessage, ChatRequest, ChatResponse
from .term import Term, TermRepository, normalize_korean_text, fuzzy_similarity, find_matching_terms
from .relation import Relation, RelationRepository

__all__ = [
    # Message
    'ChatMessage',
    'ChatRequest',
    'ChatResponse',
    # Term
    'Term',
    'TermRepository',
    'normalize_korean_text',
    'fuzzy_similarity',
    'find_matching_terms',
    # Relation
    'Relation',
    'RelationRepository',
]
