import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QApplication, QTableView

from gui.widgets.q_current.review_table import QCurrentReviewModel, QCurrentReviewTable
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager


class QCurrentReviewModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_large_model_is_lazy_and_retains_all_rows_without_cells(self):
        samples = [SimpleNamespace(time=str(i), current_mA=-16.9) for i in range(50000)]
        model = QCurrentReviewModel()
        model.set_samples(samples)
        self.assertIs(model.samples, samples)
        self.assertLessEqual(model.rowCount(), model.BATCH_SIZE)
        self.assertTrue(model.canFetchMore(QModelIndex()))
        self.assertEqual(model.data(model.index(0, 0)), "1")
        self.assertEqual(model.data(model.index(0, 2)), "-16.90")
        while model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
        self.assertEqual(model.rowCount(), 50000)
        self.assertEqual(model.data(model.index(49999, 0)), "50000")
        model.set_samples([])
        self.assertEqual(model.rowCount(), 0)
        self.assertFalse(model.canFetchMore(QModelIndex()))

    def test_selection_filter_and_theme_keep_source_identity(self):
        view = QCurrentReviewTable()
        self.addCleanup(view.deleteLater)
        self.assertIsInstance(view, QTableView)
        model = QCurrentReviewModel(view)
        samples = [SimpleNamespace(time="first", current_mA=1),
                   SimpleNamespace(time="second", current_mA=2)]
        model.set_samples(samples)
        proxy = QSortFilterProxyModel(view)
        proxy.setSourceModel(model)
        proxy.setFilterKeyColumn(1)
        proxy.setFilterFixedString("second")
        view.setModel(proxy)
        view.selectRow(0)
        index = view.selectionModel().selectedRows()[0]
        self.assertEqual(proxy.mapToSource(index).row(), 1)
        self.addCleanup(ThemeManager.fn_set_theme, ThemeManager.fn_theme())
        for theme in (ThemeType.DARK, ThemeType.LIGHT):
            ThemeManager.fn_set_theme(theme)
            view.fn_refresh_theme()
            self.assertEqual(proxy.mapToSource(view.selectionModel().selectedRows()[0]).row(), 1)
        self.assertIs(model.samples, samples)
