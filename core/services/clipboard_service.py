from pathlib import Path


class ClipboardService:

    # ==========================================
    # Public
    # ==========================================

    def fn_read_asc_content(
        self,
        log_file: str,
    ):
        """
        Read ASC log content.

        Parameters
        ----------
        log_file : str

        Returns
        -------
        tuple[Path, str]
            ASC file path and content.
        """

        if not log_file:

            raise ValueError(
                "Please select a log file."
            )

        asc_file = Path(log_file)

        if asc_file.suffix.lower() == ".blf":

            asc_file = asc_file.with_suffix(".asc")

        if not asc_file.exists():

            raise FileNotFoundError(
                f"ASC file not found:\n{asc_file}"
            )

        content = asc_file.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        return asc_file, content