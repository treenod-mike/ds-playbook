"""
Chat Feature - API Routes

채팅 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from src.entities.message import ChatRequest, ChatResponse
from src.features.chat.model import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


def get_chat_service():
    """
    DI 함수 - ChatService 인스턴스 반환

    실제 구현은 app/dependencies.py에서 제공
    """
    raise NotImplementedError("ChatService DI not configured")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat with GraphRAG-enhanced knowledge assistant

    Args:
        request: 채팅 요청 (messages, use_graph)
        chat_service: ChatService 인스턴스 (DI)

    Returns:
        채팅 응답 (message, graph_data, search_process)
    """
    try:
        user_message = request.messages[-1].content

        # Convert messages to conversation history
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages[:-1]
        ]

        # Call service
        result = await chat_service.handle_chat(
            user_message=user_message,
            use_graph=request.use_graph,
            conversation_history=conversation_history
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
