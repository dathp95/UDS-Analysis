"""Session-only ECU field drafts. Capturing never validates or mutates saved models."""
from dataclasses import dataclass
from PySide6.QtCore import QObject


@dataclass(frozen=True)
class EcuDraft:
    fields: tuple[str, ...]
    browsed_dll: str | None


class EcuDraftController(QObject):
    def __init__(self, tab):
        super().__init__(tab)
        self.tab = tab
        self.drafts = {}
        self.active_key = None
        self._baseline = None
        self._loading = False
        info, resource = tab.ecu_info, tab.ecu_resource
        self.fields = (info.txt_name, info.txt_request, info.txt_response, resource.txt_dll,
                       resource.txt_odx, resource.txt_dbc, resource.txt_dtc, resource.txt_request)
        for edit in self.fields:
            edit.textChanged.connect(self.capture)
        resource.dll_browsed.connect(self.capture)
        tab.ecu_list.draft_discard_requested.connect(self.discard)

    def snapshot(self):
        return EcuDraft(tuple(edit.text() for edit in self.fields), self.tab.ecu_resource._browsed_dll)

    def capture(self, *_):
        if self._loading or self.active_key is None:
            return
        draft = self.snapshot()
        if draft == self._baseline:
            self.drafts.pop(self.active_key, None)
        else:
            self.drafts[self.active_key] = draft
        self.apply_markers()

    def leave(self):
        self.capture()
        self.active_key = None

    def activate(self, vehicle_name, ecu):
        self.leave()
        self._loading = True
        try:
            self.tab.ecu_info.fn_set_ecu(ecu)
            metadata = self.tab._controller.resolve_ecu_dll_resource(vehicle_name, ecu.name)
            self.tab.ecu_resource.fn_set_ecu(ecu, dll_metadata=metadata)
            self.active_key = (vehicle_name, ecu.name)
            self._baseline = self.snapshot()
            draft = self.drafts.get(self.active_key)
            if draft:
                for edit, text in zip(self.fields, draft.fields):
                    edit.setText(text)
                self.tab.ecu_resource._browsed_dll = draft.browsed_dll
                self.tab.ecu_resource._refresh_dll_metadata()
        finally:
            self._loading = False
        self.apply_markers()

    def apply_markers(self):
        vehicle = self.tab._current_vehicle_name
        self.tab.ecu_list.fn_set_dirty_names({name for (owner, name) in self.drafts if owner == vehicle}, vehicle)

    def saved(self, vehicle_name, ecu_name):
        key = (vehicle_name, ecu_name)
        self.drafts.pop(key, None)
        if self.active_key == key:
            self.active_key = None
        self.apply_markers()

    def discard(self, vehicle_name, ecu_name):
        key = (vehicle_name, ecu_name)
        active = self.active_key == key
        self.saved(vehicle_name, ecu_name)
        if active:
            self.tab._on_ecu_selected(ecu_name)

    def deleted_vehicle(self, vehicle_name):
        for owner, name in tuple(self.drafts):
            if owner == vehicle_name:
                self.saved(owner, name)
        if self.active_key and self.active_key[0] == vehicle_name:
            self.active_key = None
