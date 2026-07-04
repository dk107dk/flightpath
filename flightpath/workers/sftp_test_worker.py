import socket

import paramiko
from PySide6.QtCore import QObject, QRunnable, Signal


class SftpTestSignals(QObject):
    finished = Signal(bool, str)


class SftpTestWorker(QRunnable):
    def __init__(self, *, server: str, port: int, username: str, password: str) -> None:
        super().__init__()
        if not server:
            raise ValueError("server cannot be empty")
        self.setAutoDelete(False)
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.signals = SftpTestSignals()

    def run(self) -> None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                self.server,
                port=self.port,
                username=self.username,
                password=self.password,
                allow_agent=False,
                look_for_keys=False,
                timeout=10,
            )
            self.signals.finished.emit(True, "Connected successfully")
        except paramiko.AuthenticationException:
            self.signals.finished.emit(
                False, "Authentication failed: wrong username or password"
            )
        except paramiko.ssh_exception.NoValidConnectionsError:
            self.signals.finished.emit(
                False, "Could not reach server — check host and port"
            )
        except socket.timeout:
            self.signals.finished.emit(False, "Connection timed out")
        except socket.gaierror:
            self.signals.finished.emit(
                False, "Host not found — check the server address"
            )
        except Exception as e:
            self.signals.finished.emit(False, f"Connection failed: {e}")
        finally:
            try:
                client.close()
            except Exception:
                pass
