# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

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
        'NSHumanReadableCopyright': 'Copyright 2025, David Kershaw',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDisplayName' :'FlightPath Data',
        'CFBundleExecutable' :'FlightPath Data',
        'CFBundleIconFile' :'icon.icns',
        'CFBundleIdentifier' :'com.flightpathdata.flightpath',
        'CFBundleInfoDictionaryVersion' :'6.0',
        'CFBundleName' :'FlightPath Data',
        'CFBundlePackageType' :'APPL',
        'CFBundleVersion':'1.0.01',
        'LSApplicationCategoryType':'public.app-category.developer-tools',
        'LSRequiresNativeExecution':True,
        'LSMinimumSystemVersion':'12.0.0',
        'CFBundleShortVersionString': '1.0.02',
        'ITSAppUsesNonExemptEncryption': False,
        'NSHighResolutionCapable': False
    },
)
