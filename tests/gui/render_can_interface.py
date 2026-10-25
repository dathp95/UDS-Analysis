"""Optional deterministic UI QA renderer. No hardware, frames or persistent user data.

python -m tests.gui.render_can_interface [--scale 1.5]
"""
import argparse
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scale', type=float, default=1.0)
    options = parser.parse_args()
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['QT_SCALE_FACTOR'] = str(options.scale)
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtGui import QFontDatabase, QFont
    from PySide6.QtWidgets import QApplication
    from config.paths import PROJECT_ROOT
    from gui.tabs.can_interface_tab import CANInterfaceTab
    from gui.themes.theme import ThemeType
    from gui.themes.theme_manager import ThemeManager
    from repositories.can_interface_ui_store import CanInterfaceUiStore
    from repositories.can_sequence_repository import CanSequenceRepository
    from models.vehicle import Vehicle
    from models.ecu import ECU

    app = QApplication([])
    for filename in ('segoeui.ttf', 'segoeuib.ttf', 'consola.ttf', 'seguisym.ttf'):
        QFontDatabase.addApplicationFont(f'C:/Windows/Fonts/{filename}')
    print('Font families available:', len(QFontDatabase.families()))
    app.setFont(QFont('Segoe UI', 9))
    root = Path(__file__).parents[1] / 'fixtures' / 'can_interface'
    output = PROJECT_ROOT / 'output' / 'qa_can_m03'
    output.mkdir(parents=True, exist_ok=True)
    vehicle = Vehicle('SYNTHETIC BENCH', ecus=[ECU(f'TEST_ECU_{i:02}') for i in range(1, 17)])
    with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
        tab = CANInterfaceTab(vehicle_service=SimpleNamespace(list_vehicles=lambda: [vehicle.name], load_vehicle=lambda _: vehicle),
                              sequence_repository=CanSequenceRepository(root), ui_store=CanInterfaceUiStore(Path(directory) / 'prefs'))
        tab.workspace_controller.open_source(root / '0002.READ VIN(1).diag', persist=False)
        tab.sequence_table.vehicle_selector.fn_set_vehicle(vehicle.name)
        for mode in (ThemeType.LIGHT, ThemeType.DARK):
            ThemeManager.fn_set_theme(mode)
            tab.fn_refresh_theme()
            for width, height in ((1600, 900), (1366, 768)):
                tab.resize(width, height)
                tab.show()
                app.processEvents()
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
                app.processEvents()
                name = f'{mode.name.lower()}_{width}x{height}_{int(options.scale * 100)}.png'
                tab.grab().save(str(output / name))
                print(name, 'actual=', tab.size().toTuple(), 'main=', tab.main_splitter.sizes(),
                      'right=', tab.right_splitter.sizes(), 'bottom=', tab.bottom_splitter.sizes())
        tab.close()
        app.processEvents()


if __name__ == '__main__':
    main()
