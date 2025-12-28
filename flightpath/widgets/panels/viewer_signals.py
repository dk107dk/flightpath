from PySide6.QtCore import QObject, Signal

class ViewerSignals(QObject):
    edit_made = Signal(tuple)
    columns_deleted = Signal(tuple)
    columns_inserted = Signal(tuple)
    rows_deleted = Signal(tuple)
    rows_inserted = Signal(tuple)



