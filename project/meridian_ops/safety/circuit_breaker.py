from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CircuitBreaker:
    """Stop calling a sick dependency after consecutive failures."""

    failure_threshold: int = 3
    cooldown_s: float = 30.0
    failures: int = 0
    opened_at: float | None = None

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def record_timeout(self, now: float) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = now

    def allow_call(self, now: float) -> bool:
        if self.opened_at is None:
            return True
        if now - self.opened_at >= self.cooldown_s:
            # Half-open: allow one probe. Success will close; timeout re-opens.
            return True
        return False