from dataclasses import dataclass


class SecuritySeedError(ValueError):
    pass


@dataclass(frozen=True)
class SecuritySeed:
    level: int
    seed: bytes

    def __repr__(self):
        return (
            f"SecuritySeed(level={self.level}, "
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

    Example:
        Request : 27 01
        Response: 67 01 AA BB CC DD
        Seed: AA BB CC DD
    """

    if request_payload == b"\x27\x03" and not allow_l2:
        raise SecuritySeedError(
            "Only 27 01 is supported."
        )

    if request_payload not in (b"\x27\x01", b"\x27\x03"):
        raise SecuritySeedError(
            "Only 27 01 and 27 03 are supported."
        )

    if not isinstance(response_payload, bytes):
        raise SecuritySeedError(
            "Response must be bytes."
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

    expected_prefix = bytes([0x67, request_payload[1]])
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
        level=request_payload[1],
        seed=seed,
    )
