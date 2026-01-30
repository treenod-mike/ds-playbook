"""
FastAPI application for DS-Playbook GraphRAG system

⚠️ DEPRECATED: This file is kept for backward compatibility.
New main app is at src/app/main.py (FSD 2.1 structure)
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import new FSD-structured app
from src.app.main import app

# Re-export for backward compatibility
__all__ = ['app']
