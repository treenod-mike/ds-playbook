"""
Message Entity - Pydantic Schemas

채팅 메시지 관련 데이터 모델
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ChatMessage(BaseModel):
    """채팅 메시지"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """채팅 요청"""
    messages: List[ChatMessage]
    use_graph: bool = True


class ChatResponse(BaseModel):
    """채팅 응답"""
    message: str
    graph_data: Optional[Dict[str, Any]] = None
    search_process: Optional[Dict[str, Any]] = None
