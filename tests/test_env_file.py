import os
import unittest
from flightpath.widgets.forms.config_form import ConfigForm

class TestConfigForm(unittest.TestCase):

    def test_make_path(self):
        _ = os.sep
        cwd = f"{_}d{_}k{_}fp{_}cp"
        current_project = "cp"

        path = f" "
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == "env"

        path = None
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == "env"

        path = f"env"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == "env"

        path = f" config{_}env.json"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}env.json"

        path = f"env.json "
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}env.json"

        path = f"fish{_}env.json"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}fish{_}env.json"

        path = f"{_}config{_}env.json"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}env.json"

        path = f"{_}fish{_}env.json"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}env.json"

        path = f"{cwd}{_}env.json"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}env.json"

        path = f"{cwd}{_}config{_}env.json"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}env.json"

        path = f"{cwd}{_}fish{_}env.json"
        path = ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)
        assert path == f"{cwd}{_}config{_}fish{_}env.json"





