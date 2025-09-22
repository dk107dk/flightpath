import os
import sys
import subprocess
import platform


class OsUtility:

    @classmethod
    def is_sandboxed(cls) -> bool:
        return os.environ.get("APP_SANDBOX_CONTAINER_ID") is not None

    @classmethod
    def is_windows(cls) -> bool:
        return sys.platform == "win32"

    @classmethod
    def is_mac(cls) -> bool:
        return sys.platform == "darwin"

    @classmethod
    def is_unix(cls) -> bool:
        return not cls.is_mac() and not cls.is_windows()

    @classmethod
    def file_system_open_cmd(cls) -> str:
        if cls.is_windows():
            return 'explorer'
        elif cls.is_mac():
            return 'open'
        else:
            return 'xdg-open'

    @classmethod
    def open_file(cls, path) -> None:
        osname = platform.system()
        if osname == "Windows":
            os.startfile(path)
        elif osname == "Darwin":  # macOS
            subprocess.run(["open", path])
        elif osname == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            raise ValueError("Unknown OS: {osname}")


