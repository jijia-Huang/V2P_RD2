"""
設定相關錯誤
"""
from ..error_handler import V2PError, ErrorType

class ConfigError(V2PError):
    """設定相關錯誤"""
    def __init__(self, message, details=None):
        super().__init__(message, ErrorType.CONFIG, details) 