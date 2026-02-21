from typing import List, Dict, Any
from pathlib import Path
from .static_analyzer import FileStats

class ContextRanker:
    def __init__(self, config: Dict[str, Any]):
        self.weights = {
            "centrality": 0.4,
            "ai_usage": 0.3,
            "loc": 0.2,
            "config": 0.1
        }
        
    def rank_files(self, 
                   file_stats: Dict[str, FileStats], 
                   centrality_metrics: Dict[str, Dict[str, int]]) -> List[str]:
        """
        Returns a list of file paths (module names) sorted by importance.
        """
        scores = {}
        
        # Normalize metrics for fair comparison
        max_fan_in = max((m["fan_in"] for m in centrality_metrics.values()), default=1)
        max_loc = max((s.loc for s in file_stats.values()), default=1)

        for module, stats in file_stats.items():
            metrics = centrality_metrics.get(module, {"fan_in": 0})
            
            # Scores
            s_centrality = metrics["fan_in"] / max_fan_in
            s_ai = 1.0 if (stats.imports and "openai" in str(stats.imports)) else 0.0 # simplified check
            s_loc = min(stats.loc / max_loc, 1.0) # Cap at 1.0
            s_config = 1.0 if "config" in module.lower() or "settings" in module.lower() else 0.0
            
            # Weighted Sum
            final_score = (
                (s_centrality * self.weights["centrality"]) +
                (s_ai * self.weights["ai_usage"]) +
                (s_loc * self.weights["loc"]) +
                (s_config * self.weights["config"])
            )
            scores[module] = final_score

        # Sort descending
        return sorted(scores, key=scores.get, reverse=True)
