"""
App Layer - Dependency Injection

FastAPI 의존성 주입 컨테이너
"""
import logging
import os
from openai import OpenAI

from src.core.loaders.supabase_loader import SupabaseLoader
from src.core.traversal import GraphTraversal, SubgraphExtractor
from src.entities.term import TermRepository
from src.entities.relation import RelationRepository
from src.features.chat import ChatService

logger = logging.getLogger(__name__)

# Global singletons
_supabase_loader = None
_openai_client = None
_graph_traversal = None
_subgraph_extractor = None


def get_supabase_loader() -> SupabaseLoader:
    """Supabase Loader 싱글톤"""
    global _supabase_loader
    if _supabase_loader is None:
        _supabase_loader = SupabaseLoader()
    return _supabase_loader


def get_openai_client() -> OpenAI:
    """OpenAI 클라이언트 싱글톤"""
    global _openai_client
    if _openai_client is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_base_url = os.getenv("OPENAI_BASE_URL")

        if not openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")

        _openai_client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_base_url if openai_base_url else None
        )
    return _openai_client


def get_graph_traversal() -> GraphTraversal:
    """Graph Traversal 싱글톤"""
    global _graph_traversal
    if _graph_traversal is None:
        supabase_loader = get_supabase_loader()
        _graph_traversal = GraphTraversal(supabase_loader.client)
    return _graph_traversal


def get_subgraph_extractor() -> SubgraphExtractor:
    """Subgraph Extractor 싱글톤"""
    global _subgraph_extractor
    if _subgraph_extractor is None:
        supabase_loader = get_supabase_loader()
        _subgraph_extractor = SubgraphExtractor(supabase_loader.client)
    return _subgraph_extractor


def get_term_repository() -> TermRepository:
    """Term Repository"""
    supabase_loader = get_supabase_loader()
    return TermRepository(supabase_loader.client)


def get_relation_repository() -> RelationRepository:
    """Relation Repository"""
    supabase_loader = get_supabase_loader()
    return RelationRepository(supabase_loader.client)


def get_chat_service() -> ChatService:
    """Chat Service"""
    supabase_loader = get_supabase_loader()
    openai_client = get_openai_client()
    term_repo = get_term_repository()
    relation_repo = get_relation_repository()
    subgraph_extractor = get_subgraph_extractor()

    return ChatService(
        supabase_client=supabase_loader.client,
        openai_client=openai_client,
        term_repo=term_repo,
        relation_repo=relation_repo,
        subgraph_extractor=subgraph_extractor
    )


def init_dependencies():
    """
    의존성 초기화 (Startup 이벤트)
    """
    logger.info("Initializing dependencies...")

    # Supabase 초기화
    supabase_loader = get_supabase_loader()
    logger.info("✅ Supabase connection established")

    # Graph services 초기화
    get_graph_traversal()
    get_subgraph_extractor()
    logger.info("✅ Graph services initialized")

    # OpenAI 초기화 (선택적)
    try:
        openai_client = get_openai_client()
        openai_base_url = os.getenv("OPENAI_BASE_URL")
        logger.info(f"✅ OpenAI initialized (base_url: {openai_base_url or 'default'})")
    except RuntimeError:
        logger.warning("⚠️ OPENAI_API_KEY not found - chat endpoint will be unavailable")

    logger.info("✅ All dependencies initialized")
