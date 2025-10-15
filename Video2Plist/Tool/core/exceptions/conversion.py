"""
轉換相關錯誤
"""
from ..error_handler import V2PError, ErrorType

class ConversionError(V2PError):
    """轉換相關錯誤"""
    def __init__(self, message, details=None):
        super().__init__(message, ErrorType.CONVERSION, details) 