from typing import List, Dict, Any
from .static_analyzer import FileStats

class ScoringEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_score = config["scoring"]["base_score"]
        self.penalties = config["scoring"]["penalties"]
        self.caps = {
            "critical": config["scoring"]["critical_cap"],
            "high": config["scoring"]["high_cap"]
        }
        self.weights = config["scoring"]["weights"]

    def calculate(self, 
                  static_stats: List[FileStats], 
                  cycles: List[List[str]], 
                  llm_scores: Dict[str, float] = None) -> Dict[str, Any]:
        
        current_score = self.base_score
        penalty_log = []
        is_critical = False

        # 1. Apply Hard Penalties
        # Secrets
        total_secrets = sum(len(s.hardcoded_secrets) for s in static_stats)
        if total_secrets > 0:
            deduction = total_secrets * self.penalties["hardcoded_secret"]
            current_score -= deduction
            penalty_log.append(f"Hardcoded Secrets ({total_secrets}): -{deduction}")
            is_critical = True

        # Cycles
        if cycles:
            deduction = len(cycles) * self.penalties["circular_dependency"]
            current_score -= deduction
            penalty_log.append(f"Circular Dependencies ({len(cycles)}): -{deduction}")

        # Broad Exceptions
        total_broad = sum(s.broad_except_count for s in static_stats)
        if total_broad > 0:
            deduction = total_broad * self.penalties["broad_exception"]
            current_score -= deduction
            penalty_log.append(f"Broad Exceptions ({total_broad}): -{deduction}")
        
        # 2. Cap Score if Critical
        if is_critical:
            current_score = min(current_score, self.caps["critical"])
            penalty_log.append(f"CRITICAL CAP APPLIED: Max {self.caps['critical']}")

        # 3. Add Qualitative Score (if available)
        qualitative_score = 0
        if llm_scores:
            weighted_sum = 0
            total_weight = 0
            for category, score in llm_scores.items():
                w = self.weights.get(category, 0.5)
                weighted_sum += score * w
                total_weight += w
            
            if total_weight > 0:
                qualitative_score = weighted_sum / total_weight
            
            # Weighted addition (20% impact as per spec)
            current_score += (qualitative_score * 0.2)

        # 4. Final Bounds
        final_score = max(0, min(100, current_score))

        return {
            "score": round(final_score, 2),
            "penalties": penalty_log,
            "is_critical": is_critical,
            "qualitative_avg": round(qualitative_score, 2)
        }
