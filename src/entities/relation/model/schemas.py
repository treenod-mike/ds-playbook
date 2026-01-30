"""
Relation Entity - Pydantic Schemas

관계(Relation) 관련 데이터 모델
"""
from pydantic import BaseModel
from typing import Optional


class Relation(BaseModel):
    """관계 엔티티"""
    id: str
    subject_id: str
    object_id: str
    predicate: str
    confidence: float
    document_id: Optional[str] = None
    evidence: Optional[str] = None
