"""Explicit connection configuration, never inferred from a diagnostic request."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchAuthorizationContext:
    context_id: str
    authorized: bool = False

    def __post_init__(self):
        if not isinstance(self.context_id,str) or not self.context_id.strip() or len(self.context_id)>128:
            raise ValueError('A named test-bench authorization context is required.')
        if not isinstance(self.authorized,bool):
            raise ValueError('Bench authorization must be explicit.')
