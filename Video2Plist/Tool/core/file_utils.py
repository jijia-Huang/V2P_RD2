# -*- coding: utf-8 -*-
"""
檔案處理相關功能
"""
import os
import sys
import logging
from .exceptions import FileError

def get_application_path():
    """獲取應用程式路徑"""
    try:
        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(sys.executable)
        else:
            app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        logging.debug(f"應用程式路徑：{app_path}")
        return app_path
        
    except Exception as e:
        logging.error(f"獲取應用程式路徑失敗：{str(e)}", exc_info=True)
        raise FileError(
            "無法獲取應用程式路徑",
            details=str(e)
        )

def get_videos_dir():
    """獲取影片輸出目錄"""
    try:
        videos_dir = os.path.join(get_application_path(), "videos")
        logging.debug(f"影片輸出目錄：{videos_dir}")
        return videos_dir
        
    except FileError:
        raise
    except Exception as e:
        logging.error(f"獲取輸出目錄失敗：{str(e)}", exc_info=True)
        raise FileError(
            "無法獲取輸出目錄",
            details=str(e)
        )

def get_output_dir(subfolder):
    """獲取指定子資料夾的完整路徑"""
    try:
        if not subfolder:
            logging.error("子資料夾名稱為空")
            raise FileError("子資料夾名稱不能為空")
            
        # 驗證資料夾名稱
        invalid_chars = '<>:"/\\|?*'
        if any(c in subfolder for c in invalid_chars):
            logging.error(f"資料夾名稱包含無效字符：{subfolder}")
            raise FileError(
                "資料夾名稱包含無效字符",
                details=f"不能包含以下字符：{invalid_chars}"
            )
            
        output_dir = os.path.join(get_videos_dir(), subfolder)
        logging.debug(f"輸出目錄路徑：{output_dir}")
        return output_dir
        
    except FileError:
        raise
    except Exception as e:
        logging.error(f"獲取輸出目錄路徑失敗：{str(e)}", exc_info=True)
        raise FileError(
            "無法獲取輸出目錄路徑",
            details=str(e)
        )

def ensure_output_dir(subfolder):
    """確保輸出目錄存在"""
    try:
        output_dir = get_output_dir(subfolder)
        logging.info(f"建立輸出目錄：{output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
        
    except FileError:
        raise
    except Exception as e:
        logging.error(f"建立輸出目錄失敗：{str(e)}", exc_info=True)
        raise FileError(
            "無法建立輸出目錄",
            details=str(e)
        ) 