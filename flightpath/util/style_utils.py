from PySide6.QtWidgets import (
    QWidget,
    QPlainTextEdit,
    QTreeView,
    QTableView
)
import darkdetect
from flightpath.editable import EditStates
from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit
from flightpath.widgets.raw_text_edit import RawTextEdit
from flightpath.widgets.md_text_edit import MdTextEdit

class StyleUtility:
    #
    # TODO: there's too much variability about how the views work. not
    # a huge problem, but it is messy now, even tho it made sense at each
    # step. this class hides and/or highlights a bunch of the clutter.
    #

    NOT_EDITABLE = "#f8fff8"
    NOT_EDITABLE_2 = "#d8ddd8"
    NOT_EDITABLE_DARK = "#332a33"
    NOT_EDITABLE_DARK_2 = "#554c55"

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
            elif hasattr( widget, "view"):
                widget = widget.view
            cls._set_editable_background(widget)

    @classmethod
    def get_not_editable_color(cls) -> str:
        color = StyleUtility.NOT_EDITABLE_DARK if darkdetect.isDark() else StyleUtility.NOT_EDITABLE
        return color

    @classmethod
    def get_not_editable_color_2(cls) -> str:
        color = StyleUtility.NOT_EDITABLE_DARK_2 if darkdetect.isDark() else StyleUtility.NOT_EDITABLE_2
        return color

    @classmethod
    def get_highlight_text(cls) -> str:
        color = StyleUtility.NOT_EDITABLE_DARK_2 if darkdetect.isDark() else StyleUtility.NOT_EDITABLE_2
        return color

    @classmethod
    def _set_editable_background(cls, widget) -> None:
        inst = isinstance(widget, (QTreeView, QTableView, QPlainTextEdit, CsvPathTextEdit, MdTextEdit, RawTextEdit) )
        name = cls._name(widget)
        inst = inst or name == "KeyableTreeView"
        if inst:
            if not widget.editable == EditStates.EDITABLE:
                color = StyleUtility.get_not_editable_color()
                widget.setStyleSheet(f"{name} {{ background-color: {color}; }}")
        else:
            print(f"Unknown widget type: {widget.__class__.__name__}. Cannot determine editability for style.")
        #
        # csvpath and json text editors need to know we're changing the background
        #
        if hasattr(widget, "background_changed"):
            widget.background_changed()

