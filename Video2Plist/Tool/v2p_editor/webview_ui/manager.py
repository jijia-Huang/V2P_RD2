# -*- coding: utf-8 -*-
"""
V2P Editor WebView UI 管理器
使用 pywebview 載入純 HTML/CSS/JS 介面
"""
import os
import sys
import json
import logging
import platform
import base64
import io
import weakref
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import webview
except ImportError:
    logging.error("pywebview 未安裝，請執行: pip install pywebview")
    raise

from PIL import Image

try:
    from ..inspector import FramePreview, InspectionReport, ProjectInspector
except ImportError:
    # 當作為獨立模組運行時
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from inspector import FramePreview, InspectionReport, ProjectInspector


class WebViewAPI:
    """JavaScript-Python Bridge API for V2P Editor"""
    
    def __init__(self, manager):
        # 使用弱引用避免循環引用和序列化問題
        self._manager_ref = weakref.ref(manager)
        self.inspector = ProjectInspector()
        self.report: Optional[InspectionReport] = None
    
    @property
    def _manager(self):
        """取得管理器實例（通過弱引用）"""
        manager = self._manager_ref()
        if manager is None:
            raise RuntimeError("管理器已被回收")
        return manager
    
    def __getstate__(self):
        """控制序列化，避免循環引用"""
        # 不序列化任何內容，pywebview 會重新創建對象
        # 弱引用無法序列化，所以返回空字典
        return {}
    
    def __setstate__(self, state):
        """反序列化"""
        # 這些屬性會在運行時重新設置
        self._manager_ref = None
        self.inspector = None
        self.report = None
    
    def inspectFolder(self, folder_path: str) -> Dict[str, Any]:
        """檢查 V2P 輸出資料夾"""
        try:
            self.report = self.inspector.inspect(folder_path)
            return {
                "success": True,
                "report": {
                    "name": self.report.name,
                    "folder": str(self.report.folder),
                    "metadata": self.report.metadata,
                    "frames_count": len(self.report.frames),
                    "file_status": [
                        {
                            "label": status.label,
                            "path": status.path,
                            "exists": status.exists,
                            "extra": status.extra,
                        }
                        for status in self.report.file_status
                    ],
                    "errors": self.report.errors,
                    "warnings": self.report.warnings,
                }
            }
        except Exception as e:
            logging.error(f"檢查資料夾失敗: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def getReport(self) -> Dict[str, Any]:
        """取得檢查報告"""
        if not self.report:
            return {
                "success": False,
                "error": "尚未載入任何報告"
            }
        return {
            "success": True,
            "report": self.report.to_dict()
        }
    
    def selectFolder(self) -> Dict[str, Any]:
        """選擇資料夾"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()  # 隱藏主視窗
            
            folder_path = filedialog.askdirectory(
                title="選擇 V2P 輸出資料夾"
            )
            
            root.destroy()
            
            if folder_path:
                return {
                    "success": True,
                    "path": folder_path
                }
            else:
                return {
                    "success": False,
                    "error": "未選擇資料夾"
                }
        except Exception as e:
            logging.error(f"選擇資料夾失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def copyReport(self) -> Dict[str, Any]:
        """複製報告到剪貼簿"""
        if not self.report:
            return {
                "success": False,
                "error": "尚未載入任何報告"
            }
        try:
            import tkinter as tk
            
            root = tk.Tk()
            root.withdraw()
            
            data = self.report.to_dict()
            text = json.dumps(data, indent=2, ensure_ascii=False)
            
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()  # 確保剪貼簿更新
            root.destroy()
            
            return {
                "success": True,
                "message": "已複製 JSON 報告到剪貼簿"
            }
        except Exception as e:
            logging.error(f"複製報告失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def getFrameImage(self, frame_index: int) -> Dict[str, Any]:
        """取得影格圖片（base64）"""
        if not self.report or not self.report.frames:
            return {
                "success": False,
                "error": "沒有可用的影格"
            }
        
        try:
            frame_index = int(frame_index)
            if frame_index < 0 or frame_index >= len(self.report.frames):
                return {
                    "success": False,
                    "error": f"影格索引超出範圍: {frame_index}"
                }
            
            frame = self.report.frames[frame_index]
            
            # 調整圖片大小（最大 640x640）
            max_size = 640
            image = frame.image.copy()
            width, height = image.size
            scale = min(max_size / width, max_size / height, 1.0)
            
            if scale < 1.0:
                new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
                image = image.resize(new_size, Image.LANCZOS)
            
            # 轉換為 base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            return {
                "success": True,
                "image": f"data:image/png;base64,{img_base64}",
                "size": image.size,
                "frame_info": {
                    "index": frame.index,
                    "name": frame.name,
                    "sheet": frame.sheet,
                    "size": frame.size,
                    "rotated": frame.rotated,
                }
            }
        except Exception as e:
            logging.error(f"取得影格圖片失敗: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def getFramesList(self) -> Dict[str, Any]:
        """取得所有影格列表"""
        if not self.report or not self.report.frames:
            return {
                "success": True,
                "frames": []
            }
        
        frames_list = []
        for idx, frame in enumerate(self.report.frames):
            frames_list.append({
                "index": idx,
                "frame_index": frame.index,
                "name": frame.name,
                "sheet": frame.sheet,
                "size": f"{frame.size[0]}x{frame.size[1]}",
                "rotated": frame.rotated,
            })
        
        return {
            "success": True,
            "frames": frames_list
        }


class WebViewUIManager:
    """WebView UI 管理器"""
    
    def __init__(self):
        self.api = WebViewAPI(self)
        self._base_path = None
        self._static_dir = None
        self._html_path = None
    
    def _get_base_path(self) -> Path:
        """取得基礎路徑（緩存結果）"""
        if self._base_path is None:
            if getattr(sys, 'frozen', False):
                # PyInstaller 打包環境：資源在 sys._MEIPASS
                if hasattr(sys, '_MEIPASS'):
                    self._base_path = Path(sys._MEIPASS)
                else:
                    # 如果沒有 _MEIPASS，使用執行檔所在目錄
                    self._base_path = Path(os.path.dirname(sys.executable))
            else:
                # 開發環境：使用當前檔案路徑
                current_file = Path(__file__).resolve()
                self._base_path = current_file.parent.parent
        
        return self._base_path
    
    def _get_static_dir(self) -> Path:
        """取得靜態檔案目錄（緩存結果）"""
        if self._static_dir is None:
            base_path = self._get_base_path()
            if getattr(sys, 'frozen', False):
                self._static_dir = base_path / "v2p_editor" / "webview_ui" / "static"
            else:
                self._static_dir = base_path / "webview_ui" / "static"
            
            # 只在調試模式下檢查目錄存在性
            if logging.getLogger().level <= logging.DEBUG:
                if not self._static_dir.exists():
                    logging.error(f"靜態資源目錄不存在：{self._static_dir}")
                    logging.error(f"sys.frozen: {getattr(sys, 'frozen', False)}")
                    logging.error(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
        
        return self._static_dir
    
    def _get_html_path(self) -> Path:
        """取得 HTML 檔案路徑（緩存結果）"""
        if self._html_path is None:
            self._html_path = self._get_static_dir() / "index.html"
        return self._html_path
    
    def run(self, initial_path: Optional[str] = None, window_size=(1280, 780), debug=False):
        """
        啟動 WebView UI
        
        Args:
            initial_path: 初始載入的資料夾路徑
            window_size: 視窗大小 (width, height)，預設為 (1280, 780)
            debug: 是否啟用調試模式（開發者工具），預設為 False
        """
        html_path = self._get_html_path()
        
        if not html_path.exists():
            error_msg = f"HTML 檔案不存在：{html_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # 直接使用 HTML 檔案的 file:// URL
        html_url = html_path.as_uri()
        
        try:
            # 建立 WebView 視窗
            logging.info(f"啟動 V2P Editor WebView UI: {html_url}")
            
            # 建立視窗
            window = webview.create_window(
                title="V2P Editor Viewer",
                url=html_url,
                width=window_size[0],
                height=window_size[1],
                min_size=(960, 640),
                js_api=self.api
            )
            
            # 如果提供了初始路徑，在頁面載入後自動載入
            if initial_path:
                # 轉換路徑格式（Windows 路徑轉為正斜槓，並轉義單引號）
                escaped_path = initial_path.replace('\\', '/').replace("'", "\\'")
                
                def on_loaded():
                    # 等待頁面載入完成後自動載入資料夾
                    import time
                    time.sleep(0.5)  # 給頁面一點時間初始化
                    try:
                        window.evaluate_js(f"loadFolder('{escaped_path}')")
                    except Exception as e:
                        logging.warning(f"自動載入資料夾失敗: {str(e)}")
                
                window.loaded += on_loaded
            
            # 啟動 WebView
            webview.start(debug=debug)
            
        except Exception as e:
            error_msg = str(e)
            # 檢查是否為 WebView2 Runtime 相關錯誤
            if "webview2" in error_msg.lower() or "webview" in error_msg.lower():
                full_error_msg = (
                    "無法啟動 WebView UI：WebView2 Runtime 未安裝或不可用。\n\n"
                    "請安裝 Microsoft Edge WebView2 Runtime：\n"
                    "https://developer.microsoft.com/microsoft-edge/webview2/"
                )
                logging.error(full_error_msg)
                print(f"\n❌ {full_error_msg}\n")
            else:
                logging.error(f"WebView UI 啟動失敗: {error_msg}", exc_info=True)
                print(f"\n❌ WebView UI 啟動失敗: {error_msg}\n")
            raise


def launch_viewer(initial_path: Optional[str] = None):
    """啟動 V2P Editor Viewer"""
    manager = WebViewUIManager()
    manager.run(initial_path=initial_path)

