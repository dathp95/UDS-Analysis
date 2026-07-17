"""
license/paths.py

Common paths used by the License System.
"""

from pathlib import Path

# Folder: license/
LICENSE_DIR = Path(__file__).resolve().parent

# Public key
PUBLIC_KEY_PATH = LICENSE_DIR / "public.pem"

# Default license file
LICENSE_FILE_PATH = LICENSE_DIR / "license.lic"