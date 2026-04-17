from PyQt6.QtCore import QThread, pyqtSignal

class InferenceWorker(QThread):
    """Unified background worker for neural inference."""
    response_ready = pyqtSignal(str)

    def __init__(self, text: str, manager, parent=None):
        super().__init__(parent)
        self.text = text
        self.manager = manager

    def run(self):
        try:
            response = self.manager.process_request(self.text)
            self.response_ready.emit(response)
        except Exception as e:
            self.response_ready.emit(f"Neural Error: {str(e)}")
