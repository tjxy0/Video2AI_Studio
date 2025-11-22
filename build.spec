# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys
import os

# -----------------------------------------------------------------------------
# 1. 配置设置
# -----------------------------------------------------------------------------
block_cipher = None
app_name = 'Video2AI_Studio'
main_script = 'main.py'

# -----------------------------------------------------------------------------
# 2. 收集依赖库的资源文件
# -----------------------------------------------------------------------------
# 初始化 datas, binaries, hiddenimports
datas = []
binaries = []
hiddenimports = [
    'scipy.special',
    'scipy.spatial.transform._rotation_groups',
    'sklearn.utils._cython_blas',
    'sklearn.neighbors.typedefs',
    'sklearn.neighbors.quad_tree',
    'sklearn.tree',
    'sklearn.tree._utils',
]

# 收集 PyQt-Fluent-Widgets 的资源 (主题、图标等)
tmp_ret = collect_all('qfluentwidgets')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 收集 ControlNet Aux 的数据 (避免预处理器加载失败)
tmp_ret = collect_all('controlnet_aux')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 收集 Diffusers 和 Transformers (防止动态加载失败)
tmp_ret = collect_all('diffusers')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('transformers')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# -----------------------------------------------------------------------------
# 3. 添加项目自定义文件
# -----------------------------------------------------------------------------
# 格式: ('本地路径', '打包后的相对路径')
datas.append(('configs', 'configs'))  # 包含 v1-inference.yaml

# 如果有 assets 文件夹 (图标等)，取消下面注释
# if os.path.exists('assets'):
#     datas.append(('assets', 'assets'))

# -----------------------------------------------------------------------------
# 4. Analysis - 分析脚本依赖
# -----------------------------------------------------------------------------
a = Analysis(
    [main_script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'IPython', 'jupyter', 'notebook'], # 排除不必要的包以减小体积
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# -----------------------------------------------------------------------------
# 5. PYZ - 创建 Python 压缩包
# -----------------------------------------------------------------------------
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# -----------------------------------------------------------------------------
# 6. EXE - 生成可执行文件
# -----------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True, # 推荐使用目录模式 (Onedir)，因为 PyTorch 太大了
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # 调试阶段建议设为 True，发布时设为 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico', # 如果有图标文件，请取消注释
)

# -----------------------------------------------------------------------------
# 7. COLLECT - 收集文件夹 (Onedir 模式)
# -----------------------------------------------------------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)