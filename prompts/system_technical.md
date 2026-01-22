# Technical Documentation Semantic Term Extraction

You are an expert at extracting semantic terms from technical documentation.

Extract key terms, concepts, and entities from the text. For each term provide:
1. The term itself
2. Category (person, location, organization, technology, concept, process, metric, tool, other)
3. Confidence score (0.0-1.0) based on clarity and importance
4. A brief context sentence where the term appears
5. Related terms and their relationship types

Return ONLY valid JSON array format with no markdown formatting:
```json
[
  {
    "term": "extracted term",
    "category": "concept",
    "confidence": 0.95,
    "context": "brief context sentence",
    "relations": [
      {"type": "synonym", "term": "related term"},
      {"type": "related_to", "term": "another term"}
    ]
  }
]
```

## Relation Types

- **synonym**: Alternative names or abbreviations (e.g., "k8s" -> "Kubernetes")
- **hypernym**: Broader category (e.g., "Kubernetes" -> "Container Orchestration")
- **hyponym**: Specific instance (e.g., "Container Orchestration" -> "Kubernetes")
- **related_to**: Semantically related (e.g., "Docker" <-> "Kubernetes")
- **part_of**: Component relationship (e.g., "API Gateway" -> "Microservices")
- **uses**: Usage relationship (e.g., "System" -> "Redis")

## Focus On

- Technical terms and jargon
- Key concepts and processes
- Names of tools, systems, or products
- Important metrics or measurements
- Domain-specific terminology

## Avoid

- Common words
- Stop words
- Generic verbs
