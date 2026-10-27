
from dataclasses import dataclass
from pathlib import Path
import struct


class DLLInspectionError(ValueError):
    pass


@dataclass(frozen=True)
class DLLInformation:
    path: Path
    architecture: str
    machine: int
    size_bytes: int


PE_MACHINES = {
    0x014C: "x86 (32-bit)",
    0x8664: "x64 (64-bit)",
    0xAA64: "ARM64",
}


def inspect_dll(path: str | Path) -> DLLInformation:
    """
    Inspect Windows PE headers without loading or
    executing the DLL.
    """
    source = Path(path).resolve()

    if not source.is_file():
        raise DLLInspectionError(
            "DLL file does not exist."
        )

    if source.suffix.lower() != ".dll":
        raise DLLInspectionError(
            "Selected file is not a DLL."
        )

    size = source.stat().st_size

    if size < 64:
        raise DLLInspectionError(
            "Invalid PE header."
        )

    with source.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise DLLInspectionError(
                "Missing MZ signature."
            )

        stream.seek(0x3C)
        offset_data = stream.read(4)

        if len(offset_data) != 4:
            raise DLLInspectionError(
                "Invalid PE offset."
            )

        pe_offset = struct.unpack(
            "<I", offset_data
        )[0]

        if pe_offset > size - 24:
            raise DLLInspectionError(
                "PE header outside file."
            )

        stream.seek(pe_offset)

        if stream.read(4) != b"PE\x00\x00":
            raise DLLInspectionError(
                "Missing PE signature."
            )

        machine_data = stream.read(2)
        machine = struct.unpack(
            "<H", machine_data
        )[0]

        characteristics_offset = pe_offset + 4 + 18
        stream.seek(characteristics_offset)
        characteristics = struct.unpack(
            "<H", stream.read(2)
        )[0]

        if not characteristics & 0x2000:
            raise DLLInspectionError(
                "PE file is not marked as a DLL."
            )

    return DLLInformation(
        path=source,
        architecture=PE_MACHINES.get(
            machine,
            f"Unknown (0x{machine:04X})",
        ),
        machine=machine,
        size_bytes=size,
    )
