"""
Prompt templates loader for semantic term extraction

This module loads prompts from markdown files in the prompts/ directory
with caching for performance optimization.
"""
import os
from typing import Dict, Optional

# ================================================================
# Prompt File Cache
# ================================================================

_PROMPT_CACHE: Dict[str, str] = {}

# Base directory for prompt files
_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def get_prompt(template_name: str = "technical", force_reload: bool = False) -> str:
    """
    Get system prompt by template name, loaded from markdown files

    Args:
        template_name: Name of the prompt template (technical, pokopoko, relation_builder)
        force_reload: Force reload from file even if cached

    Returns:
        System prompt string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    # Check cache first
    if not force_reload and template_name in _PROMPT_CACHE:
        return _PROMPT_CACHE[template_name]

    # Construct file path
    filename = f"system_{template_name}.md"
    filepath = os.path.join(_PROMPTS_DIR, filename)

    # Check if file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Prompt file not found: {filepath}\n"
            f"Available prompts: {list_available_prompts()}"
        )

    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    # Cache and return
    _PROMPT_CACHE[template_name] = prompt_content
    return prompt_content


def list_available_prompts() -> list:
    """
    List all available prompt templates

    Returns:
        List of prompt template names (without 'system_' prefix and '.md' suffix)
    """
    if not os.path.exists(_PROMPTS_DIR):
        return []

    prompts = []
    for filename in os.listdir(_PROMPTS_DIR):
        if filename.startswith("system_") and filename.endswith(".md"):
            # Extract template name: system_technical.md -> technical
            template_name = filename[7:-3]  # Remove 'system_' and '.md'
            prompts.append(template_name)

    return sorted(prompts)


def clear_cache():
    """Clear the prompt cache (useful for testing or hot-reloading)"""
    global _PROMPT_CACHE
    _PROMPT_CACHE.clear()


def preload_prompts():
    """
    Preload all available prompts into cache

    Useful for production environments to avoid file I/O during runtime
    """
    for template_name in list_available_prompts():
        try:
            get_prompt(template_name)
        except Exception as e:
            print(f"Warning: Failed to preload prompt '{template_name}': {e}")


# ================================================================
# Domain-Specific Synonym Dictionary (Extensible)
# ================================================================

SYNONYM_DICTIONARY = {
    # Kubernetes / Container ecosystem
    "k8s": ["kubernetes", "kube"],
    "kubernetes": ["k8s", "kube"],
    "docker": ["container runtime", "containerization"],
    "pod": ["kubernetes pod", "k8s pod"],

    # Game terminology (PokoPoko example)
    "더블폭탄": ["double bomb", "L자폭탄", "T자폭탄"],
    "클로버": ["clover", "하트", "heart", "stamina"],
    "체리": ["cherry", "코인", "coin"],
    "매치3": ["match-3", "match three", "3매치"],
    "4매치": ["match-4", "4 match", "4개 매치"],
    "5매치": ["match-5", "5 match", "5개 매치"],
    "폭탄": ["bomb", "explosion"],
    "블록": ["block", "tile"],

    # Cloud platforms
    "aws": ["amazon web services", "amazon cloud"],
    "gcp": ["google cloud platform", "google cloud"],
    "azure": ["microsoft azure", "ms azure"],

    # Add more domain-specific synonyms here
}


def get_synonyms(term: str) -> list:
    """
    Get synonyms for a given term

    Args:
        term: Input term (case-insensitive)

    Returns:
        List of synonym terms
    """
    normalized_term = term.lower().strip()
    return SYNONYM_DICTIONARY.get(normalized_term, [])


def is_synonym(term1: str, term2: str) -> bool:
    """
    Check if two terms are synonyms

    Args:
        term1: First term
        term2: Second term

    Returns:
        True if terms are synonyms
    """
    t1 = term1.lower().strip()
    t2 = term2.lower().strip()

    if t1 == t2:
        return True

    # Check if they share the same synonym group
    t1_syns = get_synonyms(t1)
    t2_syns = get_synonyms(t2)

    return (t2 in t1_syns) or (t1 in t2_syns) or bool(set(t1_syns) & set(t2_syns))


# ================================================================
# Backward Compatibility (Deprecated)
# ================================================================

def _deprecated_get_prompt_string(template_name: str) -> str:
    """
    [DEPRECATED] Use get_prompt() instead

    This function is kept for backward compatibility but will be removed in future versions.
    """
    import warnings
    warnings.warn(
        "Direct access to SYSTEM_PROMPT_* is deprecated. Use get_prompt() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_prompt(template_name)


# For backward compatibility, provide access to prompt strings
# These will load from files on first access
def __getattr__(name: str):
    """
    Dynamic attribute access for backward compatibility

    Allows: from src.core.rules.prompts import SYSTEM_PROMPT_TECHNICAL
    But warns about deprecation
    """
    if name == "SYSTEM_PROMPT_TECHNICAL":
        return _deprecated_get_prompt_string("technical")
    elif name == "SYSTEM_PROMPT_POKOPOKO":
        return _deprecated_get_prompt_string("pokopoko")
    elif name == "PROMPT_TEMPLATES":
        # Return a dict-like object that loads from files
        return {
            "technical": get_prompt("technical"),
            "pokopoko": get_prompt("pokopoko"),
        }
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
