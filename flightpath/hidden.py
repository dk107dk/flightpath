from paramiko import SSHClient


#
# these packages need to be referenced so they are found by PyInstaller
# we do it with hiddenimports in the spec file too, but it has been a
# challenge. very possibly we can take the backends out of this class
# but it's not certain and now isn't the time to dig more.
#
# oct 2025: the .spec hidden imports of smart_open.ssh, etc. are crucial and effective.
# not clear how much of the above is helpful, but some of it seems to be. but for smart-open
# we must have the hidden import arg in Analysis()
#
class Hidden:
    def __init__(self, skip=True) -> None:
        ...
        SSHClient()
