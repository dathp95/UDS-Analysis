import os
import subprocess
import sys
from pathlib import Path


def ensure_start_menu_shortcut() -> None:
    if sys.platform != "win32":
        return

    # Chỉ tạo shortcut cho bản release
    if not getattr(sys, "frozen", False):
        return

    exe_path = Path(sys.executable).resolve()

    appdata = os.environ.get("APPDATA")
    if not appdata:
        return

    shortcut_path = (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "V-CODE.lnk"
    )

    # Nếu đã tồn tại thì không cần tạo lại
    if shortcut_path.exists():
        return

    exe = str(exe_path).replace("'", "''")
    shortcut = str(shortcut_path).replace("'", "''")

    ps_script = f"""
$exe = '{exe}'
$shortcutPath = '{shortcut}'

$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($shortcutPath)

$link.TargetPath = $exe
$link.WorkingDirectory = Split-Path $exe
$link.IconLocation = "$exe,0"
$link.Description = "V-CODE EEIV Diagnostic Tool"

$link.Save()
"""

    try:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps_script,
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
    except Exception:
        # Shortcut không phải chức năng critical của V-CODE.
        # Nếu Windows policy chặn thì app vẫn phải chạy bình thường.
        pass