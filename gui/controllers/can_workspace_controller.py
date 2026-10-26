from pathlib import Path
import re
from uuid import uuid4
from dataclasses import replace

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QDialog
from core.diagnostic_sequence import DiagnosticTestCase
from core.vehicle_dll_paths import safe_component
from gui.dialogs.sequence_exchange_dialog import SequenceExchangeDialog


class CanWorkspaceController(QObject):
    """Sequence document actions and view preferences; no ECU or transport store."""
    def __init__(self, sidebar, panel, repository, store, parent=None):
        super().__init__(parent)
        self.sidebar, self.panel, self.repository, self.store = sidebar, panel, repository, store
        self.source = None
        self.document_id = None
        sidebar.sequence_open_requested.connect(self.open_source)
        panel.load_requested.connect(self.browse_source)
        panel.save_requested.connect(self.save_sequence)
        panel.sequence_modified.connect(self._modified)
        panel.vehicle_changed.connect(self._vehicle_changed)
        panel.document_changed.connect(self._sync_actions)
        sidebar.add_requested.connect(self.add_sequence)
        sidebar.import_requested.connect(self.import_sequence)
        sidebar.export_requested.connect(self.export_sequence)
        sidebar.save_requested.connect(lambda: self.save_sequence())
        self._sync_actions()

    def _modified(self, case):
        if self.document_id is None:
            self.document_id = 'draft:' + uuid4().hex
            self.sidebar.add_draft(self.document_id, case)
        self.panel.title.setText(case.name + " *")
        self.sidebar.update_document_model(self.document_id, case)
        self.sidebar.set_document_dirty(self.document_id, True)
        self._sync_actions()

    def _sync_actions(self):
        case = self.panel.fn_current_sequence()
        self.sidebar.set_document_actions(case is not None,
            self.panel.fn_is_dirty() or self.source is None or self.source.suffix.lower() == '.diag')

    def _release_current(self):
        if self.document_id in self.sidebar._drafts:
            self.sidebar.remove_draft(self.document_id)
        elif self.document_id:
            self.sidebar.set_document_dirty(self.document_id, False)

    def add_sequence(self, name=None):
        if name is None:
            name, ok = QInputDialog.getText(self.panel, 'New sequence', 'Distinct sequence name:')
            if not ok:
                return False
        name = name.strip()
        try:
            safe_component(name)
            names = [case.name.casefold() for case in self.sidebar._drafts.values()]
            for path in self.repository.fn_list_sequences():
                try:
                    names.append(self.repository.fn_load_sequence(path).name.casefold())
                except ValueError:
                    continue
            if name.casefold() in names or (self.repository.root / f'{name}.json').exists():
                raise ValueError('A sequence with this name already exists. Choose a distinct name.')
        except (OSError, ValueError) as error:
            self.panel.show_notice(str(error))
            return False
        if not self._allow_replace():
            return False
        self._release_current()
        self.source = None
        self.document_id = 'draft:' + uuid4().hex
        case = DiagnosticTestCase(1, name, '', True, [])
        self.sidebar.add_draft(self.document_id, case)
        self.panel.fn_load_sequence(case)
        self.panel._mark_dirty()
        return True

    def import_sequence(self):
        names = {ecu.name for ecu in self.panel._available_ecus if self.panel._resolved_ecu(ecu.name)} if self.panel._current_vehicle is not None else None
        dialog = SequenceExchangeDialog(self.panel, ecu_names=names)
        if dialog.exec() != QDialog.Accepted:
            return False
        if self.panel.fn_current_sequence() is None and not self.add_sequence():
            return False
        self.panel.apply_import(dialog.parsed, dialog.mode)
        return True

    def export_sequence(self):
        if self.panel.fn_current_sequence() is None:
            return False
        SequenceExchangeDialog(self.panel, text=self.panel.exchange_text()).exec()
        return True

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
        if source_id == self.document_id and not force:
            return True
        try:
            path = Path(source_id).resolve()
            if self.source == path and not force:
                return True
            case = self.repository.fn_load_sequence(path)
        except (OSError, ValueError) as error:
            self.panel.show_notice(f"{source_id}: {error}")
            self.sidebar.mark_opened(self.document_id or "", persist=False)
            return False
        if not self._allow_replace():
            self.sidebar.mark_opened(self.document_id or "", persist=False)
            return False
        # Save in _allow_replace may have updated this very same source.
        try:
            case = self.repository.fn_load_sequence(path)
        except (OSError, ValueError) as error:
            self.panel.show_notice(str(error))
            return False
        self._release_current()
        self.source = path
        self.document_id = str(path)
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
            case = self.panel.sequence_for_save()
            unresolved = self.panel.unresolved_ecus()
            if destination.suffix.lower() != '.json':
                raise ValueError("Save As must use .json; .diag sources are never overwritten.")
            if destination.exists() and destination != self.source and not overwrite:
                raise FileExistsError("Destination already exists. Choose a different file or confirm overwrite in Save As.")
            result = self.repository.fn_save_sequence(case, destination)
        except (OSError, ValueError) as error:
            self.panel.show_notice(f"Cannot save sequence: {error}")
            return None
        self.source = destination
        old_id = self.document_id
        self.document_id = str(destination)
        self.sidebar.replace_draft_id(old_id, self.document_id)
        if unresolved:
            self.panel.import_diagnostics += tuple(f'Save normalized row {row}: original ECU {name!r}' for row, name in unresolved)
        self.panel._test_case = case
        self.panel._step_signatures = self.panel._runtime_signatures()
        self.panel._refresh_ecu_combos()
        self.panel._selection_changed()
        self.panel.mark_saved()
        if hasattr(self.repository, 'register_source'):
            self.repository.register_source(destination)
        self.sidebar.fn_refresh_sequences()
        self.sidebar.mark_opened(str(destination))
        self.sidebar.set_document_dirty(self.document_id, False)
        self._sync_actions()
        self._vehicle_changed(self.panel.fn_current_vehicle())
        self.panel.show_notice('Sequence saved.' + ('\n' + '\n'.join(self.panel.import_diagnostics) if self.panel.import_diagnostics else ''))
        return result

    def _vehicle_changed(self, name):
        if self.source is not None:
            try:
                self.store.save_vehicle(str(self.source), name)
            except OSError as error:
                self.panel.show_notice(f"Cannot save Vehicle view preference: {error}")

    def refresh_vehicles(self, changed_name=""):
        self.panel.fn_refresh_vehicles(preserve_unchanged=True)
