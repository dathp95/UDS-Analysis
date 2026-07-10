from pathlib import Path

import can


def blf_to_asc(blf_file):
    """
    Convert BLF log to ASC.

    Parameters
    ----------
    blf_file : str

    Returns
    -------
    str
        ASC file path.
    """

    blf_path = Path(blf_file)

    asc_file = blf_path.with_suffix(".asc")

    reader = can.BLFReader(blf_path)

    writer = can.ASCWriter(str(asc_file))

    for msg in reader:

        writer.on_message_received(msg)

    writer.stop()

    print(f"[BLF] Convert : {blf_path.name}")

    print(f"[ASC] Output  : {asc_file}")

    return str(asc_file)

