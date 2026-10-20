from pathlib import Path

from core.log_parsers.base import BaseTextLogParser, read_text_header
from core.log_parsers.dsa_txt_parser import DSATextParser


# Register additional content-based TXT formats here.
TXT_PARSERS: list[BaseTextLogParser] = [DSATextParser()]


def detect_txt_parser(file_path: str | Path) -> BaseTextLogParser:
    header = read_text_header(file_path)
    if not header.strip():
        raise ValueError("TXT log is empty.")
    for parser in TXT_PARSERS:
        if parser.can_parse(header):
            return parser
    raise ValueError(
        "Unsupported TXT log format or invalid header. Expected DSA-TEXT "
        "(#!DSAVci.log and $Log.Format.String = DSA-TEXT) in the first 8192 characters."
    )
