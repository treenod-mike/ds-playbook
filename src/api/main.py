"""
FastAPI application for DS-Playbook GraphRAG system
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from src.core.loaders.supabase_loader import SupabaseLoader
from src.core.traversal import GraphTraversal, SubgraphExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DS-Playbook GraphRAG API",
    description="Knowledge graph exploration and analysis API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
supabase_loader = None
graph_traversal = None
subgraph_extractor = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global supabase_loader, graph_traversal, subgraph_extractor

    try:
        logger.info("Initializing Supabase connection...")
        supabase_loader = SupabaseLoader()
        graph_traversal = GraphTraversal(supabase_loader.client)
        subgraph_extractor = SubgraphExtractor(supabase_loader.client)
        logger.info("✅ Supabase connection established")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


# Pydantic models
class PathResponse(BaseModel):
    nodes: List[str]
    edges: List[str]
    depth: int
    confidence: float


class ImpactAnalysisRequest(BaseModel):
    source_node: str
    max_depth: int = 3
    min_confidence: float = 0.5


class ImpactAnalysisResponse(BaseModel):
    source: str
    max_depth: int
    impact_map: Dict[int, List[str]]
    total_nodes: int


class SubgraphRequest(BaseModel):
    center_node: str
    radius: int = 2
    min_confidence: float = 0.5


class SubgraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    center: str


# Endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "DS-Playbook GraphRAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "terms": "/api/terms",
            "impact_analysis": "/api/impact-analysis",
            "subgraph": "/api/subgraph",
            "shortest_path": "/api/shortest-path"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        result = supabase_loader.client.table('playbook_semantic_terms')\
            .select("id")\
            .limit(1)\
            .execute()

        return {
            "status": "healthy",
            "supabase": "connected",
            "terms_available": len(result.data) > 0
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/api/terms")
async def get_terms(limit: int = 10, category: Optional[str] = None):
    """Get semantic terms from database"""
    try:
        query = supabase_loader.client.table('playbook_semantic_terms')\
            .select("term, category, definition")

        if category:
            query = query.eq("category", category)

        result = query.limit(limit).execute()

        return {
            "terms": result.data,
            "count": len(result.data)
        }
    except Exception as e:
        logger.error(f"Error fetching terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/impact-analysis", response_model=ImpactAnalysisResponse)
async def impact_analysis(request: ImpactAnalysisRequest):
    """
    Analyze impact range using DFS traversal

    Shows how far a change in the source node can propagate through the graph.
    """
    try:
        logger.info(f"Impact analysis for: {request.source_node}")

        impact_map = graph_traversal.dfs_traversal(
            start_term=request.source_node,
            max_depth=request.max_depth,
            min_confidence=request.min_confidence
        )

        if not impact_map:
            raise HTTPException(
                status_code=404,
                detail=f"Term '{request.source_node}' not found or has no connections"
            )

        total_nodes = sum(len(terms) for terms in impact_map.values())

        return ImpactAnalysisResponse(
            source=request.source_node,
            max_depth=request.max_depth,
            impact_map=impact_map,
            total_nodes=total_nodes
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in impact analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/subgraph", response_model=SubgraphResponse)
async def get_subgraph(request: SubgraphRequest):
    """
    Extract subgraph around a center node

    Returns nodes and edges for visualization.
    """
    try:
        logger.info(f"Extracting subgraph for: {request.center_node}")

        subgraph = subgraph_extractor.extract_subgraph(
            center_term=request.center_node,
            radius=request.radius,
            min_confidence=request.min_confidence
        )

        if not subgraph['nodes']:
            raise HTTPException(
                status_code=404,
                detail=f"Term '{request.center_node}' not found"
            )

        return SubgraphResponse(
            nodes=subgraph['nodes'],
            edges=subgraph['edges'],
            center=request.center_node
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting subgraph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shortest-path")
async def shortest_path(
    start: str,
    end: str,
    max_depth: int = 5,
    min_confidence: float = 0.5
):
    """
    Find shortest path between two terms
    """
    try:
        logger.info(f"Finding path: {start} -> {end}")

        path = graph_traversal.find_shortest_path(
            start_term=start,
            end_term=end,
            max_depth=max_depth,
            min_confidence=min_confidence
        )

        if not path:
            return {
                "found": False,
                "message": f"No path found between '{start}' and '{end}' within {max_depth} hops"
            }

        return {
            "found": True,
            "path": {
                "nodes": path.nodes,
                "edges": path.edges,
                "depth": path.depth,
                "confidence": path.total_confidence
            }
        }
    except Exception as e:
        logger.error(f"Error finding shortest path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
