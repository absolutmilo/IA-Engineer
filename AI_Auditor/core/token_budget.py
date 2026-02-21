from typing import List

class TokenBudget:
    def __init__(self, max_tokens: int = 120000):
        self.max_tokens = max_tokens
        self.current_usage = 0

    def estimate(self, text: str) -> int:
        # Simple heuristic: 1 token ~= 4 chars
        return len(text) // 4

    def fits(self, text: str) -> bool:
        return (self.current_usage + self.estimate(text)) <= self.max_tokens

    def consume(self, text: str):
        self.current_usage += self.estimate(text)

    def reset(self):
        self.current_usage = 0
