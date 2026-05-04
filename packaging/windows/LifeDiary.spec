# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.win32 import winmanifest, winresource


ROOT = Path(SPECPATH).resolve().parents[1]
SRC = ROOT / 'src'


def _skip_windows_resource_update(*args, **kwargs):
    return None


winresource.remove_all_resources = _skip_windows_resource_update
winmanifest.write_manifest_to_executable = _skip_windows_resource_update


a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(SRC)],
    binaries=[
        ('PySide6\\plugins\\platforms\\qwindows.dll', 'PySide6\\plugins\\platforms'),
        ('PySide6\\plugins\\imageformats\\qgif.dll', 'PySide6\\plugins\\imageformats'),
        ('PySide6\\plugins\\imageformats\\qjpeg.dll', 'PySide6\\plugins\\imageformats'),
        ('PySide6\\plugins\\imageformats\\qpng.dll', 'PySide6\\plugins\\imageformats'),
        ('PySide6\\plugins\\imageformats\\qwebp.dll', 'PySide6\\plugins\\imageformats'),
    ],
    datas=[],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtXml',
        'shiboken6',
        'shiboken6.Shiboken',
        'docx',
        'docx.oxml',
        'docx.opc',
        'docx.table',
        'docx.text',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
    ],
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
    name='LifeDiary',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT / 'assets' / 'icons' / 'app_icon.ico'),
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
    name='LifeDiary',
)
