from dataclasses import dataclass
from uuid import uuid4

from services.seed_key_provider import (
    SeedKeyRequest,
    SeedKeyProvider,
    MockSeedKeyProvider,
)

from services.can.security_seed_parser import (
    parse_security_seed,
)


@dataclass(frozen=True)
class SecurityKeyResult:
    vehicle: str
    ecu: str
    level: int
    key: bytes
    mock_only: bool = True

    def __repr__(self):
        return (
            f"SecurityKeyResult("
            f"vehicle={self.vehicle!r}, "
            f"ecu={self.ecu!r}, "
            f"level={self.level}, "
            f"key_length={len(self.key)}, "
            f"mock_only={self.mock_only})"
        )


class SecurityKeyService:

    def __init__(
        self,
        provider: SeedKeyProvider,
    ):
        self.provider = provider

    def calculate_from_response(
        self,
        *,
        vehicle: str,
        ecu: str,
        request_payload: bytes,
        response_payload: bytes,
        output_size: int,
    ) -> SecurityKeyResult:

        parsed = parse_security_seed(
            request_payload,
            response_payload,
        )

        request = SeedKeyRequest(
            request_id=uuid4().hex,
            vehicle=vehicle,
            ecu=ecu,
            level=parsed.level,
            seed=parsed.seed,
            output_size=output_size,
            timeout_s=1.0,
        )

        result = self.provider.calculate(
            request
        )

        if result.request_id != request.request_id:
            raise ValueError(
                "Seed-Key provider response mismatch."
            )

        if not result.mock_only:
            raise ValueError(
                "Real provider requires a separately "
                "validated DLL integration."
            )

        return SecurityKeyResult(
            vehicle=vehicle,
            ecu=ecu,
            level=parsed.level,
            key=result.key,
            mock_only=True,
        )