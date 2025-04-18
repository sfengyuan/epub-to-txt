# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # 入口文件
    pathex=[],     # 项目路径
    binaries=[],
    datas=[('book.ico', '.')],       # 需要包含的静态文件
    hiddenimports=[
        'bs4',          # BeautifulSoup可能被误判为未使用
        'defusedxml',   # 显式声明隐藏依赖
        'epub_to_txt',   # 核心模块
        'chardet'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EPUB2TXT',          # 生成的EXE名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                 # 启用压缩（需安装UPX）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,            # 不显示控制台窗口
    icon='book.ico',          # 可选的图标文件
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
