"""Run from the repository root: python -m tests.performance.benchmark_q_current_loading."""
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QTimer
from PySide6.QtWidgets import QApplication

import gui.tabs.q_current_tab as module


def measure(count, iteration, app):
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        root = Path(directory)
        source = root / "synthetic.csv"
        source.write_text("Trigger time,No1 Average Ch1\n" + "".join(
            f"26-09-11 11:{i // 60000:02d}:{(i // 1000) % 60:02d}.{i % 1000:03d},0.01\n"
            for i in range(count)), encoding="utf-8")
        tab = module.QCurrentTab(database_dir=root / "db", config_file=root / "config.json")
        tab.resize(1400, 850)
        tab.show()
        app.processEvents()
        metrics = {"rows": count, "iteration": iteration}

        def timed(name, callback):
            def call(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return callback(*args, **kwargs)
                finally:
                    metrics[name] = metrics.get(name, 0) + time.perf_counter() - start
            return call

        ticks = [time.perf_counter()]
        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(lambda: ticks.append(time.perf_counter()))
        timer.start()
        try:
            with patch.object(module, "normalize_current_data", timed("parse_s", module.normalize_current_data)), \
                 patch.object(module, "import_dataset", timed("sqlite_write_s", module.import_dataset)), \
                 patch.object(module, "get_samples", timed("sqlite_read_s", module.get_samples)), \
                 patch.object(tab, "_populate_review_table", timed("table_bind_s", tab._populate_review_table)), \
                 patch.object(tab, "_initialize_analysis_range_from_samples", timed("range_gui_s", tab._initialize_analysis_range_from_samples)), \
                 patch.object(tab, "_load_samples_into_workspace", timed("workspace_gui_s", tab._load_samples_into_workspace)), \
                 patch.object(module.QMessageBox, "information"):
                tab.set_source_file(source)
                start = time.perf_counter()
                tab.import_current_file()
                while tab._operation_running:
                    app.processEvents()
                    if time.perf_counter() - start > 180:
                        raise TimeoutError("Import benchmark did not finish")
                    time.sleep(0.001)
                app.processEvents()
                metrics["total_s"] = time.perf_counter() - start
                ticks.append(time.perf_counter())
                metrics["max_gui_gap_s"] = max(b - a for a, b in zip(ticks, ticks[1:]))
                metrics["samples"] = len(tab.current_samples)
                start = time.perf_counter()
                tab.fn_refresh_theme()
                metrics["theme_s"] = time.perf_counter() - start
        finally:
            timer.stop()
            tab.close()
            tab.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        print(json.dumps(metrics, sort_keys=True), flush=True)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication([])
    for count in (1000, 50000):
        for iteration in range(1, 3):
            measure(count, iteration, app)
