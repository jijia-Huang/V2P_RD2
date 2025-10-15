"""
錯誤處理模組
"""
import logging
from enum import Enum

class ErrorType(Enum):
    CONFIG = "設定錯誤"
    FILE = "檔案錯誤"
    CONVERSION = "轉換錯誤"
    VERSION = "版本錯誤"
    SYSTEM = "系統錯誤"

class V2PError(Exception):
    """V2P 工具的基礎錯誤類"""
    def __init__(self, message, error_type=ErrorType.SYSTEM, details=None):
        self.message = message
        self.error_type = error_type
        self.details = details
        super().__init__(self.message)

def handle_error(error, ui_component=None):
    """統一的錯誤處理函數"""
    if isinstance(error, V2PError):
        message = f"❌ {error.error_type.value}：{error.message}"
        logging.error(f"{error.error_type.value} - {error.message}")
        if error.details:
            logging.debug(f"詳細資訊：{error.details}")
    else:
        message = f"❌ 未預期的錯誤：{str(error)}"
        logging.error(f"未預期的錯誤：{str(error)}")
    
    if ui_component:
        return message
    return None 