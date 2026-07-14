from pathlib import Path


class CopyService:

    # ==========================================================================
    # Function: fn_read_asc_content
    #
    # Purpose:
    #     Read ASC text content for copy-to-clipboard workflow.
    #
    # Inputs:
    #     log_file: Selected ASC or BLF log file path.
    #
    # Outputs:
    #     tuple[str, str]: ASC file path and ASC text content.
    #
    # Called by:
    #     AnalysisController.fn_get_copy_content()
    #
    # Calls:
    #     CopyService._fn_resolve_asc_file()
    #     Path.read_text()
    #
    # Side Effects:
    #     Reads a text file from disk.
    #
    # Responsibility:
    #     Provide ASC file content for the GUI copy workflow.
    #
    # Does NOT:
    #     - Update GUI.
    #     - Write to clipboard.
    #     - Convert BLF to ASC.
    #     - Parse UDS transactions.
    #     - Export Excel.
    #
    # ==========================================================================
    def fn_read_asc_content(self, log_file: str) -> tuple[str, str]:
        """Read ASC text content from a selected log path.

        Args:
            log_file: Path selected in the GUI. It may be an ASC file or a BLF
                file whose converted ASC file already exists.

        Returns:
            A tuple containing the resolved ASC file path and file content.

        Raises:
            ValueError: If the file type is not ASC or BLF.
            FileNotFoundError: If the resolved ASC file does not exist.
        """
        asc_file = self._fn_resolve_asc_file(log_file)
        content = asc_file.read_text(encoding="utf-8", errors="ignore")

        return str(asc_file), content

    # ==========================================================================
    # Function: _fn_resolve_asc_file
    #
    # Purpose:
    #     Resolve the ASC file path used by the copy workflow.
    #
    # Inputs:
    #     log_file: Selected ASC or BLF log file path.
    #
    # Outputs:
    #     Path: Resolved ASC file path.
    #
    # Called by:
    #     CopyService.fn_read_asc_content()
    #
    # Calls:
    #     Path.with_suffix()
    #     Path.exists()
    #
    # Side Effects:
    #     Checks whether a file exists on disk.
    #
    # Responsibility:
    #     Map selected ASC/BLF path to the ASC text file to copy.
    #
    # Does NOT:
    #     - Convert BLF to ASC.
    #     - Read file content.
    #     - Update GUI.
    #     - Write to clipboard.
    #     - Export Excel.
    #
    # ==========================================================================
    def _fn_resolve_asc_file(self, log_file: str) -> Path:
        """Resolve selected log path to an existing ASC file.

        Args:
            log_file: Selected file path from the GUI.

        Returns:
            Path to an existing ASC file.

        Raises:
            ValueError: If no path is provided or the suffix is unsupported.
            FileNotFoundError: If the resolved ASC file does not exist.
        """
        if not log_file:
            raise ValueError("Please select a log file before copying.")

        asc_file = Path(log_file)

        if asc_file.suffix.lower() == ".blf":
            asc_file = asc_file.with_suffix(".asc")

        if asc_file.suffix.lower() != ".asc":
            raise ValueError("Copy only supports ASC text files.")

        if not asc_file.exists():
            raise FileNotFoundError(f"ASC file not found: {asc_file}")

        return asc_file
