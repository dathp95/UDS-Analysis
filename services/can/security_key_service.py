from dataclasses import dataclass
from uuid import uuid4

from services.seed_key_provider import (
    SeedKeyRequest,
    SeedKeyProvider,
    MockSeedKeyProvider,
    encode_request,
    SeedKeyResponse,
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
        dll_path: str = "",
        variant: str = "",
        cancel=None,
    ) -> SecurityKeyResult:

        parsed = parse_security_seed(
            request_payload,
            response_payload,
            allow_l2=True,
        )

        request = SeedKeyRequest(
            request_id=uuid4().hex,
            vehicle=vehicle,
            ecu=ecu,
            level=parsed.level,
            seed=parsed.seed,
            output_size=output_size,
            timeout_s=1.0,
            dll_path=dll_path,
            variant=variant,
        )

        encode_request(request)  # Validate the contract even for injected providers.
        result = self.provider.calculate(
            request, cancel=cancel
        )

        if (not isinstance(result, SeedKeyResponse) or result.request_id != request.request_id or not isinstance(result.key, bytes)
                or len(result.key) != request.output_size):
            raise ValueError(
                "Seed-Key provider response mismatch."
            )

        if not dll_path and result.mock_only is not True:
            raise ValueError(
                "Real provider requires a separately "
                "validated DLL integration."
            )

        return SecurityKeyResult(
            vehicle=vehicle,
            ecu=ecu,
            level=parsed.level,
            key=result.key,
            mock_only=result.mock_only,
        )
