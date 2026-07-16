
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
from gui.widgets.controls.quick_access_button import QuickAccessButton



from gui.widgets.controls.secondary_button import SecondaryButton


class QuickAccessWidget(QWidget):

    quick_filter_selected = Signal(dict)

    def __init__(self):

        super().__init__()

        self.quick_filters = []

        self.quick_access_controller = QuickAccessController()

        self.setup_ui()

        self.fn_reload()
    
    def setup_ui(self):

        self.group = QGroupBox(
            "Quick Access"
        )

        self.group_layout = QVBoxLayout()

        self.group.setLayout(
            self.group_layout
        )

        self.group_layout.setContentsMargins(8, 8, 8, 8)

        self.group_layout.setSpacing(8)

        # Quick filter buttons
        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_widget = QWidget()

        self.button_layout = QVBoxLayout(
            self.scroll_widget
        )

        self.button_layout.setContentsMargins(8, 8, 8, 8)

        self.button_layout.setSpacing(6)

        self.scroll_area.setWidget(
            self.scroll_widget
        )

        self.group_layout.addWidget(
            self.scroll_area
        )

        self.scroll_area.setMaximumHeight(240)
        self.scroll_area.setMinimumHeight(200)

        self.group_layout.addSpacing(10)

        # Add button
        self.btn_add = SecondaryButton(
            "+ Add Filter"
        )

        self.group_layout.addWidget(
            self.btn_add
        )

        root_layout = QVBoxLayout(self)

        root_layout.addWidget(
            self.group
        )
        
        self._connect_signals()

    def _connect_signals(self):

        self.btn_add.clicked.connect(
            self.fn_add_filter
        )

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
            "✏ Edit"
        )

        action_delete = menu.addAction(
            "🗑 Delete"
        )

        action = menu.exec(

            button.mapToGlobal(pos)

        )

        if action == action_edit:

            self._fn_edit_filter(quick_filter)

        elif action == action_delete:

            self._fn_delete_filter(quick_filter)
    
    
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

