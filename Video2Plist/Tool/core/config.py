# -*- coding: utf-8 -*-
"""
設定管理模組
"""
import os
import yaml
import json
import logging
import subprocess
import time
from .file_utils import get_application_path
from .exceptions import ConfigError, FileError
from version import get_version

# 預設設定
DEFAULT_CONFIG = {
    "ffmpeg_path": "",  # 保持空白，讓程式自動尋找
    "texture_packer_path": "",
    "tinypng_api_key": "",  # TinyPNG API 金鑰
}

class ConfigManager:
    """設定管理器"""
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.preferences = {}
        self.ui_manager = None  # 添加 UI 管理器引用
        self.load_config()
        self.load_preferences()
        self._check_config_version()
        self._init_tinypng_api()
    
    def _check_config_version(self):
        """檢查配置文件版本"""
        if not self.preferences.get('last_version'):
            # 首次使用，記錄版本
            self.save_preferences({'last_version': get_version()})
            return
        
        last_version = self.preferences['last_version']
        current_version = get_version()
        
        if last_version != current_version:
            logging.info(f"工具版本已更新：{last_version} -> {current_version}")
            # 這裡可以添加配置升級邏輯
            self.save_preferences({'last_version': current_version})
    
    def test_executable(self, path, program_type):
        """測試執行檔是否可用"""
        logging.info(f"測試執行檔：{program_type} - {path}")
        
        if not path or not os.path.exists(path):
            logging.error(f"找不到執行檔：{program_type} - {path}")
            raise ConfigError(
                f"找不到 {program_type} 執行檔",
                details=f"路徑：{path}"
            )
        
        try:
            if program_type == "TexturePacker":
                logging.info("執行 TexturePacker 版本檢查")
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=2,
                )
                if result.returncode != 0:
                    logging.error(f"TexturePacker 執行失敗：{result.stderr}")
                    raise ConfigError(f"{program_type} 執行失敗")
                version = result.stdout.strip()
                logging.info(f"TexturePacker 版本：{version}")
                return version
            else:
                logging.error(f"不支援的程式類型：{program_type}")
                raise ConfigError(f"不支援的程式類型：{program_type}")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"執行失敗：{str(e)}\n{e.stderr}")
            raise ConfigError(
                f"執行失敗：{program_type}",
                details=str(e)
            )
        except subprocess.TimeoutExpired as e:
            logging.error(f"執行超時：{str(e)}", exc_info=True)
            return "timeout"
            # raise ConfigError(
            #     f"執行超時：{program_type}",
            #     details=str(e)
            # )
        except Exception as e:
            logging.error(f"測試失敗：{str(e)}", exc_info=True)
            raise ConfigError(
                f"測試失敗：{program_type}",
                details=str(e)
            )

    def agree_texture_packer(self, path):
        """同意 TexturePacker 第一次執行 Console 的輸出"""
        logging.info(f"同意 TexturePacker 第一次執行 Console 的輸出：{path}")

        if not path or not os.path.exists(path):
            logging.error(f"找不到執行檔：{path}")
            raise ConfigError(
                f"找不到執行檔",
                details=f"路徑：{path}"
            )
        try:
            subprocess.run(
                [path], 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore', 
                timeout=2,
                input='agree')
            return "ok"
        except subprocess.TimeoutExpired as e:
            logging.error(f"執行超時：{str(e)}", exc_info=True)
            raise ConfigError(
                f"執行超時",
                details=str(e)
            )
        except Exception as e:
            logging.error(f"執行失敗：{str(e)}", exc_info=True)
            raise ConfigError(
                f"執行失敗",
                details=str(e)
            )
        
    
    def load_config(self):
        """載入設定"""
        logging.info("開始載入設定")
        
        try:
            local_ffmpeg = self.get_local_ffmpeg()
            if local_ffmpeg:
                logging.info(f"找到本地 FFmpeg：{local_ffmpeg}")
                self.config["ffmpeg_path"] = local_ffmpeg
            
            config_path = os.path.join(get_application_path(), "config.yaml")
            if not os.path.exists(config_path):
                return
                
            logging.info(f"載入設定檔：{config_path}")
            with open(config_path, "r") as f:
                saved_config = yaml.safe_load(f)
                if not isinstance(saved_config, dict):
                    raise ConfigError("設定檔格式錯誤")
                logging.info(f"載入的設定：{saved_config}")
                self.config.update(saved_config)
        except yaml.YAMLError as e:
            raise ConfigError("設定檔解析失敗", details=str(e))
        except Exception as e:
            raise ConfigError("載入設定失敗", details=str(e))
    
    def save_config(self, ffmpeg_path, texture_packer_path, tinypng_api_key=""):
        """儲存設定"""
        try:
            logging.info("開始儲存設定")
            logging.info(f"FFmpeg 路徑：{ffmpeg_path}")
            logging.info(f"TexturePacker 路徑：{texture_packer_path}")
            logging.info(f"TinyPNG API 金鑰：{'已設定' if tinypng_api_key else '未設定'}")
            
            # 驗證路徑（只驗證非空的路徑）
            if ffmpeg_path and not os.path.exists(ffmpeg_path):
                logging.error(f"FFmpeg 路徑無效：{ffmpeg_path}")
                raise ConfigError("FFmpeg 路徑無效")
            
            if texture_packer_path and not os.path.exists(texture_packer_path):
                logging.error(f"TexturePacker 路徑無效：{texture_packer_path}")
                raise ConfigError("TexturePacker 路徑無效")
            
            # 更新設定
            self.config.update({
                "ffmpeg_path": ffmpeg_path,
                "texture_packer_path": texture_packer_path,
                "tinypng_api_key": tinypng_api_key
            })
            
            # 如果有設定 TinyPNG API 金鑰，則設定到 tinify 模組中
            if tinypng_api_key:
                from .video import set_tinify_api_key
                set_tinify_api_key(tinypng_api_key)
            
            # 保存到檔案
            config_path = os.path.join(get_application_path(), "config.yaml")
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True)
            
            logging.info("設定儲存成功")
            return "✅ 設定已儲存"
            
        except ConfigError:
            raise
        except Exception as e:
            logging.error(f"儲存設定失敗：{str(e)}", exc_info=True)
            raise ConfigError("儲存設定失敗", details=str(e))
    
    def get_local_ffmpeg(self):
        """檢查本地 FFmpeg"""
        app_dir = get_application_path()
        ffmpeg_path = os.path.join(app_dir, "ffmpeg.exe")
        
        if os.path.exists(ffmpeg_path):
            try:
                subprocess.run([ffmpeg_path, "-version"], 
                             capture_output=True, 
                             check=True)
                return ffmpeg_path.replace("\\", "/")
            except:
                pass
        return ""
    
    def load_preferences(self):
        """載入使用者偏好設定"""
        prefs_file = os.path.join(get_application_path(), "preferences.json")
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, "r", encoding="utf-8") as f:
                    self.preferences = json.load(f)
                    # 將布林值轉換為正確的格式
                    for key, value in self.preferences.items():
                        if isinstance(value, bool):
                            self.preferences[key] = value
                        elif isinstance(value, str) and value.lower() in ['true', 'false']:
                            self.preferences[key] = value.lower() == 'true'
            except:
                pass
    
    def save_preferences(self, prefs):
        """儲存使用者偏好設定"""
        self.preferences.update(prefs)
        prefs_file = os.path.join(get_application_path(), "preferences.json")
        try:
            with open(prefs_file, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"儲存使用者偏好設定失敗：{str(e)}")
    
    def get_ffmpeg_path(self):
        """獲取 FFmpeg 路徑"""
        return self._normalize_path(self.config.get("ffmpeg_path", ""))
    
    def get_texture_packer_path(self):
        """獲取 TexturePacker 路徑"""
        return self._normalize_path(self.config.get("texture_packer_path", ""))
    
    def get_preference(self, key, default=None):
        """獲取偏好設定"""
        return self.preferences.get(key, default)
    
    def _normalize_path(self, path):
        """標準化路徑格式"""
        if not path:
            return ""
        try:
            if os.path.exists(path):
                return os.path.abspath(path).replace("\\", "/")
            return path.strip().strip('"').strip("'").replace("\\", "/")
        except Exception as e:
            logging.error(f"路徑格式化失敗：{str(e)}")
            return ""
    
    def cleanup_old_files(self, days):
        """清理超過指定天數的檔案"""
        try:
            from datetime import datetime, timedelta
            from core.file_utils import get_videos_dir
            
            videos_dir = get_videos_dir()
            if not os.path.exists(videos_dir):
                return "❌ 輸出目錄不存在"
            
            # 計算截止時間
            cutoff = time.time() - (days * 24 * 60 * 60)
            removed_count = 0
            
            # 遍歷所有子目錄
            for subfolder in os.listdir(videos_dir):
                subfolder_path = os.path.join(videos_dir, subfolder)
                if not os.path.isdir(subfolder_path):
                    continue
                
                # 檢查每個檔案
                for file in os.listdir(subfolder_path):
                    file_path = os.path.join(subfolder_path, file)
                    if os.path.getmtime(file_path) < cutoff:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                        except Exception as e:
                            logging.error(f"刪除檔案失敗 {file_path}: {str(e)}")
                
                # 如果目錄為空，也刪除目錄
                if not os.listdir(subfolder_path):
                    try:
                        os.rmdir(subfolder_path)
                    except Exception as e:
                        logging.error(f"刪除目錄失敗 {subfolder_path}: {str(e)}")
            
            if removed_count > 0:
                return f"✅ 已清理 {removed_count} 個檔案"
            else:
                return "✅ 沒有需要清理的檔案"
            
        except Exception as e:
            logging.error(f"清理檔案失敗：{str(e)}")
            return f"❌ 清理失敗：{str(e)}"
    
    def open_output_folder(self):
        """開啟輸出資料夾"""
        try:
            from core.file_utils import get_videos_dir
            import subprocess
            import platform
            
            videos_dir = get_videos_dir()
            if not os.path.exists(videos_dir):
                return "❌ 輸出目錄不存在"
            
            # 根據作業系統選擇開啟方式
            if platform.system() == "Windows":
                os.startfile(videos_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", videos_dir])
            else:  # Linux
                subprocess.run(["xdg-open", videos_dir])
            
            return "✅ 已開啟輸出資料夾"
            
        except Exception as e:
            logging.error(f"開啟資料夾失敗：{str(e)}")
            return f"❌ 開啟失敗：{str(e)}"
    
    def _init_tinypng_api(self):
        """初始化 TinyPNG API 金鑰"""
        from .video import set_tinify_api_key
        api_key = self.get_tinypng_api_key()
        if api_key:
            set_tinify_api_key(api_key)
    
    def get_tinypng_api_key(self):
        """獲取 TinyPNG API 金鑰"""
        return self.config.get("tinypng_api_key", "") 