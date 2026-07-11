from pathlib import Path

import pytest

from core.services.copy_service import CopyService


# ==========================================================================
# Function: test_read_asc_content_normal_case
#
# Purpose:
#     Verify CopyService reads ASC file content successfully.
#
# Inputs:
#     tmp_path: Pytest temporary directory fixture.
#
# Outputs:
#     None.
#
# Called by:
#     pytest
#
# Calls:
#     CopyService.fn_read_asc_content()
#
# Side Effects:
#     Creates a temporary ASC file in pytest temp directory.
#
# Responsibility:
#     Validate normal ASC copy content workflow.
#
# Does NOT:
#     - Update GUI.
#     - Write to clipboard.
#     - Parse UDS transactions.
#     - Export Excel.
#     - Modify project files.
#
# ==========================================================================
def test_read_asc_content_normal_case(tmp_path: Path) -> None:
    """Verify ASC file path and content are returned."""
    asc_file = tmp_path / "sample.asc"
    asc_file.write_text("date test\n1.000 CANFD 123 Rx d 8 01\n")

    service = CopyService()
    resolved_path, content = service.fn_read_asc_content(str(asc_file))

    assert resolved_path == str(asc_file)
    assert "CANFD" in content


# ==========================================================================
# Function: test_read_asc_content_from_blf_uses_matching_asc
#
# Purpose:
#     Verify BLF input resolves to an existing ASC file with the same name.
#
# Inputs:
#     tmp_path: Pytest temporary directory fixture.
#
# Outputs:
#     None.
#
# Called by:
#     pytest
#
# Calls:
#     CopyService.fn_read_asc_content()
#
# Side Effects:
#     Creates temporary BLF and ASC paths in pytest temp directory.
#
# Responsibility:
#     Validate BLF-to-existing-ASC copy workflow.
#
# Does NOT:
#     - Convert BLF to ASC.
#     - Update GUI.
#     - Write to clipboard.
#     - Parse UDS transactions.
#     - Export Excel.
#
# ==========================================================================
def test_read_asc_content_from_blf_uses_matching_asc(tmp_path: Path) -> None:
    """Verify BLF path maps to same-name ASC path."""
    blf_file = tmp_path / "sample.blf"
    asc_file = tmp_path / "sample.asc"
    blf_file.write_bytes(b"")
    asc_file.write_text("converted asc content")

    service = CopyService()
    resolved_path, content = service.fn_read_asc_content(str(blf_file))

    assert resolved_path == str(asc_file)
    assert content == "converted asc content"


# ==========================================================================
# Function: test_read_asc_content_rejects_unsupported_file
#
# Purpose:
#     Verify unsupported file suffix raises ValueError.
#
# Inputs:
#     tmp_path: Pytest temporary directory fixture.
#
# Outputs:
#     None.
#
# Called by:
#     pytest
#
# Calls:
#     CopyService.fn_read_asc_content()
#
# Side Effects:
#     None.
#
# Responsibility:
#     Validate invalid input handling for copy workflow.
#
# Does NOT:
#     - Update GUI.
#     - Write to clipboard.
#     - Parse UDS transactions.
#     - Export Excel.
#     - Modify runtime config.
#
# ==========================================================================
def test_read_asc_content_rejects_unsupported_file(tmp_path: Path) -> None:
    """Verify unsupported file types are rejected."""
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("not asc")

    service = CopyService()

    with pytest.raises(ValueError):
        service.fn_read_asc_content(str(txt_file))


# ==========================================================================
# Function: test_read_asc_content_missing_file
#
# Purpose:
#     Verify missing ASC file raises FileNotFoundError.
#
# Inputs:
#     tmp_path: Pytest temporary directory fixture.
#
# Outputs:
#     None.
#
# Called by:
#     pytest
#
# Calls:
#     CopyService.fn_read_asc_content()
#
# Side Effects:
#     None.
#
# Responsibility:
#     Validate missing file handling for copy workflow.
#
# Does NOT:
#     - Update GUI.
#     - Write to clipboard.
#     - Parse UDS transactions.
#     - Export Excel.
#     - Create output reports.
#
# ==========================================================================
def test_read_asc_content_missing_file(tmp_path: Path) -> None:
    """Verify missing ASC files are reported."""
    missing_file = tmp_path / "missing.asc"
    service = CopyService()

    with pytest.raises(FileNotFoundError):
        service.fn_read_asc_content(str(missing_file))
