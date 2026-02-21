import re
from typing import List, Dict, Any
from .static_analyzer import FileStats


class AIDetector:
    def __init__(self):
        self.ai_libraries = {
            "openai", "anthropic", "google.generativeai", "ollama",
            "langchain", "llama_index", "transformers", "cohere", "mistralai"
        }
        self.rag_libraries = {
            "qdrant_client", "chromadb", "faiss", "pinecone",
            "weaviate", "milvus", "lancedb", "elasticsearch"
        }
        self.embedding_libraries = {
            "sentence_transformers", "fastembed", "tiktoken"
        }
        self.resilience_libraries = {"tenacity", "backoff", "retry"}
        self.structured_output_libs = {"instructor", "outlines", "guidance"}
        self.observability_libs = {"prometheus_client", "opentelemetry", "datadog"}

        self._prompt_patterns = [
            re.compile(r"you are a", re.IGNORECASE),
            re.compile(r"system\s*prompt", re.IGNORECASE),
            re.compile(r"f['\"].*\{context\}.*['\"]", re.IGNORECASE),
            re.compile(r"f['\"].*\{query\}.*['\"]", re.IGNORECASE),
        ]

    def detect(self, stats: FileStats, source_code: str = "") -> Dict[str, Any]:
        findings: Dict[str, Any] = {
            "uses_llm": False,
            "uses_rag": False,
            "uses_embeddings": False,
            "uses_resilience": False,
            "uses_structured_output": False,
            "uses_observability": False,
            "direct_api_call": False,
            "has_llm_abstraction": False,
            "prompt_count": 0,
            "llm_libs": [],
            "rag_libs": [],
        }

        for imp in stats.imports:
            base = imp.split(".")[0]
            if base in self.ai_libraries:
                findings["uses_llm"] = True
                findings["llm_libs"].append(base)
            if base in self.rag_libraries:
                findings["uses_rag"] = True
                findings["rag_libs"].append(base)
            if base in self.embedding_libraries:
                findings["uses_embeddings"] = True
            if base in self.resilience_libraries:
                findings["uses_resilience"] = True
            if base in self.structured_output_libs:
                findings["uses_structured_output"] = True
            if base in self.observability_libs:
                findings["uses_observability"] = True

        # Direct API call: using LLM lib without an abstraction wrapper
        if "openai" in stats.imports or "ollama" in stats.imports or "anthropic" in stats.imports:
            findings["direct_api_call"] = True

        # Abstraction: a class that wraps LLM calls (e.g., LLMClient, ModelProvider)
        abstraction_names = {"llmclient", "llmprovider", "modelclient", "aigateway",
                              "llmgateway", "chatclient", "basemodel", "llmwrapper"}
        for cls in stats.classes:
            if cls.lower() in abstraction_names:
                findings["has_llm_abstraction"] = True

        # Count prompt patterns in source
        if source_code:
            for pat in self._prompt_patterns:
                findings["prompt_count"] += len(pat.findall(source_code))

        return findings


def build_ai_profile(all_file_stats: Dict[str, FileStats],
                     all_source_codes: Dict[str, str] = None) -> Dict[str, Any]:
    """Aggregate AI detection across all project files."""
    detector = AIDetector()
    all_source_codes = all_source_codes or {}

    profile: Dict[str, Any] = {
        "uses_llm": False,
        "uses_rag": False,
        "uses_embeddings": False,
        "uses_resilience": False,
        "uses_structured_output": False,
        "uses_observability": False,
        "has_llm_abstraction": False,
        "total_direct_api_calls": 0,
        "total_prompt_count": 0,
        "llm_libs": set(),
        "rag_libs": set(),
        "files_with_direct_llm": [],
    }

    for module, stats in all_file_stats.items():
        src = all_source_codes.get(module, "")
        result = detector.detect(stats, src)

        profile["uses_llm"] = profile["uses_llm"] or result["uses_llm"]
        profile["uses_rag"] = profile["uses_rag"] or result["uses_rag"]
        profile["uses_embeddings"] = profile["uses_embeddings"] or result["uses_embeddings"]
        profile["uses_resilience"] = profile["uses_resilience"] or result["uses_resilience"]
        profile["uses_structured_output"] = profile["uses_structured_output"] or result["uses_structured_output"]
        profile["uses_observability"] = profile["uses_observability"] or result["uses_observability"]
        profile["has_llm_abstraction"] = profile["has_llm_abstraction"] or result["has_llm_abstraction"]
        profile["total_prompt_count"] += result["prompt_count"]
        profile["llm_libs"].update(result["llm_libs"])
        profile["rag_libs"].update(result["rag_libs"])

        if result["direct_api_call"]:
            profile["total_direct_api_calls"] += 1
            profile["files_with_direct_llm"].append(module)

    profile["llm_libs"] = list(profile["llm_libs"])
    profile["rag_libs"] = list(profile["rag_libs"])

    return profile
