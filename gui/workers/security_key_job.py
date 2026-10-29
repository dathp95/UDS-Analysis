"""Bounded provider calculation away from the Qt GUI and CAN owner threads."""
from PySide6.QtCore import QThread


# A closing tab may cancel before a provider returns. Keep the parentless thread
# alive until finished; destroying a running QThread would terminate the process.
_RUNNING_JOBS = set()


class SecurityKeyJob(QThread):
    def __init__(self, session, provider, gate, request):
        super().__init__()
        self.session, self.provider, self.gate = session, provider, gate
        self.request = request
        self.succeeded = False
        self.finished.connect(self._release)

    def start(self):
        _RUNNING_JOBS.add(self)
        super().start()

    def run(self):
        try:
            self.session.calculate_verified(self.provider, self.gate)
            self.succeeded = True
        except Exception:
            # Never propagate provider exceptions containing seed/key/secret data.
            self.succeeded = False

    def _release(self):
        if not self.wait(0):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1, self._release)
            return
        _RUNNING_JOBS.discard(self)
        self.deleteLater()
