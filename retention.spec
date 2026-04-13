# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        (r'C:\Users\kayas\AppData\Roaming\Python\Python314\site-packages\xgboost\lib\xgboost.dll', 'xgboost/lib'),
    ],
    datas=[
        ('assets/styles.qss', 'assets'),
        ('datasets', 'datasets'),
        (r'C:\Users\kayas\AppData\Roaming\Python\Python314\site-packages\xgboost\VERSION', 'xgboost'),
    ],
    hiddenimports=[
        'sklearn.utils._typedefs',
        'sklearn.utils._heap',
        'sklearn.utils._sorting',
        'sklearn.utils._vector_sentinel',
        'sklearn.neighbors._partition_nodes',
        'xgboost',
        'xgboost.sklearn',
        'xgboost.training',
        'sqlalchemy.dialects.sqlite',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.workbook',
        'openpyxl.reader.excel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RetentionOptimizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RetentionOptimizer',
)
