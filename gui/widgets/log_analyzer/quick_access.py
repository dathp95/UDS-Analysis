
from copy import deepcopy

from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QScrollArea,
    QMenu,
    QMessageBox
)
from gui.controllers.quick_access_controller import QuickAccessController
from gui.dialogs.quick_filter_dialog import QuickFilterDialog
from gui.dialogs.import_quick_filters_dialog import ImportQuickFiltersDialog
from gui.dialogs.export_quick_filters_dialog import ExportQuickFiltersDialog
from gui.widgets.controls.quick_access_button import QuickAccessButton


from gui.widgets.controls.secondary_button import SecondaryButton
from gui.themes.styles.controls.scrollbar_style import (
    fn_apply_scrollbar_style,
)


class QuickAccessWidget(QWidget):

    quick_filter_selected = Signal(dict)

    def __init__(self):

        super().__init__()

        self.quick_filters = []
        self.buttons = []
        self.selected_filter = None


        self.quick_access_controller = QuickAccessController()

        self.setup_ui()

        self.fn_reload()
    
    def setup_ui(self):

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        # --------------------------
        # Quick Filter
        # --------------------------

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_widget = QWidget()

        self.button_layout = QVBoxLayout(self.scroll_widget)

        self.button_layout.setContentsMargins(8, 8, 8, 8)
        self.button_layout.setSpacing(4)

        self.scroll_area.setWidget(self.scroll_widget)

        fn_apply_scrollbar_style(self.scroll_area)

        # Keep room for Import/Add actions and the theme switch below without
        # forcing the left panel beyond the available window height.
        self.scroll_area.setMinimumHeight(360)

        root_layout.addWidget(self.scroll_area)

        root_layout.addSpacing(4)

        # --------------------------
        # Add Filter
        # --------------------------

        self.btn_add = SecondaryButton("+ Add Filter +")

        root_layout.addWidget(self.btn_add)

        self.btn_import = SecondaryButton("Import Filters")
        root_layout.addWidget(self.btn_import)

        self.btn_export = SecondaryButton("Export Filters")
        root_layout.addWidget(self.btn_export)

        root_layout.addStretch()

        self._connect_signals()

    def _connect_signals(self):

        self.btn_add.clicked.connect(
            self.fn_add_filter
        )
        self.btn_import.clicked.connect(self.fn_import_filters)
        self.btn_export.clicked.connect(self.fn_export_filters)

    def fn_import_filters(self):
        dialog = ImportQuickFiltersDialog(self)
        if not dialog.exec():
            return
        try:
            self.quick_access_controller.fn_add_many(dialog.fn_filters())
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Import Quick Access", str(error))
            return
        self.fn_reload()


    def fn_export_filters(self):
        dialog = ExportQuickFiltersDialog(
            self.quick_access_controller.fn_export_filters(),
            self,
        )
        dialog.exec()

    def fn_reload(self):
        """
        Reload all quick filter buttons.
        """

        self._fn_clear_buttons()

        self._fn_load_filters()

        self._fn_build_buttons()
    
    
    def _fn_load_filters(self):         

        self.quick_filters = self.quick_access_controller.fn_load()
    
    
    def fn_add_filter(self):
        """
        Show Add Quick Filter dialog.
        """

        dialog = QuickFilterDialog(
            quick_filter=None,
            parent=self
        )

        if dialog.exec():

            quick_filter = dialog.fn_get_data()

            self.quick_access_controller.fn_add(
                quick_filter
            )

            self.fn_reload()
    
    
    def _fn_build_buttons(self):
        """
        Create quick filter buttons.
        """

        for item in self.quick_filters:

            button = QuickAccessButton(

                text=item["name"],

                height=24

            )

            self.buttons.append(button)


            button.setContextMenuPolicy(
                Qt.CustomContextMenu
            )

            button.clicked.connect(

                lambda checked=False, data=item:

                self._fn_button_clicked(data)

            )
            button.customContextMenuRequested.connect(

                lambda pos, data=item, btn=button:

                self._fn_show_context_menu(
                    btn,
                    pos,
                    data
                )

            )

            self.button_layout.addWidget(
                button
            )
        self.button_layout.addStretch(2)

    
    def _fn_clear_buttons(self):
        """
        Remove all quick filter buttons.
        """
        self.buttons.clear()


        while self.button_layout.count():

            item = self.button_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

            del item
    
    
    def _fn_button_clicked(
            self,
            filter_data: dict,
        ):

        self.selected_filter = filter_data
        self.quick_filter_selected.emit(

            filter_data

        )
    
    def _fn_show_context_menu(
            self,
            button,
            pos,
            quick_filter,
        ):
        """
        Show context menu.
        """

        menu = QMenu(self)

        action_edit = menu.addAction(
            "Edit"
        )

        action_clone = menu.addAction("Clone")
        action_delete = menu.addAction("Delete")

        action = menu.exec(button.mapToGlobal(pos))

        if action == action_edit:
            self._fn_edit_filter(quick_filter)
        elif action == action_clone:
            self._fn_clone_filter(quick_filter)
        elif action == action_delete:
            self._fn_delete_filter(quick_filter)

    def fn_clone_selected(self):
        if self.selected_filter is None:
            return

        existing_names = {
            item.get("name", "")
            for item in self.quick_access_controller.fn_load()
        }
        base_name = f"{self.selected_filter.get('name', 'Quick Filter')} (Copy)"
        name = base_name
        suffix = 2
        while name in existing_names:
            name = f"{base_name} {suffix}"
            suffix += 1

        cloned = deepcopy(self.selected_filter)
        cloned["name"] = name
        self.quick_access_controller.fn_insert_after(
            self.selected_filter["id"],
            cloned,
        )
        self.fn_reload()
    
    
    def _fn_delete_filter(
            self,
            quick_filter: dict,
        ):
        """
        Delete a quick filter.
        """

        answer  = QMessageBox.question(

            self,

            "Delete Quick Filter",

            f"Are you sure you want to delete the quick filter '{quick_filter['name']}' ?\n\nThis action cannot be undone.👻",

            QMessageBox.Yes | QMessageBox.No,

            QMessageBox.No

        )

        if answer  == QMessageBox.Yes:

            self.quick_access_controller.fn_delete(

                quick_filter["id"]

            )

            self.fn_reload()

    def _fn_clone_filter(self, quick_filter: dict):
        """Create an independent copy of a quick filter."""

        existing_names = {
            item.get("name", "")
            for item in self.quick_access_controller.fn_load()
        }
        base_name = f"{quick_filter.get('name', 'Quick Filter')} (Copy)"
        name = base_name
        suffix = 2
        while name in existing_names:
            name = f"{base_name} {suffix}"
            suffix += 1

        cloned = deepcopy(quick_filter)
        cloned.pop("id", None)
        cloned.pop("enabled", None)
        cloned["name"] = name

        self.quick_access_controller.fn_add(cloned)
        self.fn_reload()

    def _fn_edit_filter(
            self,
            quick_filter: dict,
        ):
        """
        Edit one quick filter.
        """

        dialog = QuickFilterDialog(

            quick_filter=quick_filter,

            parent=self

        )

        if not dialog.exec():

            return

        updated_filter = dialog.fn_get_data()

        self.quick_access_controller.fn_update(
        updated_filter
        )

        self.fn_reload()

    def fn_set_enabled(self):

        self.fn_enable_buttons(True)

    def fn_set_disabled(self):

        self.fn_enable_buttons(False)
    
    def fn_enable_buttons(
            self,
            enabled: bool
        ):
        """
        Enable or disable all quick access buttons.
        """

        for button in self.buttons:

            button.fn_enable(enabled)
    
    def fn_refresh_theme(self):

        fn_apply_scrollbar_style(self.scroll_area)
        self.btn_add.fn_refresh_theme()
        self.btn_import.fn_refresh_theme()
        self.btn_export.fn_refresh_theme()
