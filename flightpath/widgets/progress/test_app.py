# In your main window / AI caller

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from ai_progress_widget import AIProgressWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central = QWidget()
        layout = QVBoxLayout(central)

        self.progress = AIProgressWidget(max_turns=5)
        layout.addWidget(self.progress)

        btn = QPushButton("Ask Claude")
        btn.clicked.connect(self.run_query)
        layout.addWidget(btn)

        self.setCentralWidget(central)

    def run_query(self):
        self.progress.reset("Starting…")
        result = self.call_claude_with_turns(
            prompt="...",
            on_turn=self._on_turn   # your existing callback hook
        )
        self.progress.reset("Done ✓")

    def call_claude_with_turns(self, prompt, on_turn):
        import time
        for _ in range(0,5):
            time.sleep(1)
            on_turn(_, "t")

    def _on_turn(self, turn_number: int, event_type: str):
        # Called by your AI loop on each turn
        labels = {
            "tool_call": "Calling tool…",
            "tool_result": "Processing result…",
            "response": "Generating response…",
        }
        label = labels.get(event_type, f"Turn {turn_number}…")
        self.progress.set_turn(turn_number, label)
        QApplication.processEvents()   # refresh UI since you're on main thread


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
