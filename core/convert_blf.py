from pathlib import Path

import can

from core.blf_reader import (
    _fn_raw_blf_channel_to_logical_channel,
    get_blf_channels,
)


def blf_to_asc(blf_file):
    """
    Explicit legacy conversion utility. Not used by Log Analyzer.

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

    with can.BLFReader(blf_path) as reader:
        writer = can.ASCWriter(str(asc_file))
        try:
            for msg in reader:
                writer.on_message_received(msg)
        finally:
            writer.stop()

    return str(asc_file)
