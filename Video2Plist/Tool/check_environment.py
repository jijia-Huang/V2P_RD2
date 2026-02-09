#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
檢查打包環境的腳本
用於確認 PyInstaller 和依賴套件是否在正確的環境中
"""

import sys
import os

print("=" * 60)
print("環境檢查")
print("=" * 60)

print(f"\nPython 執行檔路徑：{sys.executable}")
print(f"Python 版本：{sys.version}")
print(f"Python 版本資訊：{sys.version_info}")

print("\n" + "=" * 60)
print("檢查必要套件")
print("=" * 60)

packages = [
    'pyinstaller',
    'webview',
    'PIL',
    'yaml',
    'tinify',
    'cv2',
    'numpy',
    'packaging',
]

for package in packages:
    try:
        if package == 'webview':
            import webview
            print(f"✓ {package}: {webview.__version__ if hasattr(webview, '__version__') else '已安裝'}")
        elif package == 'PIL':
            import PIL
            print(f"✓ {package}: {PIL.__version__}")
        elif package == 'yaml':
            import yaml
            print(f"✓ {package}: {yaml.__version__}")
        elif package == 'cv2':
            import cv2
            print(f"✓ {package}: {cv2.__version__}")
        elif package == 'numpy':
            import numpy
            print(f"✓ {package}: {numpy.__version__}")
        elif package == 'packaging':
            import packaging
            print(f"✓ {package}: {packaging.__version__}")
        elif package == 'pyinstaller':
            import PyInstaller
            print(f"✓ {package}: {PyInstaller.__version__}")
        else:
            module = __import__(package)
            version = getattr(module, '__version__', '已安裝')
            print(f"✓ {package}: {version}")
    except ImportError as e:
        print(f"✗ {package}: 未安裝 - {e}")

print("\n" + "=" * 60)
print("檢查 PyInstaller 是否能找到 webview")
print("=" * 60)

try:
    from PyInstaller.utils.hooks import collect_submodules, collect_data_files
    
    webview_submodules = collect_submodules('webview')
    webview_datas = collect_data_files('webview')
    
    print(f"✓ webview 子模組數量：{len(webview_submodules)}")
    print(f"✓ webview 資料檔案數量：{len(webview_datas)}")
    
    if webview_submodules:
        print("\n前 10 個 webview 子模組：")
        for mod in list(webview_submodules)[:10]:
            print(f"  - {mod}")
    
except Exception as e:
    print(f"✗ 無法收集 webview 模組：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("建議")
print("=" * 60)
print("1. 確保在正確的 conda 環境中執行 PyInstaller")
print("2. 使用以下命令確認環境：")
print("   conda activate <your_env>")
print("   python check_environment.py")
print("   pyinstaller v2p.spec")
print("3. 如果 PyInstaller 不在當前環境，請安裝：")
print("   conda install pyinstaller")
print("   或")
print("   pip install pyinstaller")

