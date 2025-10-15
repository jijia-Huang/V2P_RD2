# -*- coding: utf-8 -*-
"""
版本控制模組
"""
import os
import sys
import logging
import importlib

# 主版本號
VERSION = {
    'major': 1,    # 重大更新，可能不相容
    'minor': 1,    # 新功能，但向下相容
    'patch': 0     # 錯誤修復
}

# 版本號字串
VERSION_STRING = f"v{VERSION['major']}.{VERSION['minor']}.{VERSION['patch']}"

# 構建資訊
BUILD_INFO = {
    'date': '2025-10-09',          # 更新發布日期
    'min_gradio': '5.16.2',        # 最低需求的 gradio 版本
    'min_python': '3.8'            # 最低需求的 python 版本
}

def get_version():
    """獲取當前版本號"""
    return f"{VERSION['major']}.{VERSION['minor']}.{VERSION['patch']}"

def get_version_info():
    """獲取完整版本資訊"""
    return {
        'version': VERSION_STRING,
        **BUILD_INFO
    }

def check_compatibility():
    """檢查相容性"""
    try:
        logging.info("開始檢查相容性")
        
        # 檢查必要套件是否可以導入
        required_packages = ['gradio', 'packaging']
        for package in required_packages:
            try:
                importlib.import_module(package)
                logging.debug(f"成功導入套件：{package}")
            except ImportError as e:
                logging.error(f"找不到套件：{package}")
                return False, f"找不到必要的套件：{package}"
        
        # 檢查 Python 版本
        current_python = sys.version_info[:2]
        required_python = (3, 8)
        
        logging.debug(f"Python 版本：目前={current_python}, 需求={required_python}")
        if current_python < required_python:
            logging.error(f"Python 版本不相容：需要 {required_python}，目前為 {current_python}")
            return False, f"Python 版本過低（需要 3.8 以上，目前為 {current_python[0]}.{current_python[1]}）"
        
        logging.info("相容性檢查通過")
        return True, "相容性檢查通過"
        
    except Exception as e:
        logging.error(f"相容性檢查失敗：{str(e)}", exc_info=True)
        return False, f"相容性檢查失敗：{str(e)}" 