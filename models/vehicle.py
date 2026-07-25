"""
vehicle.py

Vehicle data model for Vehicle Configuration.

A Vehicle contains multiple ECU configurations.
JSON loading/saving is handled by VehicleRepository.
"""

from dataclasses import dataclass, field

from models.ecu import ECU


@dataclass
class Vehicle:
    """Represents a vehicle package."""

    # General
    name: str
    manufacturer: str = ""
    version: str = "1.0.0"
    description: str = ""

    # ECU collection
    ecus: list[ECU] = field(default_factory=list)