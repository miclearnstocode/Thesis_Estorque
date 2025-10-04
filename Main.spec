# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['thesis_copy\\Main.py'],
    pathex=[],  # You can add paths here if needed, but no imports!
    binaries=[],
    datas=[
        # Include config.ini - format: (source, destination)
        ('config.ini', '.'),
        
        # Include config_manager.py
        ('config_manager.py', '.'),
        
        # Include icons directory
        ('icons', 'icons'),
        
        # Include assets directory  
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'mysql.connector',
        'mysql.connector.locales.eng.client_error',  # Often missing
        'customtkinter',
        'CTkMessagebox',
        'PIL',
        'PIL._tkinter_finder',
        'pandas',
        'numpy',
        'tkinter',
        'configparser'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)