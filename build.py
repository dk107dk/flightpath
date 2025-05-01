import PyInstaller.__main__
import subprocess


def build_application():

    print("Creating executable file for FlightPath")
    PyInstaller.__main__.run([
        'flightpath/main.py',
        '--windowed',  # Required for Windows install to not open a console.
        '--collect-all', 'flightpath',
        '--log-level', 'WARN',
        '--name', 'FlightPath Data',
        '--noconfirm',
        '--icon', 'flightpath/assets/icons/icon.icns'
    ])
    #
    # exp! seems to be deleting. would like to see.
    #
    #subprocess.run(['rm', 'flightpath.spec'])


if __name__ == "__main__":
    build_application()
