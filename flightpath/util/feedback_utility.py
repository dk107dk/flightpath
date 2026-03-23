
from flightpath.util.tabs_utility import TabsUtility as taut
#
# this is intended to be a simpler more focused static wrapper for
# widgets/help/Helper. for help things Helper may still be the place
# to look.
#
class FeedbackUtility:

    @classmethod
    def clear_feedback(cls, main) -> None:
        while main.helper.help_and_feedback.count() > 0:
            t = main.helper.help_and_feedback.widget(0)
            main.helper.help_and_feedback.removeTab(0)
            t.deleteLater()

    @classmethod
    def add_feedback_tab(cls, *, main, name:str, tab, tab_id:str=None) -> None:
        if tab_id is not None:
            tab_id = str(tab_id)
            old = taut.tab_index_by_name_if(main.helper.help_and_feedback, tab_id)
            if old is not None and old != -1:
                t = taut.find_tab(main.helper.help_and_feedback, tab_id)
                if t:
                    main.helper.help_and_feedback.removeTab(t[0])
                    t[1].deleteLater()
            tab.setObjectName(tab_id)
            main.helper.help_and_feedback.addTab(tab, name)
        else:
            tab.setObjectName(name)
            main.helper.help_and_feedback.addTab(tab, name)

    @classmethod
    def switch_to_feedback(self, main, name:str) -> None:
        t = taut.tab_index_by_name_if(main.helper.help_and_feedback, name)
        if t and t >= 0:
            taut.select_tab(main.helper.help_and_feedback, t)

    @classmethod
    def open_feedback(self, main) -> None:
        main.main.setSizes([1, 1])

    @classmethod
    def close_feedback(self, main) -> None:
        main.main.setSizes([1, 0])

    @classmethod
    def is_showing_feedback(self, main) -> bool:
        ss = main.main.sizes()
        if ss is None:
            return False
        if len(ss) <= 1:
            return False
        return ss[1] > 0

