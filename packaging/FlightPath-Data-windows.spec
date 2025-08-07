
import os

# -*- mode: python ; coding: utf-8 -*-

assets_path = os.path.abspath('../flightpath/assets')  
datas = []
datas.append((assets_path, 'assets'))

a = Analysis(
    ['..\\flightpath\\main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='FlightPathData',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.abspath('..\\flightpath\\assets\\icons\\icon.ico'),
)

