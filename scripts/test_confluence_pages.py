#!/usr/bin/env python3
"""
Simple test to check if we can access Confluence pages
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.processors.confluence_processor import ConfluenceProcessor
from src.shared.utils import load_page_ids

def main():
    print("=" * 70)
    print("Testing Confluence Page Access")
    print("=" * 70)

    # Initialize processor
    confluence = ConfluenceProcessor()

    # Load page IDs
    page_ids = load_page_ids()
    print(f"\nLoaded {len(page_ids)} page IDs")

    # Test first 3 pages
    test_pages = page_ids[:3]
    print(f"\nTesting first 3 pages: {test_pages}")
    print()

    for i, page_id in enumerate(test_pages, 1):
        print(f"{i}. Testing page {page_id}...")

        try:
            page_data = confluence.process_page(page_id)

            if page_data:
                print(f"   ✅ SUCCESS")
                print(f"   - Title: {page_data.get('title', 'N/A')[:60]}")
                print(f"   - Content length: {len(page_data.get('content', ''))} characters")
                print(f"   - URL: {page_data.get('url', 'N/A')}")
                print(f"   - Space: {page_data.get('space_key', 'N/A')}")
            else:
                print(f"   ❌ FAILED - No data returned")

        except Exception as e:
            print(f"   ❌ ERROR: {e}")

        print()

    print("=" * 70)
    print("Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()
