from pathlib import Path

import can


def _fn_raw_blf_channel_to_logical_channel(value):
    if value is None:
        return None

    try:
        raw_blf_channel = int(value)
    except (TypeError, ValueError):
        return None

    # python-can BLFReader exposes CANoe channels as zero-based values.
    return raw_blf_channel + 1


def get_blf_channels(blf_file):
    channels = set()

    for msg in can.BLFReader(Path(blf_file)):
        logical_channel = _fn_raw_blf_channel_to_logical_channel(
            getattr(msg, "channel", None)
        )

        if logical_channel is not None:
            channels.add(logical_channel)

    return sorted(channels)


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

    return str(asc_file)
