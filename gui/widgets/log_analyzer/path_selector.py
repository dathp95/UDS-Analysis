from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog

)
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.controls.primary_button import PrimaryButton

from PySide6.QtCore import Signal

class PathSelectorWidget(QWidget):

    path_changed = Signal(str)

    def __init__(self, title, file_filter):
        super().__init__()

        self.file_filter = file_filter
        self.label = QLabel(title)
        self.edit_path = PrimaryLineEdit(placeholder="Please, input file format *.blf/asc")

        self.browse_button = PrimaryButton("Browse")

        self.set_ui()
        self.connect_signals()


    def set_ui(self):
        main_layout = QVBoxLayout(self) # Tạo layout chính theo chiều dọc
        file_layout = QHBoxLayout()     # Tạo layout ngang

        file_layout.addWidget(self.edit_path)
        file_layout.addWidget(self.browse_button)


        main_layout.addWidget(self.label)
        
        main_layout.addLayout(file_layout)  # Thêm layout ngang vào layout dọc
    
    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_file)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.label.text(),
            "",
            self.file_filter
        )
        if file_path:
            self.edit_path.setText(file_path)   # Đưa đường dẫn lên QLineEdit
            self.path_changed.emit(file_path)
    
    def path(self):
        return self.edit_path.text()    # Nó chỉ làm 1 việc lấy dữ liệu filename = widget.path() => "C:\\abc\\test.blf" 
    
    def set_path(self,value):
        self.edit_path.setText(value)   # Nó chỉ làm 1 việc đưa dữ liệu vào QLineEdit

    def fn_refresh_theme(self):

        self.edit_path.fn_refresh_theme()
        self.browse_button.fn_refresh_theme()
