import sys
import os

from flightpath.util.gate_guard import GateGuard
from flightpath_server.main import Main as ServerMain

def server_main():
    #
    # we use this function to start FlightPath Server. this lives
    # in FlightPath Data so we can create a separate 2nd exe for
    # the windows package. macOS does not need two binaries, but
    # for windows to run Server with a console and Data without a
    # console, we need two exes.
    #
    #    - check for server mode key
    #    - if key found, start a FlightPath Server
    #
    mode = GateGuard.has_ticket()
    #
    # for now gate guard is skipped.
    #
    if True or mode is True:
        print(GateGuard.ART)
        main = ServerMain()
        main.serve()
        return

if __name__ == "__main__":
    server_main()
