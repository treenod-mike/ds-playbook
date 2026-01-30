"""Term Entity - Public API"""
from .model import Term, TermRepository
from .lib import normalize_korean_text, fuzzy_similarity, find_matching_terms

__all__ = [
    'Term',
    'TermRepository',
    'normalize_korean_text',
    'fuzzy_similarity',
    'find_matching_terms'
]
