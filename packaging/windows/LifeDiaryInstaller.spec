# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.win32 import winmanifest, winresource


PACKAGING = Path(SPECPATH).resolve()


def _skip_windows_resource_update(*args, **kwargs):
    return None


winresource.remove_all_resources = _skip_windows_resource_update
winmanifest.write_manifest_to_executable = _skip_windows_resource_update


a = Analysis(
    [str(PACKAGING / 'installer.py')],
    pathex=[],
    binaries=[],
    datas=[(str(PACKAGING / 'payload'), 'payload')],
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
    name='LifeDiaryInstaller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='NONE',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
