"""
context_builder.py
Converts static analysis results into a compact structured summary
that can be sent to the LLM without hitting token limits.
Target size: ~2,500 tokens — well within a 3B model's context window.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from .static_analyzer import FileStats, ProjectLevelStats
from .dependency_graph import DependencyGraph
from .ai_detector import build_ai_profile
from utils.logger import get_logger

logger = get_logger("context_builder")


class ContextBuilder:
    def __init__(
        self,
        root_path: Path,
        file_stats: Dict[str, FileStats],
        graph: DependencyGraph,
        cycles: List[List[str]],
        coupling: Dict[str, Dict[str, int]],
        config: Dict[str, Any],
    ):
        self.root_path = root_path
        self.file_stats = file_stats
        self.graph = graph
        self.cycles = cycles
        self.coupling = coupling
        self.config = config

    def build(self) -> Dict[str, Any]:
        """Returns a structured dict summary of the project — compact enough for local LLM."""
        thresholds = self.config.get("thresholds", {}).get("god_mode", {})
        god_loc = thresholds.get("loc", 800)
        god_fan_in = thresholds.get("fan_in", 20)
        god_fan_out = thresholds.get("fan_out", 15)

        # ── File-level summary ────────────────────────────────────────────
        files_summary = []
        total_secrets = 0
        total_subprocesses = 0
        total_broad_excepts = 0
        total_print_calls = 0
        files_with_logging = 0
        files_with_retry = 0
        files_with_timeout = 0
        files_with_hardcoded_paths = 0
        god_mode_files = []
        all_hardcoded_paths: List[str] = []

        for module, stats in self.file_stats.items():
            coupling_info = self.coupling.get(module, {})
            fan_in = coupling_info.get("fan_in", 0)
            fan_out = coupling_info.get("fan_out", 0)

            is_god = (
                stats.loc > god_loc
                or fan_in > god_fan_in
                or fan_out > god_fan_out
            )
            if is_god:
                god_mode_files.append(module)

            total_secrets += len(stats.hardcoded_secrets)
            total_broad_excepts += stats.broad_except_count
            total_print_calls += stats.print_count
            if stats.has_subprocess_call:
                total_subprocesses += 1
            if stats.uses_logging:
                files_with_logging += 1
            if stats.has_retry_pattern:
                files_with_retry += 1
            if stats.has_timeout_pattern:
                files_with_timeout += 1
            if stats.has_hardcoded_path:
                files_with_hardcoded_paths += 1
                all_hardcoded_paths.extend(stats.hardcoded_paths)

            files_summary.append({
                "module": module,
                "loc": stats.loc,
                "classes": len(stats.classes),
                "functions": len(stats.functions),
                "cyclomatic_complexity": stats.cyclomatic_complexity,
                "fan_in": fan_in,
                "fan_out": fan_out,
                "broad_excepts": stats.broad_except_count,
                "secrets": len(stats.hardcoded_secrets),
                "subprocess": stats.has_subprocess_call,
                "print_calls": stats.print_count,
                "uses_logging": stats.uses_logging,
                "has_retry": stats.has_retry_pattern,
                "has_timeout": stats.has_timeout_pattern,
                "hardcoded_path": stats.has_hardcoded_path,
                "direct_llm_calls": len(stats.direct_llm_calls),
            })

        # Sort by LOC descending for quick human/LLM comprehension
        files_summary.sort(key=lambda x: x["loc"], reverse=True)

        # ── AI/ML profile ─────────────────────────────────────────────────
        ai_profile = build_ai_profile(self.file_stats)

        # ── Project-level signals ─────────────────────────────────────────
        project_stats = ProjectLevelStats(self.root_path).analyze()

        # ── Dependency cycles ─────────────────────────────────────────────
        cycles_summary = [" -> ".join(c) for c in self.cycles[:5]]  # cap at 5

        # ── Assemble ──────────────────────────────────────────────────────
        summary = {
            "project_name": self.root_path.name,
            "total_python_files": project_stats["total_python_files"],
            "total_loc": sum(s.loc for s in self.file_stats.values()),
            "project_flags": {
                "has_tests": project_stats["has_tests"],
                "test_file_count": project_stats["test_file_count"],
                "has_dockerfile": project_stats["has_dockerfile"],
                "has_requirements": project_stats["has_requirements"],
                "has_env_example": project_stats["has_env_example"],
                "has_ci_config": project_stats["has_ci_config"],
                "has_config_file": project_stats["has_config_file"],
            },
            "code_quality": {
                "total_hardcoded_secrets": total_secrets,
                "total_broad_excepts": total_broad_excepts,
                "total_print_calls": total_print_calls,
                "files_using_logging": files_with_logging,
                "files_with_retry": files_with_retry,
                "files_with_timeout": files_with_timeout,
                "files_with_subprocess": total_subprocesses,
                "files_with_hardcoded_paths": files_with_hardcoded_paths,
                "sample_hardcoded_paths": list(set(all_hardcoded_paths))[:3],
                "god_mode_files": god_mode_files,
                "circular_dependencies": len(self.cycles),
                "circular_dependency_examples": cycles_summary,
            },
            "ai_ml_profile": {
                "uses_llm": ai_profile["uses_llm"],
                "uses_rag": ai_profile["uses_rag"],
                "uses_embeddings": ai_profile["uses_embeddings"],
                "has_llm_abstraction": ai_profile["has_llm_abstraction"],
                "uses_resilience_library": ai_profile["uses_resilience"],
                "uses_structured_output": ai_profile["uses_structured_output"],
                "uses_observability": ai_profile["uses_observability"],
                "llm_libraries": ai_profile["llm_libs"],
                "rag_libraries": ai_profile["rag_libs"],
                "files_with_direct_llm_calls": ai_profile["files_with_direct_llm"],
                "total_prompt_strings_detected": ai_profile["total_prompt_count"],
            },
            "files": files_summary,
        }
        
        # Log context summary info
        logger.info(f"Context summary built:")
        logger.info(f"  Total LOC: {summary['total_loc']}")
        logger.info(f"  Python files: {summary['total_python_files']}")
        logger.info(f"  God-mode files: {len(god_mode_files)}")
        logger.info(f"  Circular dependencies: {len(self.cycles)}")
        logger.debug(f"  Code quality metrics: {summary['code_quality']}")
        logger.debug(f"  AI/ML profile: {summary['ai_ml_profile']}")

        return summary

    def to_compact_text(self) -> str:
        """Returns a compact JSON string of the summary (< 3000 tokens)."""
        data = self.build()
        return json.dumps(data, indent=2)
