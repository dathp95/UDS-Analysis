from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiagnosticExecutionSettings:
    loop: int = 1
    command_delay_ms: int = 100


@dataclass(frozen=True)
class DiagnosticStep:
    step: int
    sequence_name: str
    ecu: str
    request: str
    delay_ms: int | None = 100
    repeat: int = 1
    expected_response: str = ""
    match: str = "prefix"
    comment: str = ""


@dataclass(frozen=True)
class DiagnosticTestCase:
    schema_version: int
    name: str
    description: str
    enabled: bool
    steps: list[DiagnosticStep] = field(default_factory=list)
    execution: DiagnosticExecutionSettings = field(
        default_factory=DiagnosticExecutionSettings
    )
