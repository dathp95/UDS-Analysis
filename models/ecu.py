"""
ecu.py

ECU data model for Vehicle Configuration.

This class represents a single ECU and only stores configuration data.
JSON loading/saving is handled by VehicleRepository.
"""

from dataclasses import dataclass, field


@dataclass
class ECU:
    """Represents a single ECU configuration."""

    # General
    name: str
    request_id: str = ""
    response_id: str = ""
    functional_id: str = ""

    # Optional
    aliases: list[str] = field(default_factory=list)

    # External resources
    resources: dict[str, str] = field(
        default_factory=lambda: {
            "dll": "",
            "dbc": "",
            "odx": "",
            "dtc": "",
            "request_library": "",
        }
    )

    # Diagnostic quick requests (V3)
    quick_requests: list = field(default_factory=list)