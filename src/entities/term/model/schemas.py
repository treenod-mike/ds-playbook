"""
Term Entity - Pydantic Schemas

용어(Term) 관련 데이터 모델
"""
from pydantic import BaseModel
from typing import Optional


class Term(BaseModel):
    """용어 엔티티"""
    id: str
    term: str
    category: str
    document_id: Optional[str] = None
    definition: Optional[str] = None

    # Fuzzy matching 결과 (선택적)
    match_type: Optional[str] = None  # 'exact' | 'exact_fuzzy' | 'fuzzy'
    match_confidence: Optional[float] = None
