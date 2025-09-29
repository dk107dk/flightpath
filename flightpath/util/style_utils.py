from PySide6.QtWidgets import (
    QWidget,
    QPlainTextEdit,
    QTreeView,
    QTableView
)
import darkdetect
from flightpath.editable import EditStates
from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit
from flightpath.util.syntax.csvpath_highlighter import CsvPathSyntaxHighlighter
from flightpath.widgets.raw_text_edit import RawTextEdit

class StyleUtility:
    #
    # TODO: there's too much variability about how the views work. not
    # a huge problem, but it is messy now, even tho it made sense at each
    # step. this class hides and/or highlights a bunch of the clutter.
    #

    NOT_EDITABLE = "#f8fff8"
    NOT_EDITABLE_DARK = "#332a33"

    @staticmethod
    def set_common_style(widget):
        widget.setStyleSheet("font-size: 15px;")
        ...

    @classmethod
    def _is(cls, widget, name ) -> bool:
        n = cls._name(widget)
        return n == name

    @classmethod
    def _name(cls, widget) -> str:
        n = widget.__class__.__name__
        n = n[n.rfind(".")+1:]
        n = n.rstrip("'>")
        return n

    @classmethod
    def set_editable_background(cls, widget:QWidget) -> None:
        if cls._is( widget, "DataViewer"):
            cls._set_editable_background( widget.table_view )
            cls._set_editable_background( widget.raw_view.content_view )
        else:
            if hasattr( widget, "content_view"):
                widget = widget.content_view
            cls._set_editable_background(widget)

    @classmethod
    def _set_editable_background(cls, widget) -> None:
        inst = isinstance(widget, (QTreeView, QTableView, QPlainTextEdit, CsvPathTextEdit, RawTextEdit) )
        name = cls._name(widget)
        inst = inst or name == "KeyableTreeView"
        if inst:
            color = StyleUtility.NOT_EDITABLE_DARK if darkdetect.isDark() else StyleUtility.NOT_EDITABLE
            if not widget.editable == EditStates.EDITABLE:
                widget.setStyleSheet(f"{name} {{ background-color: {color}; }}")
            if isinstance( widget, CsvPathTextEdit ):
                CsvPathSyntaxHighlighter(widget.document())
        else:
            print(f"Unknown widget type: {widget.__class__.__name__}. Cannot determine editability for style.")

