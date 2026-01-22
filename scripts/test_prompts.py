#!/usr/bin/env python3
"""
Test script for prompts module
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.rules.prompts import (
    get_prompt,
    list_available_prompts,
    clear_cache,
    preload_prompts,
    get_synonyms,
    is_synonym
)


def test_list_prompts():
    """Test listing available prompts"""
    print("=" * 70)
    print("Available Prompts")
    print("=" * 70)

    prompts = list_available_prompts()
    print(f"Found {len(prompts)} prompt templates:")
    for prompt_name in prompts:
        print(f"  - {prompt_name}")
    print()

    return len(prompts) > 0


def test_load_prompts():
    """Test loading each prompt"""
    print("=" * 70)
    print("Loading Prompts")
    print("=" * 70)

    prompts = list_available_prompts()
    success_count = 0

    for prompt_name in prompts:
        try:
            content = get_prompt(prompt_name)
            print(f"✓ Loaded '{prompt_name}' ({len(content)} characters)")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to load '{prompt_name}': {e}")

    print()
    return success_count == len(prompts)


def test_caching():
    """Test prompt caching"""
    print("=" * 70)
    print("Testing Cache")
    print("=" * 70)

    # Clear cache
    clear_cache()
    print("✓ Cache cleared")

    # First load (from file)
    import time
    start = time.time()
    content1 = get_prompt("technical")
    first_load_time = time.time() - start
    print(f"✓ First load: {first_load_time*1000:.2f}ms")

    # Second load (from cache)
    start = time.time()
    content2 = get_prompt("technical")
    second_load_time = time.time() - start
    print(f"✓ Second load: {second_load_time*1000:.2f}ms (cached)")

    # Verify same content
    assert content1 == content2, "Content mismatch!"
    print(f"✓ Cache speedup: {first_load_time/second_load_time:.1f}x")

    print()
    return True


def test_preload():
    """Test preloading all prompts"""
    print("=" * 70)
    print("Testing Preload")
    print("=" * 70)

    clear_cache()
    preload_prompts()
    print("✓ All prompts preloaded")

    # Verify all are cached
    prompts = list_available_prompts()
    for prompt_name in prompts:
        content = get_prompt(prompt_name)
        assert content, f"Prompt '{prompt_name}' not cached!"

    print(f"✓ Verified {len(prompts)} prompts in cache")
    print()
    return True


def test_synonyms():
    """Test synonym dictionary"""
    print("=" * 70)
    print("Testing Synonyms")
    print("=" * 70)

    # Test get_synonyms
    k8s_synonyms = get_synonyms("k8s")
    print(f"Synonyms for 'k8s': {k8s_synonyms}")

    clover_synonyms = get_synonyms("클로버")
    print(f"Synonyms for '클로버': {clover_synonyms}")

    # Test is_synonym
    test_cases = [
        ("k8s", "kubernetes", True),
        ("클로버", "하트", True),
        ("docker", "kubernetes", False),
        ("폭탄", "bomb", True),
    ]

    for term1, term2, expected in test_cases:
        result = is_synonym(term1, term2)
        status = "✓" if result == expected else "✗"
        print(f"{status} is_synonym('{term1}', '{term2}') = {result} (expected: {expected})")

    print()
    return True


def test_relation_builder_prompt():
    """Test relation_builder prompt has placeholder"""
    print("=" * 70)
    print("Testing Relation Builder Prompt")
    print("=" * 70)

    try:
        prompt = get_prompt("relation_builder")

        # Check for {predicates} placeholder
        if "{predicates}" in prompt:
            print("✓ Found {predicates} placeholder")
        else:
            print("✗ Missing {predicates} placeholder")
            return False

        # Test placeholder replacement
        predicates = "triggers, consumes, blocks, defeats"
        filled_prompt = prompt.replace("{predicates}", predicates)

        if predicates in filled_prompt and "{predicates}" not in filled_prompt:
            print("✓ Placeholder replacement works")
        else:
            print("✗ Placeholder replacement failed")
            return False

        print(f"✓ Prompt length: {len(prompt)} characters")
        print()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Prompts Module Test Suite")
    print("=" * 70 + "\n")

    tests = [
        ("List Available Prompts", test_list_prompts),
        ("Load All Prompts", test_load_prompts),
        ("Test Caching", test_caching),
        ("Test Preload", test_preload),
        ("Test Synonyms", test_synonyms),
        ("Test Relation Builder Prompt", test_relation_builder_prompt),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print()
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
