import PyInstaller.__main__
import subprocess

"""
    don't use this script.
    unless there is no spec for some reason just do:
        pyinstaller FlightPath\ Data.spec

"""
def build_application():

    print("Creating executable file for FlightPath")
    PyInstaller.__main__.run([
        '../flightpath/main.py',
        '--windowed',  # Required for Windows install to not open a console.
        '--collect-all', 'flightpath',
        '--log-level', 'WARN',
        '--name', 'FlightPath Data',
        '--noconfirm',
        '--icon', '../flightpath/assets/icons/icon.icns'
    ])
    #
    # if spec exists we don't have to run this script to build it.
    #
    #subprocess.run(['rm', 'flightpath.spec'])


if __name__ == "__main__":
    build_application()
