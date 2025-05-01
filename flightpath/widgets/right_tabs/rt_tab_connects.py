#
# widget parts
#   - connects
#   - behaviors
#   - layout and load
#

class RtTabConnects:
    def __init__(self, main) -> None:
        self.main = main

    def _connects(self) -> None:
        self.main.rt_tab_widget.currentChanged.connect(self.main._on_rt_tab_changed)

