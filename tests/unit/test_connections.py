#!/usr/bin/env python3
"""
Test all API connections before running the main pipeline
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.shared.utils import setup_logging
from src.core.processors.confluence_processor import ConfluenceProcessor
from src.core.processors.semantic_processor import SemanticProcessor
from src.core.loaders.supabase_loader import SupabaseLoader

logger = setup_logging()

def main():
    print("="*70)
    print("Testing All API Connections")
    print("="*70)

    # Validate config
    print("\n1. Validating Configuration...")
    try:
        Config.validate()
        print("   ✅ All required environment variables are set")
    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        return

    # Test Confluence
    print("\n2. Testing Confluence API...")
    print(f"   URL: {Config.CONFLUENCE_URL}")
    print(f"   Email: {Config.CONFLUENCE_EMAIL}")
    try:
        confluence = ConfluenceProcessor()
        if confluence.test_connection():
            print("   ✅ Confluence connection successful")
        else:
            print("   ❌ Confluence connection failed")
    except Exception as e:
        print(f"   ❌ Confluence error: {e}")

    # Test OpenAI
    print("\n3. Testing OpenAI API...")
    print(f"   Base URL: {Config.OPENAI_BASE_URL or 'Default (https://api.openai.com/v1)'}")
    print(f"   Model: {Config.EMBEDDING_MODEL}")
    try:
        semantic = SemanticProcessor()
        if semantic.test_connection():
            print("   ✅ OpenAI connection successful")
        else:
            print("   ❌ OpenAI connection failed")
    except Exception as e:
        print(f"   ❌ OpenAI error: {e}")

    # Test Supabase
    print("\n4. Testing Supabase...")
    print(f"   URL: {Config.SUPABASE_URL}")
    print(f"   Table: {Config.SUPABASE_TABLE}")
    try:
        supabase = SupabaseLoader()
        if supabase.test_connection():
            print("   ✅ Supabase connection successful")
        else:
            print("   ❌ Supabase connection failed")
    except Exception as e:
        print(f"   ❌ Supabase error: {e}")

    print("\n" + "="*70)
    print("Connection Test Complete")
    print("="*70)

if __name__ == "__main__":
    main()
