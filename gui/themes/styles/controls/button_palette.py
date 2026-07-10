from dataclasses import dataclass


@dataclass(frozen=True)
class ButtonPalette:

    background: str

    hover: str

    pressed: str

    text: str

    border: str