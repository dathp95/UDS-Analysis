import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QGroupBox, QSplitter

from gui.tabs.q_current_tab import PLACEHOLDER_VALUE, QCurrentTab
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox


class QCurrentTabTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def tearDown(self):
        ThemeManager.fn_set_theme(ThemeType.LIGHT)

    def test_q_current_tab_builds_static_placeholder_layout(self):
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)

        self.assertIsInstance(tab.settings_group, QGroupBox)
        self.assertEqual(tab.settings_group.title(), "Analysis Settings")
        self.assertIsInstance(tab.vehicle_selector, PrimaryComboBox)
        self.assertEqual(tab.vehicle_selector.currentText(), "â€”")
        self.assertEqual(tab.file_value.text(), "â€”")

        self.assertIsInstance(tab.main_splitter, QSplitter)
        self.assertEqual(tab.main_splitter.orientation(), Qt.Horizontal)
        self.assertIs(tab.main_splitter.widget(0), tab.information_group)
        self.assertIs(tab.main_splitter.widget(1), tab.center_splitter)
        self.assertIs(tab.main_splitter.widget(2), tab.right_panel)

        self.assertEqual(tab.center_splitter.orientation(), Qt.Vertical)
        self.assertIs(tab.center_splitter.widget(0), tab.chart_group)
        self.assertIs(tab.center_splitter.widget(1), tab.review_group)

        self.assertEqual(tab.information_group.title(), "Analysis Information")
        self.assertEqual(tab.chart_group.title(), "Current Chart")
        self.assertEqual(tab.review_group.title(), "Data Review")
        self.assertEqual(tab.summary_group.title(), "Summary")

        self.assertEqual(tab.chart_placeholder.text(), "â€”")
        self.assertEqual(tab.review_placeholder.text(), "â€”")
        self.assertTrue(all(value.text() == "â€”" for value in tab.info_values.values()))
        self.assertTrue(all(value.text() == "â€”" for value in tab.summary_values.values()))

    def test_q_current_tab_uses_existing_controls_and_theme_refresh(self):
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)

        buttons = [
            tab.btn_run,
            tab.btn_export,
            tab.btn_copy_chart,
            tab.btn_clear,
        ]
        self.assertTrue(all(isinstance(button, PrimaryButton) for button in buttons))
        self.assertEqual([button.text() for button in buttons], [
            "RUN",
            "EXPORT",
            "COPY CHART",
            "CLEAR",
        ])

        light_style = tab.chart_placeholder.styleSheet()
        ThemeManager.fn_set_theme(ThemeType.DARK)
        tab.fn_refresh_theme()
        dark_style = tab.chart_placeholder.styleSheet()

        self.assertNotEqual(light_style, dark_style)
        self.assertIn(ThemeManager.fn_colors().TEXT, dark_style)


if __name__ == "__main__":
    unittest.main()