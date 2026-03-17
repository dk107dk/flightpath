
from flightpath.util.tabs_utility import TabsUtility as taut
#
# this is intended to be a simpler more focused wrapper for widgets/help/Helper
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
            print(f"FeedbackUtility.add_feedback_tab: old: {old}")
            if old is not None and old != -1:
                t = taut.find_tab(main.helper.help_and_feedback, tab_id)
                print(f"FeedbackUtility.add_feedback_tab: t: {t}")
                if t:
                    main.helper.help_and_feedback.removeTab(t[0])
                    t[1].deleteLater()
            tab.setObjectName(tab_id)
            main.helper.help_and_feedback.addTab(tab, name)
        else:
            tab.setObjectName(name)
            main.helper.help_and_feedback.addTab(tab, name)




