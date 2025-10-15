"""
檔案相關錯誤
"""
from ..error_handler import V2PError, ErrorType

class FileError(V2PError):
    """檔案相關錯誤"""
    def __init__(self, message, details=None):
        super().__init__(message, ErrorType.FILE, details) 