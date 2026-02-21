# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pluggy',
        'iniconfig',
        'setuptools',
        'pip',
        'Pygments',
        '_pytest',
        'pre_commit',
        'ruff',
        'unittest',
        'pydoc',
        'doctest',
        'tkinter',
        'xmlrpc',
        'pdb',
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clicky',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icons/app.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    name='clicky',
)
app = BUNDLE(
    coll,
    name='clicky.app',
    icon='./assets/icons/app.icns',
    bundle_identifier=None,
)
