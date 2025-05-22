import os
import sys

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
            return 'explorer.exe'
        elif cls.is_mac():
            return 'open'
        else:
            return 'xdg-open'

