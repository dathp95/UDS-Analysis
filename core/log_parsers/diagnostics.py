from dataclasses import dataclass, field


@dataclass
class ParserDiagnostics:
    """One scan's file totals, kept separate from selected-channel/pipeline totals.

    Examples contain only line numbers and parser-owned descriptions, never
    source paths, raw lines, payloads, or untrusted display fields.
    """

    format_name: str = "DSA-TEXT"
    total_can_records: int = 0
    parsed_frames: int = 0
    malformed_frames: int = 0
    unsupported_frames: int = 0
    other_skipped_can_frames: int = 0
    non_can_lines: int = 0
    channels: list[int] = field(default_factory=list)
    frames_by_channel: dict[int, int] = field(default_factory=dict)
    selected_channel: int | None = None
    loaded_frames: int = 0
    pipeline_frames: int = 0
    declared_channel_count: int | None = None
    declared_channels: list[int] = field(default_factory=list)
    bus_types: dict[int, str] = field(default_factory=dict)
    baud_rates: dict[int, int] = field(default_factory=dict)
    timestamp_discontinuities: int = 0
    first_timestamp: float | None = None
    last_timestamp: float | None = None
    scan_complete: bool = False
    warnings: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

    @property
    def skipped_frames(self) -> int:
        return self.malformed_frames + self.unsupported_frames + self.other_skipped_can_frames

    @property
    def selected_channel_frames(self) -> int:
        return self.frames_by_channel.get(self.selected_channel, 0)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings or self.skipped_frames or self.timestamp_discontinuities)

    def reset(self, selected_channel: int | None = None) -> None:
        self.__dict__.update(ParserDiagnostics(selected_channel=selected_channel).__dict__)

    def add_example(self, line_number: int, description: str) -> None:
        if len(self.examples) < 5:
            self.examples.append(f"line {line_number}: {description}")

    def observe(self, message: dict, line_number: int) -> None:
        self.parsed_frames += 1
        channel = message["channel"]
        self.frames_by_channel[channel] = self.frames_by_channel.get(channel, 0) + 1
        timestamp = message["timestamp"]
        if self.last_timestamp is not None and timestamp < self.last_timestamp:
            self.timestamp_discontinuities += 1
            self.add_example(line_number, "Timestamp moved backwards; source order preserved")
        if self.first_timestamp is None:
            self.first_timestamp = timestamp
        self.last_timestamp = timestamp

    def finish(self) -> None:
        self.channels = sorted(self.frames_by_channel)
        self.scan_complete = True
        if self.skipped_frames:
            self.warnings.append(
                f"Skipped {self.skipped_frames} CAN records: {self.malformed_frames} malformed, "
                f"{self.unsupported_frames} unsupported, {self.other_skipped_can_frames} other. "
                "Some diagnostic transactions may be incomplete."
            )
        if ((self.declared_channel_count is not None and self.declared_channel_count != len(self.channels))
                or (self.declared_channels and self.declared_channels != self.channels)):
            self.warnings.append("DSA header channel metadata disagrees with observed CAN channels; using valid CAN records.")
        if self.timestamp_discontinuities:
            self.warnings.append(f"{self.timestamp_discontinuities} backwards timestamps; source order and time base preserved.")
