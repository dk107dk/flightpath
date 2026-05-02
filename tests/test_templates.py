import unittest
from flightpath.dialogs.template_dialog import TemplateDialog


class TestTemplates(unittest.TestCase):
    def test_templates(self):
        print("")
        end = ":run_dir"

        t = ""
        assert ("", False) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "/"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "\\"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = ":a"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "//"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "http://abc"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "c:\\abc"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "c/:c"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "c:/c"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = ":run_dir/c"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = ":run_dir/c/:run_dir"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = ":run_dir"
        assert ("", False) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "/:run_dir"
        assert ("", False) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "a/:run_dir"
        assert ("a/:run_dir", False) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = ":0/a/:run_dir"
        assert (":0/a/:run_dir", False) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "b/:0/a/:run_dir"
        assert ("b/:0/a/:run_dir", False) == TemplateDialog.clean_or_reject(
            end=end, t=t
        )

        t = "b/:0/:1/:run_dir"
        assert ("b/:0/:1/:run_dir", False) == TemplateDialog.clean_or_reject(
            end=end, t=t
        )

        t = "b/:09/a/:run_dir"
        assert ("b/:09/a/:run_dir", False) == TemplateDialog.clean_or_reject(
            end=end, t=t
        )

        t = "/b/:09/a/:run_dir"
        assert ("b/:09/a/:run_dir", False) == TemplateDialog.clean_or_reject(
            end=end, t=t
        )

        t = "a/b/c"
        assert ("a/b/c/:run_dir", False) == TemplateDialog.clean_or_reject(end=end, t=t)

        t = "a/:b/:run_dir"
        assert ("", True) == TemplateDialog.clean_or_reject(end=end, t=t)
