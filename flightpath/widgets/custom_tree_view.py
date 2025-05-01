from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Signal

class CustomTreeView(QTreeView):
    empty_area_click = Signal()

    def mousePressEvent(self, event):
        """Emits an event if the user clicks on an empty space."""
        index = self.indexAt(event.position().toPoint())
        if not index.isValid():
            self.empty_area_click.emit()
            # Accept the event to prevent further processing
            event.accept()
        else:
            # Only call super if we have a valid index
            super().mousePressEvent(event)

    # Override this method to add additional safety
    def selectionChanged(self, selected, deselected):
        # Add safeguards before passing to base implementation
        try:
            super().selectionChanged(selected, deselected)
        except Exception as e:
            print(f"Error in selection change: {e}")


    def expanded(self, index):
        # Safety check before passing to base implementation
        if index.isValid() and self.model():
            super().expanded(index)

    def collapsed(self, index):
        # Safety check before passing to base implementation
        if index.isValid() and self.model():
            super().collapsed(index)



