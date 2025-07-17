# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os



build_number = None
with open("build_number.txt", "r") as file:
    build_number = file.read()
    build_number = build_number.strip()
if build_number is None:
    raise ValueError("The FLIGHTPATH_BUILD env var must exist")



datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('../flightpath')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


# Get the absolute path to your assets directory
assets_path = os.path.abspath('../flightpath/assets')  # Adjust this path to the correct location of your assets
datas.append((assets_path, 'assets'))


a = Analysis(
    ['../flightpath/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FlightPath Data',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon=['../flightpath/assets/icons/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FlightPath Data',
)
app = BUNDLE(
    coll,
    name='FlightPath Data.app',
    icon='../flightpath/assets/icons/icon.icns',
    bundle_identifier=None,
    info_plist={
        'NSHumanReadableCopyright': 'Copyright 2025, CsvPath Maintainers; Atesta Analytics; David Kershaw',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDisplayName' :'FlightPath Data',
        'CFBundleExecutable' :'FlightPath Data',
        'CFBundleIconFile' :'icon.icns',
        'CFBundleIdentifier' :'com.flightpathdata.flightpath',
        'CFBundleInfoDictionaryVersion' :'6.0',
        'CFBundleName' :'FlightPath Data',
        'CFBundlePackageType' :'APPL',
        'CFBundleVersion':build_number,
        'LSApplicationCategoryType':'public.app-category.developer-tools',
        'LSRequiresNativeExecution':True,
        'LSMinimumSystemVersion':'12.0.0',
        'CFBundleShortVersionString': build_number,
        'ITSAppUsesNonExemptEncryption': False,
        'NSHighResolutionCapable': True
    },
)
