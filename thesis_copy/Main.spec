# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Main.py'],
    pathex=[],
    binaries=[],
    datas=[('grade_screen.py', '.'), ('loginform.py', '.'), ('curriculum_screen.py', '.'), ('database.py', '.'), ('archive_screen.py', '.'), ('appraisal_screen.py', '.'), ('admin_screen.py', '.'), ('../icons', 'icons'), ('../Image', 'Image'), ('pictures', 'thesis_copy/pictures')],
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
    [],
    exclude_binaries=True,
    name='Main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Main',
)
