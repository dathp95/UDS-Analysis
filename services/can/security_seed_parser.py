from dataclasses import dataclass
from core.diagnostic_request import SECURITY_LEVELS, is_security_seed_payload


class SecuritySeedError(ValueError):
    pass


@dataclass(frozen=True)
class SecuritySeed:
    level: int
    seed: bytes
    subfunction: int = 1

    def __repr__(self):
        return (
            f"SecuritySeed(level={self.level}, "
            f"subfunction=0x{self.subfunction:02X}, "
            f"seed_length={len(self.seed)})"
        )


def parse_security_seed(
    request_payload: bytes,
    response_payload: bytes,
    *,
    allow_l2: bool = False,
) -> SecuritySeed:
    """
    Parse UDS SecurityAccess requestSeed response.

    Supports 27 01, 27 03, 27 05, 27 07.
    """
    if not is_security_seed_payload(request_payload):
        raise SecuritySeedError(
            "SecurityAccess requires a valid subfunction in SECURITY_LEVELS (27 01, 27 03, 27 05, 27 07)."
        )

    if not isinstance(response_payload, bytes):
        raise SecuritySeedError(
            "Response must be bytes."
        )

    subfunc = request_payload[1]
    if not allow_l2 and subfunc != 0x01:
        raise SecuritySeedError(
            f"SecurityAccess subfunction 0x{subfunc:02X} requires allow_l2/multi-level flag."
        )

    if (
        len(response_payload) >= 3
        and response_payload[:2] == b"\x7F\x27"
    ):
        raise SecuritySeedError(
            f"ECU rejected SecurityAccess: "
            f"NRC 0x{response_payload[2]:02X}"
        )

    if len(response_payload) < 3:
        raise SecuritySeedError(
            "SecurityAccess response has no seed."
        )

    expected_prefix = bytes([0x67, subfunc])
    if response_payload[:2] != expected_prefix:
        raise SecuritySeedError(
            "Unexpected SecurityAccess response."
        )

    seed = response_payload[2:]

    if len(seed) > 64:
        raise SecuritySeedError(
            "Seed exceeds provider size limit."
        )

    return SecuritySeed(
        level=SECURITY_LEVELS[subfunc]["level"],
        seed=seed,
        subfunction=subfunc,
    )
