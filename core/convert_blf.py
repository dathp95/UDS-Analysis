from pathlib import Path

import can


def _fn_channel_value(value):
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_blf_channels(blf_file):
    channels = set()

    for msg in can.BLFReader(Path(blf_file)):
        channel = _fn_channel_value(
            getattr(msg, "channel", None)
        )

        if channel is not None:
            channels.add(channel)

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
