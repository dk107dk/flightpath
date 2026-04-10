from PySide6.QtWidgets import QTreeView
from PySide6.QtCore import QTimer


class LazyTreeView(QTreeView):
    def __init__(self, parent, *, main) -> None:
        super().__init__(parent)
        self.main = main
        #
        # this class should take some load off the UI, but in practice it isn't
        # very apparent. fixing the eager loading of file or not file for
        # all the tree items was more impactful. leaving this because it seems
        # likely that we'll need to rely on it more in the future.
        #
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(500)  # ms to wait after last resize event
        self._resize_timer.timeout.connect(self._on_resize_settled)

    def reset(self) -> None:
        self.model().set_frozen(False)
        super().reset()
        print("resettsing!")

    def is_index_visible(self, index):
        rect = self.visualRect(index)
        return not rect.isEmpty() and self.viewport().rect().intersects(rect)

    def resizeEvent(self, event):
        if hasattr(self.model(), "set_frozen"):
            self.model().set_frozen(True)
        self._resize_timer.start()  # restarts the timer on each event
        super().resizeEvent(event)

    def _on_resize_settled(self):
        if hasattr(self.model(), "set_frozen"):
            self.model().set_frozen(False)
        self.updateGeometries()
        self.viewport().update()

    def viewportEvent(self, event):
        return super().viewportEvent(event)
