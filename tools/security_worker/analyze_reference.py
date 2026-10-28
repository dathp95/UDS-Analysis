"""Offline audit only; never loads a DLL or transmits CAN. Output contains no secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.can.security_reference import read_reference_workbook
from services.can.security_provider_gate import inspect_security_provider
from services.vehicle_service import VehicleService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook', type=Path)
    parser.add_argument('--vehicle', required=True)
    parser.add_argument('--ecu', required=True)
    parser.add_argument('--local-fixture', type=Path, help='Optional PRIVATE fixture, restricted to ignored output/.')
    args = parser.parse_args()
    try:
        if args.local_fixture is not None:
            fixture = args.local_fixture.resolve()
            if not fixture.is_relative_to((ROOT/'output').resolve()) or fixture == args.workbook.resolve():
                raise ValueError('Private fixtures must stay under output/ and cannot replace the workbook.')
        analysis = read_reference_workbook(args.workbook)
        status = inspect_security_provider(VehicleService(), args.vehicle, args.ecu)
        if args.local_fixture is not None:
            fixture.parent.mkdir(parents=True, exist_ok=True)
            vectors = [dict(ecu=v.ecu,session=v.session,subfunction=v.subfunction,
                            seed_time=v.seed_time,key_time=v.key_time,seed_hex=v.seed.hex(),key_hex=v.key.hex())
                       for v in analysis.vectors if v.ecu == args.ecu]
            # Explicit offline fixture storage only. The worker never writes secrets to disk.
            fixture.write_text(json.dumps(vectors),encoding='utf-8')
        summary = analysis.summary()
        summary.update(workbook_sha256=hashlib.sha256(args.workbook.read_bytes()).hexdigest(),
                       dll_sha256=status.sha256,dll_size=status.size_bytes,
                       provider_status=status.readiness.value,live_enabled=status.live_enabled,
                       native_vectors_compared=0,offline_verification='BLOCKED: no verified native ABI/provider')
        print(json.dumps(summary,indent=2))
        return 0
    except Exception:
        # No raw cell contents or sensitive exceptions in CLI output.
        print('Offline audit failed: check the workbook schema and saved Vehicle/ECU configuration.',file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
