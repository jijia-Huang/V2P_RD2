# -*- coding: utf-8 -*-
"""
WebView UI 管理器
使用 pywebview 載入純 HTML/CSS/JS 介面，不依賴 Gradio
"""
import os
import sys
import json
import logging
import platform
import threading
import weakref
from pathlib import Path

try:
    import webview
except ImportError:
    logging.error("pywebview 未安裝，請執行: pip install pywebview")
    raise

from version import VERSION_STRING
from core.file_utils import get_application_path, get_videos_dir
from core.video import get_video_info
from ui.services import ConversionService


def check_webview2_runtime():
    """
    檢查 WebView2 Runtime 是否可用
    
    Returns:
        bool: True 如果 WebView2 Runtime 可用，False 否則
    """
    if platform.system() != "Windows":
        # 非 Windows 系統使用其他渲染引擎
        return True
    
    # 在 Windows 上，pywebview 會自動使用 WebView2
    # 如果 WebView2 不可用，webview.start() 會拋出異常
    try:
        import winreg
        # 檢查 WebView2 Runtime 註冊表項
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
            )
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            # 嘗試另一個註冊表路徑
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
                )
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                # 如果找不到註冊表項，可能未安裝，但讓 pywebview 自己處理
                return True
    except Exception as e:
        logging.warning(f"檢查 WebView2 Runtime 時發生錯誤: {str(e)}")
        return True


class WebViewAPI:
    """JavaScript-Python Bridge API"""
    
    def __init__(self, manager):
        # 使用弱引用避免循環引用和序列化問題
        self._manager_ref = weakref.ref(manager)  # 使用弱引用
        self._conversion_service = None  # 延遲初始化
    
    @property
    def _manager(self):
        """取得管理器實例（通過弱引用）"""
        manager = self._manager_ref()
        if manager is None:
            raise RuntimeError("管理器已被回收")
        return manager
    
    @property
    def config_manager(self):
        """取得配置管理器（動態訪問，避免序列化）"""
        return self._manager.config_manager
    
    @property
    def conversion_service(self):
        """取得轉換服務（延遲初始化）"""
        if self._conversion_service is None:
            self._conversion_service = ConversionService(self.config_manager)
        return self._conversion_service
    
    def __getstate__(self):
        """控制序列化，避免循環引用"""
        # 不序列化任何內容，pywebview 會重新創建對象
        # 弱引用無法序列化，所以返回空字典
        return {}
    
    def __setstate__(self, state):
        """反序列化"""
        # 這些屬性會在運行時重新設置
        self._manager_ref = None
        self._conversion_service = None
    
    def getVersion(self):
        """取得版本資訊"""
        return VERSION_STRING
    
    def getSettings(self):
        """取得設定"""
        return {
            "ffmpegPath": self.config_manager.get_ffmpeg_path() or "",
            "texturePackerPath": self.config_manager.get_texture_packer_path() or "",
            "tinypngKey": self.config_manager.get_tinypng_api_key() or ""
        }
    
    def getBgRemovalTolerance(self):
        """取得去背容差值"""
        return self.config_manager.get_preference("last_bg_removal_tolerance", 10)
    
    def getBgRemovalEnabled(self):
        """取得去背啟用狀態"""
        return self.config_manager.get_preference("last_bg_removal_enabled", False)
    
    def selectPath(self, tool_type):
        """選擇工具路徑（需要實作檔案選擇對話框）"""
        # 注意：pywebview 不直接支援檔案選擇對話框
        # 需要使用 Python 的 tkinter.filedialog 或類似的
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()  # 隱藏主視窗
            
            if tool_type == "ffmpeg":
                file_path = filedialog.askopenfilename(
                    title="選擇 FFmpeg 執行檔",
                    filetypes=[("執行檔", "*.exe"), ("所有檔案", "*.*")]
                )
                if file_path:
                    self.config_manager.set_ffmpeg_path(file_path)
                    self.config_manager.save_config()
            elif tool_type == "texturepacker":
                file_path = filedialog.askopenfilename(
                    title="選擇 TexturePacker 執行檔",
                    filetypes=[("執行檔", "*.exe"), ("所有檔案", "*.*")]
                )
                if file_path:
                    self.config_manager.set_texture_packer_path(file_path)
                    self.config_manager.save_config()
            
            root.destroy()
            return {"success": True, "path": file_path if file_path else ""}
        except Exception as e:
            logging.error(f"選擇路徑失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def saveSettings(self, params=None):
        """儲存設定"""
        try:
            if params:
                tinypng_key = params.get('tinypngKey', '')
                if tinypng_key:
                    self.config_manager.set_tinypng_api_key(tinypng_key)
                    self.config_manager.save_config()
            return {"success": True}
        except Exception as e:
            logging.error(f"儲存設定失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def getOutputPath(self, output_name):
        """取得輸出路徑"""
        try:
            from core.file_utils import get_videos_dir
            videos_dir = get_videos_dir()
            output_path = os.path.join(videos_dir, f"v2p_{output_name}")
            return output_path
        except Exception as e:
            logging.error(f"取得輸出路徑失敗: {str(e)}")
            return None
    
    def testTexturePacker(self, path):
        """測試 TexturePacker"""
        try:
            if not path:
                return {"success": False, "error": "請選擇 TexturePacker 執行檔"}
            version = self.config_manager.test_executable(path, "TexturePacker")
            if version and version != "":
                if version.startswith("TexturePacker"):
                    return {"success": True, "message": f"✅ TexturePacker 可用！\n版本：{version}"}
                else:
                    # 需要幫助輸入 agree
                    agree_result = self.config_manager.agree_texture_packer(path)
                    if agree_result == "ok":
                        return self.testTexturePacker(path)
                    else:
                        return {"success": False, "error": "❌ TexturePacker 無法執行"}
            else:
                return {"success": False, "error": "❌ TexturePacker 無法執行"}
        except Exception as e:
            logging.error(f"測試 TexturePacker 失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def getVideoInfo(self, filename):
        """取得影片資訊"""
        try:
            # 這裡需要完整的檔案路徑
            # JavaScript 需要傳遞完整路徑
            return None
        except Exception as e:
            logging.error(f"取得影片資訊失敗: {str(e)}")
            return None
    
    def extractPreviewFrames(self, params):
        """提取預覽影格"""
        try:
            video_path = params.get('videoPath')
            fps = params.get('fps', 24)
            
            if not video_path or not os.path.exists(video_path):
                return {"success": False, "error": "影片檔案不存在"}
            
            from core.video import extract_frames, get_video_dimensions
            import hashlib
            import glob
            
            # 創建預覽目錄
            video_hash = hashlib.md5(video_path.encode()).hexdigest()[:8]
            preview_base = os.path.join(get_application_path(), "preview")
            frames_dir = os.path.join(preview_base, f"bg_preview_{video_hash}")
            
            # 清理舊的預覽影格
            if os.path.exists(frames_dir):
                import shutil
                shutil.rmtree(frames_dir, ignore_errors=True)
            
            os.makedirs(frames_dir, exist_ok=True)
            
            logging.info(f"開始提取預覽影格：{video_path}，FPS={fps}")
            
            # 提取影格
            frame_count = extract_frames(
                video_path,
                frames_dir,
                fps,
                self.config_manager.get_ffmpeg_path(),
                "preview",
                output_format="PNG",
                quality=5
            )
            
            # 收集預覽影格路徑（最多12個）
            frame_paths = sorted(glob.glob(os.path.join(frames_dir, "*.png")))[:12]
            
            # 保存預覽資訊
            import time
            self.config_manager.save_preferences({
                "preview_frames_dir": frames_dir,
                "preview_frame_count": frame_count,
                "preview_fps": fps,
                "preview_video_path": video_path,
                "preview_update_time": time.time()
            })
            
            logging.info(f"預覽影格提取完成：{frame_count} 個影格")
            
            return {
                "success": True,
                "frameCount": frame_count,
                "frames": frame_paths
            }
        except Exception as e:
            logging.error(f"提取預覽影格失敗: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def selectVideoFile(self):
        """選擇影片檔案"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()  # 隱藏主視窗
            
            file_path = filedialog.askopenfilename(
                title="選擇 MP4 影片檔案",
                filetypes=[("MP4 檔案", "*.mp4"), ("所有檔案", "*.*")]
            )
            
            root.destroy()
            
            if file_path and os.path.exists(file_path):
                return {"success": True, "path": file_path}
            else:
                return {"success": False, "error": "未選擇檔案"}
        except Exception as e:
            logging.error(f"選擇檔案失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def convertVideo(self, params):
        """轉換影片"""
        try:
            video_path = params.get('videoPath')
            
            # 如果路徑不存在，嘗試從檔名尋找
            if not video_path or not os.path.exists(video_path):
                # 嘗試在常見位置尋找
                possible_paths = [
                    os.path.join(get_application_path(), video_path),
                    os.path.join(os.path.expanduser('~'), 'Downloads', video_path),
                    video_path
                ]
                
                video_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        video_path = path
                        break
                
                if not video_path:
                    return {"success": False, "error": "影片檔案不存在，請使用檔案選擇功能選擇檔案"}
            
            # 執行轉換
            result = self.conversion_service.convert(
                video=video_path,
                fps=params.get('fps', 24),
                output_name=params.get('outputName', 'output'),
                max_width=params.get('maxWidth', 2048),
                max_height=params.get('maxHeight', 2048),
                output_format=params.get('outputFormat', 'PNG'),
                quality=params.get('quality', 5),
                use_tinypng=params.get('useTinyPNG', False),
                packer_choice=params.get('packerChoice', '自動選擇'),
                enable_bg_removal=params.get('enableBgRemoval', False),
                bg_removal_tolerance=params.get('bgRemovalTolerance', 10),
                progress=None  # 暫時不支援進度回調
            )
            
            # 檢查結果
            logging.info(f"轉換結果類型：{type(result)}, 內容：{result}")
            
            if result:
                if isinstance(result, dict):
                    if result.get('success'):
                        return {
                            "success": True,
                            "outputPath": result.get('output_path', '')
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get('error', '轉換失敗')
                        }
                elif isinstance(result, str):
                    # 如果返回的是字串，檢查是否包含成功標記
                    if "✅" in result or "成功" in result:
                        return {
                            "success": True,
                            "outputPath": "videos 目錄"
                        }
                    else:
                        return {"success": False, "error": result}
                else:
                    # 其他類型的結果
                    return {"success": False, "error": f"未知結果類型：{type(result)}"}
            else:
                return {"success": False, "error": "轉換失敗：未返回結果"}
        except Exception as e:
            logging.error(f"轉換失敗: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def getOutputList(self):
        """取得輸出列表"""
        try:
            videos_dir = get_videos_dir()
            outputs = []
            
            if os.path.exists(videos_dir):
                for item in os.listdir(videos_dir):
                    item_path = os.path.join(videos_dir, item)
                    if os.path.isdir(item_path) and item.startswith('v2p_'):
                        outputs.append({
                            "name": item.replace('v2p_', ''),
                            "path": item_path
                        })
            
            return outputs
        except Exception as e:
            logging.error(f"取得輸出列表失敗: {str(e)}")
            return []
    
    def cleanupTempFiles(self):
        """清理臨時檔案"""
        try:
            temp_dir = os.path.join(get_application_path(), 'temp')
            if os.path.exists(temp_dir):
                import shutil
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
            return {"success": True}
        except Exception as e:
            logging.error(f"清理臨時檔案失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def cleanupOldFiles(self, days):
        """清理舊檔案"""
        try:
            from core.config import ConfigManager
            self.config_manager.cleanup_old_files(days)
            return {"success": True}
        except Exception as e:
            logging.error(f"清理舊檔案失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def analyzeDiskUsage(self):
        """分析磁碟使用"""
        try:
            import shutil
            videos_dir = get_videos_dir()
            if os.path.exists(videos_dir):
                total_size = 0
                for root, dirs, files in os.walk(videos_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                        except:
                            pass
                
                # 格式化大小
                def format_size(size):
                    for unit in ['B', 'KB', 'MB', 'GB']:
                        if size < 1024.0:
                            return f"{size:.2f} {unit}"
                        size /= 1024.0
                    return f"{size:.2f} TB"
                
                disk = shutil.disk_usage(videos_dir)
                return {
                    "success": True,
                    "totalSize": format_size(disk.total),
                    "usedSize": format_size(disk.used),
                    "freeSize": format_size(disk.free)
                }
            return {"success": False, "error": "輸出目錄不存在"}
        except Exception as e:
            logging.error(f"分析磁碟使用失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def openOutputFolder(self):
        """開啟輸出資料夾"""
        try:
            import subprocess
            import platform
            videos_dir = get_videos_dir()
            if os.path.exists(videos_dir):
                if platform.system() == "Windows":
                    os.startfile(videos_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", videos_dir])
                else:  # Linux
                    subprocess.Popen(["xdg-open", videos_dir])
                return {"success": True}
            return {"success": False, "error": "輸出目錄不存在"}
        except Exception as e:
            logging.error(f"開啟輸出資料夾失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def loadPreviewFrames(self):
        """載入預覽影格"""
        try:
            import glob
            
            # 從偏好設定讀取預覽影格資訊
            preview_frames_dir = self.config_manager.get_preference("preview_frames_dir", "")
            preview_frame_count = self.config_manager.get_preference("preview_frame_count", 0)
            preview_fps = self.config_manager.get_preference("preview_fps", 24)
            preview_video_path = self.config_manager.get_preference("preview_video_path", "")
            
            if (preview_frames_dir and 
                os.path.exists(preview_frames_dir) and 
                preview_frame_count > 0):
                
                # 獲取影格檔案列表（排除 filter_ 前綴的去背檔案）
                all_png_files = sorted(glob.glob(os.path.join(preview_frames_dir, "*.png")))
                frame_files = [f for f in all_png_files if not os.path.basename(f).startswith('filter_')]
                
                video_name = os.path.basename(preview_video_path) if preview_video_path else "未知"
                
                return {
                    "success": True,
                    "frames": frame_files,
                    "frameCount": len(frame_files),
                    "fps": preview_fps,
                    "videoName": video_name
                }
            
            return {
                "success": True,
                "frames": [],
                "frameCount": 0,
                "fps": 24,
                "videoName": ""
            }
        except Exception as e:
            logging.error(f"載入預覽影格失敗: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def previewBgRemovalFrame(self, params):
        """預覽去背影格"""
        try:
            frame_path = params.get('framePath')
            tolerance = params.get('tolerance', 10)
            
            if not frame_path or not os.path.exists(frame_path):
                return {"success": False, "error": "影格檔案不存在"}
            
            from core.filter import preview_single_frame
            
            # 處理影格
            original_img, processed_img = preview_single_frame(
                frame_path,
                bg_color=None,
                tolerance=tolerance,
                auto_detect=True
            )
            
            # 保存臨時圖片供預覽
            import tempfile
            temp_dir = os.path.join(get_application_path(), "preview", "temp_preview")
            os.makedirs(temp_dir, exist_ok=True)
            
            frame_name = os.path.splitext(os.path.basename(frame_path))[0]
            original_path = os.path.join(temp_dir, f"{frame_name}_original.png")
            processed_path = os.path.join(temp_dir, f"{frame_name}_processed_t{tolerance}.png")
            
            original_img.save(original_path, 'PNG')
            processed_img.save(processed_path, 'PNG')
            
            return {
                "success": True,
                "originalPath": original_path,
                "processedPath": processed_path
            }
        except Exception as e:
            logging.error(f"預覽去背影格失敗: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def savePreviewImage(self, params):
        """保存預覽圖片"""
        try:
            frame_path = params.get('framePath')
            tolerance = params.get('tolerance', 10)
            
            if not frame_path or not os.path.exists(frame_path):
                return {"success": False, "error": "影格檔案不存在"}
            
            from core.filter import preview_single_frame
            
            # 處理影格
            _, processed_img = preview_single_frame(
                frame_path,
                bg_color=None,
                tolerance=tolerance,
                auto_detect=True
            )
            
            # 保存到 videos 目錄
            videos_dir = get_videos_dir()
            os.makedirs(videos_dir, exist_ok=True)
            
            frame_name = os.path.splitext(os.path.basename(frame_path))[0]
            output_filename = f"preview_{frame_name}_tolerance{tolerance}.png"
            output_path = os.path.join(videos_dir, output_filename)
            
            processed_img.save(output_path, 'PNG')
            
            logging.info(f"已保存預覽圖片：{output_path}")
            
            return {
                "success": True,
                "outputPath": output_path
            }
        except Exception as e:
            logging.error(f"保存預覽圖片失敗: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}


class WebViewUIManager:
    """WebView UI 管理器 - 使用純 HTML/CSS/JS，不依賴 Gradio"""
    
    def __init__(self, config_manager):
        """
        初始化 WebView UI 管理器
        
        Args:
            config_manager: ConfigManager 實例
        """
        logging.info("初始化 WebView UI 管理器（獨立版本）")
        self.config_manager = config_manager
        # 不設置 ui_manager，避免循環引用導致序列化問題
        # self.config_manager.ui_manager = self  # 註釋掉，避免循環引用
        
        # WebView 相關
        self.webview_window = None
        self.api = WebViewAPI(self)
        
    def _get_html_path(self):
        """取得 HTML 檔案路徑"""
        app_path = get_application_path()
        html_path = os.path.join(app_path, 'ui', 'webview', 'static', 'index.html')
        return html_path
    
    def _get_static_dir(self):
        """取得靜態資源目錄路徑"""
        app_path = get_application_path()
        static_dir = os.path.join(app_path, 'ui', 'webview', 'static')
        return static_dir
    
    def run(self, port=None, window_size=(1400, 900), debug=False):
        """
        啟動 WebView UI
        
        Args:
            port: 未使用（保留以相容現有介面）
            window_size: 視窗大小 (width, height)，預設為 (1400, 900)
            debug: 是否啟用調試模式（開發者工具），預設為 False
        """
        html_path = self._get_html_path()
        
        if not os.path.exists(html_path):
            error_msg = f"HTML 檔案不存在：{html_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # 直接使用 HTML 檔案的 file:// URL
        # CSS 和 JS 使用相對路徑，因為它們在同一個目錄下
        html_url = Path(html_path).as_uri()
        
        try:
            # 建立 WebView 視窗
            logging.info(f"建立 WebView 視窗，載入 {html_url}")
            
            self.webview_window = webview.create_window(
                title=f"V2P 工具 {VERSION_STRING}",
                url=html_url,
                width=window_size[0],
                height=window_size[1],
                min_size=(800, 600),
                resizable=True,
                js_api=self.api  # 暴露 API 給 JavaScript
            )
            
            # 監聽視窗關閉事件
            def on_closed():
                """視窗關閉時的回調函數"""
                logging.info("WebView 視窗已關閉，正在退出程式...")
                # 清理資源
                self.webview_window = None
                # 強制退出程式
                os._exit(0)
            
            # 訂閱視窗關閉事件
            self.webview_window.events.closed += on_closed
            
            # 啟動 WebView
            logging.info(f"啟動 WebView UI (debug={debug})")
            if debug:
                logging.info("開發者工具已啟用，按 F12 或右鍵選擇「檢查」可打開開發者工具")
            
            # webview.start() 會阻塞直到所有視窗關閉
            # 當視窗關閉時，webview.start() 會返回
            webview.start(debug=debug)
            
            # 當 webview.start() 返回時（視窗已關閉），退出程式
            # 這是一個備用退出機制，以防事件處理失敗
            logging.info("WebView 視窗已關閉，正在退出程式...")
            os._exit(0)
            
        except KeyboardInterrupt:
            logging.info("使用者中斷（Ctrl+C）")
            os._exit(0)
        except Exception as e:
            error_msg = str(e)
            # 檢查是否為 WebView2 Runtime 相關錯誤
            if "webview2" in error_msg.lower() or "webview" in error_msg.lower():
                full_error_msg = (
                    "無法啟動 WebView UI：WebView2 Runtime 未安裝或不可用。\n\n"
                    "請安裝 Microsoft Edge WebView2 Runtime：\n"
                    "https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
                    "或者使用瀏覽器模式：python v2p.py --ui gradio"
                )
                logging.error(full_error_msg)
                print(f"\n❌ {full_error_msg}\n")
            else:
                logging.error(f"WebView UI 啟動失敗: {error_msg}", exc_info=True)
                print(f"\n❌ WebView UI 啟動失敗: {error_msg}\n")
            raise
