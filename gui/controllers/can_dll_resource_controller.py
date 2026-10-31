"""Read-only resource presentation; never authorizes or executes diagnostics."""
from html import escape
from pathlib import Path

from PySide6.QtCore import QObject

from core.dll_resource import DllResourceStatus
from services.ecu_dll_resource import resolve_ecu_dll_resource


class CanDllResourceController(QObject):
    def __init__(self, panel, view, parent=None):
        super().__init__(parent)
        self.panel, self.view = panel, view
        self.metadata = None
        self._selection = None
        for signal in (panel.row_selected, panel.sequence_modified):
            signal.connect(self.refresh)
        for signal in (panel.document_changed, panel.vehicle_configuration_changed, panel.vehicle_resources_changed):
            signal.connect(self._invalidate)
        self.refresh()

    def _invalidate(self):
        self._selection = None
        self.refresh()

    def refresh(self, *_):
        step = self.panel.step_for_id(self.panel.selected_step_id())
        vehicle = self.panel.fn_current_vehicle()
        selection = (vehicle, step.ecu if step else '')
        if selection == self._selection:
            return
        self._selection = selection
        if step is None or not vehicle:
            self.metadata = None
            self.view.dll_status.setText('DLL: select a diagnostic row and Vehicle.')
            self.view.dll_status.setToolTip('Security execution disabled.')
            return
        metadata = resolve_ecu_dll_resource(self.panel._vehicle_service, vehicle, step.ecu)
        self.metadata = metadata
        text = metadata.message
        worker_path = Path(__file__).resolve().parents[2] / 'build' / 'security_worker' / 'SeedKeyWorker.x86.exe'
        worker_ready = worker_path.is_file() or Path('build/security_worker/SeedKeyWorker.x86.exe').is_file()
        if metadata.status == DllResourceStatus.METADATA_AVAILABLE:
            text = f'DLL configured ({metadata.machine}); Security Access ready.'
        elif metadata.status == DllResourceStatus.ARCH_UNSUPPORTED and metadata.machine == 'x86':
            if worker_ready:
                text = f'DLL configured ({metadata.machine}); ready via 32-bit helper.'
            else:
                text = 'DLL incompatible: x86 requires a 32-bit helper.'
        self.view.dll_status.setText(text)
        status_note = ('32-bit helper worker ready for Auto Security Access.' if worker_ready
                       else 'Static metadata only; ABI unverified. Security execution disabled.')
        details = [metadata.message, metadata.filename, metadata.machine,
                   f'{metadata.bits}-bit' if metadata.bits else '', *metadata.exports[:16],
                   status_note]
        self.view.dll_status.setToolTip('<br>'.join(escape(part) for part in details if part))
