from pathlib import Path
import re

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog, QMessageBox


class CanWorkspaceController(QObject):
    """Sequence document actions and view preferences; no ECU or transport store."""
    def __init__(self, sidebar, panel, repository, store, parent=None):
        super().__init__(parent)
        self.sidebar, self.panel, self.repository, self.store = sidebar, panel, repository, store
        self.source = None
        sidebar.sequence_open_requested.connect(self.open_source)
        panel.load_requested.connect(self.browse_source)
        panel.save_requested.connect(self.save_sequence)
        panel.sequence_modified.connect(self._modified)
        panel.vehicle_changed.connect(self._vehicle_changed)

    def _modified(self, case):
        self.panel.title.setText(case.name + " *")

    def _allow_replace(self):
        if not self.panel.fn_is_dirty():
            return True
        answer = QMessageBox.question(self.panel, "Unsaved sequence", "Save changes before opening another sequence?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)
        if answer == QMessageBox.Cancel:
            return False
        return bool(self.save_sequence()) if answer == QMessageBox.Save else True

    def browse_source(self):
        path, _ = QFileDialog.getOpenFileName(self.panel, "Load Diagnostic Sequence", "", "Sequences (*.diag *.json)")
        if path:
            self.open_source(path, force=True)

    def open_source(self, source_id, *, persist=True, force=False):
        try:
            path = Path(source_id).resolve()
            if self.source == path and not force:
                return True
            case = self.repository.fn_load_sequence(path)
        except (OSError, ValueError) as error:
            self.panel.show_notice(f"{source_id}: {error}")
            self.sidebar.mark_opened(str(self.source) if self.source else "", persist=False)
            return False
        if not self._allow_replace():
            self.sidebar.mark_opened(str(self.source) if self.source else "", persist=False)
            return False
        self.source = path
        self.panel.fn_load_sequence(case)
        chosen = self.store.load().vehicles.get(str(path), "")
        self.panel.fn_refresh_vehicles(chosen)
        if hasattr(self.repository, 'register_source'):
            self.repository.register_source(path)
        self.sidebar.fn_refresh_sequences()
        self.sidebar.mark_opened(str(path), persist=persist)
        if path.suffix.lower() == ".diag":
            self.panel.show_notice("Imported .diag is read-only. Save As JSON excludes external IDs, DLL paths and execution rules.")
        if case.steps:
            self.panel._select_row(0)
        return True

    def restore(self):
        selected = self.store.load().selected_id
        if selected:
            self.open_source(selected, persist=False)

    def save_sequence(self, path=None, *, overwrite=False):
        case = self.panel.fn_current_sequence()
        if case is None:
            self.panel.show_notice("No diagnostic sequence to save.")
            return None
        if path is None:
            if self.source is not None and self.source.suffix.lower() == '.json':
                path = self.source
            else:
                name = re.sub(r'[<>:"/\\|?*]', '_', case.name) or "sequence"
                path, _ = QFileDialog.getSaveFileName(self.panel, "Save As V-CODE Sequence (.json)",
                           str(self.repository.root / f"{name}.json"), "V-CODE Sequence (*.json)")
                if not path:
                    return None
                overwrite = True  # Native file dialog confirms existing destinations.
        destination = Path(path).resolve()
        try:
            if destination.suffix.lower() != '.json':
                raise ValueError("Save As must use .json; .diag sources are never overwritten.")
            if destination.exists() and destination != self.source and not overwrite:
                raise FileExistsError("Destination already exists. Choose a different file or confirm overwrite in Save As.")
            result = self.repository.fn_save_sequence(case, destination)
        except (OSError, ValueError) as error:
            self.panel.show_notice(f"Cannot save sequence: {error}")
            return None
        self.source = destination
        self.panel.mark_saved()
        if hasattr(self.repository, 'register_source'):
            self.repository.register_source(destination)
        self.sidebar.fn_refresh_sequences()
        self.sidebar.mark_opened(str(destination))
        self._vehicle_changed(self.panel.fn_current_vehicle())
        self.panel.show_notice("Sequence saved.")
        return result

    def _vehicle_changed(self, name):
        if self.source is not None:
            try:
                self.store.save_vehicle(str(self.source), name)
            except OSError as error:
                self.panel.show_notice(f"Cannot save Vehicle view preference: {error}")

    def refresh_vehicles(self, changed_name=""):
        self.panel.fn_refresh_vehicles()
