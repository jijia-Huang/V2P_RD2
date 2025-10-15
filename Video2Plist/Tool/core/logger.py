# -*- coding: utf-8 -*-
"""
日誌處理模組
"""
import os
import logging
from datetime import datetime
from .file_utils import get_application_path

def get_log_path():
    """獲取日誌檔案路徑"""
    log_dir = os.path.join(get_application_path(), "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    date_str = datetime.now().strftime('%Y%m%d')
    return os.path.join(log_dir, f"v2p_{date_str}.log")

def setup_logger(log_level=logging.INFO):
    """設定日誌處理器"""
    try:
        # 獲取根記錄器
        logger = logging.getLogger()
        logger.setLevel(log_level)  # 設置根記錄器級別
        
        # 清除現有的處理器，避免重複
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 設定格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 檔案處理器
        file_handler = logging.FileHandler(
            filename=get_log_path(),
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 記錄初始設定
        logging.info(f"日誌級別設置為：{logging.getLevelName(log_level)}")
        
    except Exception as e:
        print(f"設定日誌處理器失敗：{str(e)}")
        raise 