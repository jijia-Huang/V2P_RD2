"""
影片處理相關功能
"""
import os
import glob
import json
import time
import shutil
import logging
import subprocess
import gradio as gr
import tinify
from datetime import datetime
from version import get_version
from .exceptions import ConversionError, FileError, ConfigError
from .file_utils import (get_application_path, get_output_dir, ensure_output_dir)

# TinyPNG API 金鑰設定，實際使用時需要替換成自己的 API Key
TINIFY_API_KEY = None  # 預設為 None，需要在設定中配置


def set_tinify_api_key(api_key):
    """設定 TinyPNG API 金鑰"""
    global TINIFY_API_KEY
    TINIFY_API_KEY = api_key
    if api_key:
        tinify.key = api_key
        logging.info("已設定 TinyPNG API 金鑰")
    else:
        logging.warning("未設定 TinyPNG API 金鑰，將無法使用 TinyPNG 壓縮功能")


def compress_png_with_tinypng(image_path, api_key=None):
    """使用 TinyPNG API 壓縮圖片檔案"""
    if not os.path.exists(image_path):
        logging.error(f"找不到圖片檔案：{image_path}")
        return False

    try:
        # 使用傳入的 API 金鑰或全局金鑰
        key_to_use = api_key or TINIFY_API_KEY
        if not key_to_use:
            logging.warning(f"未設定 TinyPNG API 金鑰，跳過壓縮 {image_path}")
            return False

        # 設定 TinyPNG API 金鑰
        tinify.key = key_to_use

        # 記錄原始檔案大小
        original_size = os.path.getsize(image_path)

        # 壓縮並覆蓋原檔案
        source = tinify.from_file(image_path)
        source.to_file(image_path)

        # 記錄壓縮後檔案大小和節省的空間
        compressed_size = os.path.getsize(image_path)
        saved_size = original_size - compressed_size
        saved_percent = (saved_size / original_size) * 100 if original_size > 0 else 0

        logging.info(f"已壓縮 {image_path}，原始大小：{original_size/1024:.2f} KB，"
                     f"壓縮後：{compressed_size/1024:.2f} KB，"
                     f"節省：{saved_percent:.2f}%")

        return True
    except tinify.AccountError:
        logging.error("TinyPNG API 金鑰認證失敗，請檢查您的 API 金鑰")
        return False
    except tinify.ClientError:
        logging.error("TinyPNG API 請求錯誤")
        return False
    except tinify.ServerError:
        logging.error("TinyPNG 伺服器錯誤，請稍後再試")
        return False
    except tinify.ConnectionError:
        logging.error("連接 TinyPNG 服務器失敗，請檢查網路連接")
        return False
    except Exception as e:
        logging.error(f"TinyPNG 壓縮過程中發生錯誤：{str(e)}")
        return False


def compress_all_images_in_folder(folder_path, name_pattern, output_format, api_key=None):
    """壓縮資料夾中所有符合模式的圖片檔案"""
    if not os.path.exists(folder_path):
        logging.error(f"找不到資料夾：{folder_path}")
        return 0

    # 根據輸出格式決定要壓縮的檔案類型
    file_extension = output_format.lower()
    if file_extension not in ["png", "jpg"]:
        logging.error(f"不支援的輸出格式：{output_format}")
        return 0

    # 找出所有符合模式的圖片檔案
    image_files = glob.glob(os.path.join(folder_path, f"{name_pattern}*.{file_extension}"))
    if not image_files:
        logging.warning(f"在 {folder_path} 中找不到符合 {name_pattern}*.{file_extension} 的檔案")
        return 0

    # 記錄開始壓縮
    logging.info(f"開始壓縮 {len(image_files)} 個 {output_format} 檔案...")

    # 計算壓縮成功的檔案數
    success_count = 0
    for image_file in image_files:
        if compress_png_with_tinypng(image_file, api_key):
            success_count += 1

    # 記錄壓縮結果
    logging.info(f"{output_format} 壓縮完成，成功：{success_count}/{len(image_files)}")
    return success_count


# TinyPNG API 金鑰設定，實際使用時需要替換成自己的 API Key
TINIFY_API_KEY = None  # 預設為 None，需要在設定中配置

def set_tinify_api_key(api_key):
    """設定 TinyPNG API 金鑰"""
    global TINIFY_API_KEY
    TINIFY_API_KEY = api_key
    if api_key:
        tinify.key = api_key
        logging.info("已設定 TinyPNG API 金鑰")
    else:
        logging.warning("未設定 TinyPNG API 金鑰，將無法使用 TinyPNG 壓縮功能")

def compress_png_with_tinypng(png_path, api_key=None):
    """使用 TinyPNG API 壓縮 PNG 檔案"""
    if not os.path.exists(png_path):
        logging.error(f"找不到 PNG 檔案：{png_path}")
        return False
    
    try:
        # 使用傳入的 API 金鑰或全局金鑰
        key_to_use = api_key or TINIFY_API_KEY
        if not key_to_use:
            logging.warning(f"未設定 TinyPNG API 金鑰，跳過壓縮 {png_path}")
            return False
        
        # 設定 TinyPNG API 金鑰
        tinify.key = key_to_use
        
        # 記錄原始檔案大小
        original_size = os.path.getsize(png_path)
        
        # 壓縮並覆蓋原檔案
        source = tinify.from_file(png_path)
        source.to_file(png_path)
        
        # 記錄壓縮後檔案大小和節省的空間
        compressed_size = os.path.getsize(png_path)
        saved_size = original_size - compressed_size
        saved_percent = (saved_size / original_size) * 100 if original_size > 0 else 0
        
        logging.info(f"已壓縮 {png_path}，原始大小：{original_size/1024:.2f} KB，"
                    f"壓縮後：{compressed_size/1024:.2f} KB，"
                    f"節省：{saved_percent:.2f}%")
        
        return True
    except tinify.AccountError:
        logging.error("TinyPNG API 金鑰認證失敗，請檢查您的 API 金鑰")
        return False
    except tinify.ClientError:
        logging.error("TinyPNG API 請求錯誤")
        return False
    except tinify.ServerError:
        logging.error("TinyPNG 伺服器錯誤，請稍後再試")
        return False
    except tinify.ConnectionError:
        logging.error("連接 TinyPNG 服務器失敗，請檢查網路連接")
        return False
    except Exception as e:
        logging.error(f"TinyPNG 壓縮過程中發生錯誤：{str(e)}")
        return False

def compress_all_pngs_in_folder(folder_path, name_pattern, api_key=None):
    """壓縮資料夾中所有符合模式的 PNG 檔案"""
    if not os.path.exists(folder_path):
        logging.error(f"找不到資料夾：{folder_path}")
        return 0
    
    # 找出所有符合模式的 PNG 檔案
    png_files = glob.glob(os.path.join(folder_path, f"{name_pattern}*.png"))
    if not png_files:
        logging.warning(f"在 {folder_path} 中找不到符合 {name_pattern}*.png 的檔案")
        return 0
    
    # 記錄開始壓縮
    logging.info(f"開始壓縮 {len(png_files)} 個 PNG 檔案...")
    
    # 計算壓縮成功的檔案數
    success_count = 0
    for png_file in png_files:
        if compress_png_with_tinypng(png_file, api_key):
            success_count += 1
    
    # 記錄壓縮結果
    logging.info(f"PNG 壓縮完成，成功：{success_count}/{len(png_files)}")
    return success_count

def get_video_dimensions(video_path, ffmpeg_path):
    """獲取影片原始尺寸
    
    Args:
        video_path: 影片檔案路徑
        ffmpeg_path: FFmpeg 執行檔路徑
    
    Returns:
        tuple: (width, height) 或 (None, None)
    """
    if not ffmpeg_path or not os.path.exists(video_path):
        logging.warning(f"獲取影片尺寸失敗：ffmpeg_path={ffmpeg_path}, video exists={os.path.exists(video_path) if video_path else False}")
        return None, None
    
    try:
        import re
        
        # 嘗試使用 ffprobe（如果存在）
        ffprobe_path = ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe") if "ffmpeg.exe" in ffmpeg_path else ffmpeg_path.replace("ffmpeg", "ffprobe")
        
        if os.path.exists(ffprobe_path) and "ffprobe" in ffprobe_path:
            logging.debug(f"使用 ffprobe 讀取影片尺寸：{ffprobe_path}")
            cmd = [
                ffprobe_path,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
            if result.returncode == 0 and result.stdout:
                dimensions = result.stdout.strip().split('x')
                if len(dimensions) == 2:
                    width, height = int(dimensions[0]), int(dimensions[1])
                    logging.info(f"成功讀取影片尺寸（ffprobe）：{width}x{height}")
                    return width, height
        
        # 使用 ffmpeg -i 輸出解析
        logging.debug(f"使用 ffmpeg -i 讀取影片尺寸")
        result = subprocess.run([ffmpeg_path, "-i", video_path], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
        
        # 搜尋影片流資訊
        for line in result.stderr.split('\n'):
            if 'Stream' in line and 'Video:' in line:
                # 尋找類似 "1920x1080" 或 "1080x1920" 的模式
                match = re.search(r'(\d{2,5})x(\d{2,5})', line)
                if match:
                    width, height = int(match.group(1)), int(match.group(2))
                    logging.info(f"成功讀取影片尺寸（ffmpeg -i）：{width}x{height}")
                    return width, height
        
        logging.warning("無法從 ffmpeg 輸出中解析影片尺寸")
        return None, None
        
    except subprocess.TimeoutExpired:
        logging.error("讀取影片尺寸超時")
        return None, None
    except Exception as e:
        logging.error(f"獲取影片尺寸失敗：{str(e)}", exc_info=True)
        return None, None


def get_video_info(video_path, ffmpeg_path):
    """使用 FFmpeg 獲取影片資訊"""
    if not ffmpeg_path:
        raise ConfigError("未設定 FFmpeg 路徑")

    if not os.path.exists(video_path):
        raise FileError("找不到影片檔案", details=f"路徑：{video_path}")

    try:
        # 直接使用 -i 參數獲取資訊
        result = subprocess.run([ffmpeg_path, "-i", video_path], capture_output=True, text=True, encoding='utf-8', errors='ignore')

        # FFmpeg 的影片資訊輸出在 stderr
        info = result.stderr

        if not info:
            raise ConversionError("無法讀取影片資訊", details="FFmpeg 沒有返回任何資訊")

        # 提取重要資訊
        lines = []
        for line in info.split('\n'):
            if any(key in line.lower() for key in ['duration', 'video:', 'stream']):
                lines.append(line.strip())

        if not lines:
            raise ConversionError("無法解析影片資訊", details="找不到影片相關資訊")

        return "\n".join(lines)

    except (ConfigError, FileError, ConversionError):
        raise
    except subprocess.CalledProcessError as e:
        raise ConversionError("FFmpeg 執行失敗", details=e.stderr if e.stderr else str(e))
    except Exception as e:
        raise ConversionError("讀取影片資訊失敗", details=str(e))


def save_metadata(output_folder, output_name, settings):
    """保存動畫相關的設定資訊"""
    try:
        if not os.path.exists(output_folder):
            raise FileError("輸出目錄不存在", details=f"路徑：{output_folder}")

        metadata = {
            "name": output_name,
            "fps": settings.get("fps", 0),
            "max_width": settings.get("max_width", 0),
            "max_height": settings.get("max_height", 0),
            "creation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "frame_count": settings.get("frame_count", 0),
            "plist_count": settings.get("plist_count", 0),
            "tool_version": get_version(),
            "output_format": settings.get("output_format", "PNG"),
            "quality": settings.get("quality", 5),
            # Frame 縮放相關資訊
            "original_size": settings.get("original_size", ""),
            "frame_resize_enabled": settings.get("frame_resize_enabled", False),
            "frame_size": settings.get("frame_size", ""),
            "resize_mode": settings.get("resize_mode", "")
        }

        metadata_path = os.path.join(output_folder, f"{output_name}_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except FileError:
        raise
    except Exception as e:
        raise FileError("保存 metadata 失敗", details=str(e))


def process_video(mp4_file,
                  fps,
                  output_name,
                  max_width,
                  max_height,
                  ffmpeg_path,
                  texture_packer_path,
                  output_format="PNG",
                  quality=5,
                  use_tinypng=False,
                  tinypng_api_key=None,
                  packer_choice="自動選擇",
                  enable_resize=False,
                  target_width=None,
                  target_height=None,
                  resize_mode="stretch",
                  enable_bg_removal=False,
                  bg_removal_tolerance=10,
                  config_manager=None,
                  ui_manager=None,
                  progress=gr.Progress()):
    """處理影片轉換
    
    Args:
        mp4_file: MP4 檔案物件
        fps: 影格率
        output_name: 輸出名稱
        max_width: 材質最大寬度
        max_height: 材質最大高度
        ffmpeg_path: FFmpeg 執行檔路徑
        texture_packer_path: TexturePacker 執行檔路徑
        output_format: 輸出格式 (PNG/JPG)
        quality: 輸出品質 (1-31)
        use_tinypng: 是否使用 TinyPNG 壓縮
        tinypng_api_key: TinyPNG API 金鑰
        enable_resize: 是否啟用 Frame 縮放
        target_width: Frame 目標寬度
        target_height: Frame 目標高度
        resize_mode: 縮放模式
        enable_bg_removal: 是否啟用去背處理
        bg_removal_tolerance: 去背容差值
        ui_manager: UI 管理器
        progress: Gradio Progress 物件
    
    Returns:
        str: 處理結果訊息
    """
    temp_folder = None
    try:
        # 檢查和驗證
        if not mp4_file:
            raise FileError("請選擇 MP4 檔案")

        if not output_name:
            raise ConfigError("請輸入輸出名稱")
        
        # 驗證縮放參數
        if enable_resize:
            if not target_width or not target_height:
                raise ConfigError("啟用縮放時必須提供目標寬度和高度")
            if target_width < 1 or target_height < 1:
                raise ConfigError("目標尺寸必須大於 0")
            if target_width > 8192 or target_height > 8192:
                logging.warning(f"目標尺寸 {target_width}x{target_height} 較大，處理時間可能較長")

        # 獲取原始影片尺寸
        original_width, original_height = get_video_dimensions(mp4_file.name, ffmpeg_path)
        if original_width and original_height:
            logging.info(f"原始影片尺寸：{original_width}x{original_height}")

        # 確保輸出目錄存在
        output_dir = ensure_output_dir(output_name)

        # 詳細記錄處理參數
        logging.info(f"開始處理影片：{mp4_file.name}")
        logging.info(f"參數設定：FPS={fps}, 輸出名稱={output_name}")
        logging.info(f"材質限制：{max_width}x{max_height}")
        logging.info(f"輸出格式：{output_format}")
        logging.info(f"輸出品質：{quality}")
        logging.info(f"使用 TinyPNG 壓縮：{'是' if use_tinypng else '否'}")
        if enable_resize:
            logging.info(f"Frame 縮放：啟用 - {target_width}x{target_height} ({resize_mode})")
        else:
            logging.info("Frame 縮放：未啟用")
        logging.info(f"使用工具：FFmpeg={ffmpeg_path}, TexturePacker={texture_packer_path}")

        # 記錄臨時目錄
        temp_folder = os.path.join(get_application_path(), "temp", output_name)
        logging.info(f"建立臨時目錄：{temp_folder}")

        # 記錄影格提取
        frames_dir = os.path.join(temp_folder, "frames")
        
        logging.info(f"開始提取影格到：{frames_dir}")
        frame_count = extract_frames(
            mp4_file.name, frames_dir, fps, ffmpeg_path, output_name, output_format, quality,
            enable_resize=enable_resize,
            target_width=target_width,
            target_height=target_height,
            resize_mode=resize_mode
        )
        logging.info(f"成功提取 {frame_count} 個影格")

        # 保存影格目錄資訊供去背預覽使用（更新為當前的工作影格）
        config_manager.save_preferences({
            "preview_frames_dir": frames_dir,
            "preview_frame_count": frame_count,
            "preview_fps": fps,
            "preview_video_path": mp4_file.name,
            "preview_temp_folder": temp_folder  # 保存臨時目錄路徑，供後續清理
        })
        
        logging.info(f"已更新影格目錄資訊：{frames_dir}")

        # 去背處理
        if enable_bg_removal and output_format.upper() == "PNG":
            logging.info(f"開始批次去背處理（容差：{bg_removal_tolerance}）...")
            from .filter import process_frames_batch
            
            progress(0.3, desc="正在去背處理...")
            
            # 檢查去背前的影格
            frame_files_before = glob.glob(os.path.join(frames_dir, "*.png"))
            logging.info(f"去背前影格數量：{len(frame_files_before)}")
            
            try:
                result = process_frames_batch(
                    frames_dir,
                    bg_color=None,
                    tolerance=bg_removal_tolerance,
                    output_dir=frames_dir,  # 覆蓋原影格
                    auto_detect=True,
                    progress_callback=None
                )
                
                # 檢查去背後的影格
                frame_files_after = glob.glob(os.path.join(frames_dir, "*.png"))
                logging.info(f"去背後影格數量：{len(frame_files_after)}")
                
                if result['failed'] > 0:
                    logging.warning(f"部分影格去背失敗：{result['failed']}/{result['total']}")
                
                logging.info(f"去背完成：成功 {result['success']}/{result['total']} 幀")
            except Exception as e:
                logging.error(f"去背處理失敗：{str(e)}", exc_info=True)
                # 去背失敗不應該阻止整個流程，繼續處理
                logging.warning("去背處理失敗，將使用原始影格繼續處理")
        else:
            if enable_bg_removal and output_format.upper() != "PNG":
                logging.warning(f"輸出格式為 {output_format}，跳過去背處理（僅支援 PNG）")

        # 根據使用者選擇決定使用哪個打包器
        logging.info(f"打包器選擇: {packer_choice}")
        
        if packer_choice == "TexturePacker":
            # 強制使用 TexturePacker
            if not texture_packer_path or not os.path.exists(texture_packer_path):
                raise ConfigError("TexturePacker 未設定或不存在，請在設定頁面配置 TexturePacker 路徑")
            logging.info("使用 TexturePacker 進行打包")
            plist_count = _process_with_texturepacker(
                texture_packer_path, frames_dir, output_dir, output_name, 
                max_width, max_height, output_format, progress
            )
        elif packer_choice == "Python 打包器":
            # 強制使用 Python 打包器
            logging.info("使用 Python 打包器進行打包")
            plist_count = _process_with_python_packer(
                frames_dir, output_dir, output_name, 
                max_width, max_height, output_format, progress
            )
        else:
            # 自動選擇（預設行為）
            if texture_packer_path and os.path.exists(texture_packer_path):
                logging.info("自動選擇：使用 TexturePacker 進行打包")
                plist_count = _process_with_texturepacker(
                    texture_packer_path, frames_dir, output_dir, output_name, 
                    max_width, max_height, output_format, progress
                )
            else:
                logging.info("自動選擇：TexturePacker 未設定，使用 Python 打包器進行打包")
                plist_count = _process_with_python_packer(
                    frames_dir, output_dir, output_name, 
                    max_width, max_height, output_format, progress
                )

        # 保存設定資訊
        settings = {
            "fps": fps,
            "max_width": max_width,
            "max_height": max_height,
            "frame_count": frame_count,
            "plist_count": plist_count,
            "output_format": output_format,
            "quality": quality,
            "use_tinypng": use_tinypng,
            # 縮放相關資訊
            "original_size": f"{original_width}x{original_height}" if original_width and original_height else "",
            "frame_resize_enabled": enable_resize,
            "frame_size": f"{target_width}x{target_height}" if enable_resize and target_width and target_height else (f"{original_width}x{original_height}" if original_width and original_height else ""),
            "resize_mode": resize_mode if enable_resize else "",
            # 去背相關資訊
            "bg_removal_enabled": enable_bg_removal,
            "bg_removal_tolerance": bg_removal_tolerance if enable_bg_removal else None
        }

        # 如果啟用了 TinyPNG 壓縮，則進行壓縮
        if use_tinypng:
            logging.info(f"開始使用 TinyPNG 壓縮 {output_format} 檔案...")
            compress_count = compress_all_images_in_folder(output_dir, output_name, output_format, tinypng_api_key)
            logging.info(f"TinyPNG 壓縮完成，共壓縮 {compress_count} 個檔案")

            # 將壓縮信息也添加到設定中
            settings["compressed_count"] = compress_count

        logging.info(f"TexturePacker 完成，生成 {plist_count} 個 plist 檔案")

        # 記錄 metadata 保存
        logging.info(f"保存 metadata 到：{output_dir}")
        save_metadata(output_dir, output_name, settings)

        logging.info("✅ 處理完成")
        return "✅ 處理完成！"

    except (FileError, ConfigError, ConversionError) as e:
        logging.error(f"{e.error_type.value} - {e.message}")
        if e.details:
            logging.debug(f"詳細錯誤：{e.details}")
        return f"❌ {e.error_type.value}：{e.message}"

    except Exception as e:
        logging.error(f"未預期的錯誤：{str(e)}", exc_info=True)
        return f"❌ 處理失敗：{str(e)}"

    finally:
        # 轉換完成後清理臨時目錄（預覽影格在獨立目錄，不受影響）
        if temp_folder and os.path.exists(temp_folder):
            try:
                import shutil
                # shutil.rmtree(temp_folder, ignore_errors=True)
                logging.info(f"已清理轉換臨時目錄：{temp_folder}")
            except Exception as e:
                logging.error(f"清理暫存檔案失敗：{str(e)}")


def extract_frames(video_path, output_folder, fps, ffmpeg_path, output_name, output_format="PNG", quality=5,
                  enable_resize=False, target_width=None, target_height=None, resize_mode="stretch"):
    """從影片中提取影格
    
    Args:
        video_path: 影片檔案路徑
        output_folder: 輸出資料夾
        fps: 影格率
        ffmpeg_path: FFmpeg 執行檔路徑
        output_name: 輸出名稱
        output_format: 輸出格式 (PNG/JPG)
        quality: 輸出品質 (1-31)
        enable_resize: 是否啟用縮放
        target_width: 目標寬度
        target_height: 目標高度
        resize_mode: 縮放模式 (stretch/crop/pad_black/pad_transparent)
    
    Returns:
        int: 提取的影格數量
    """
    if not os.path.exists(video_path):
        raise FileError("找不到影片檔案", details=f"路徑：{video_path}")

    if not ffmpeg_path:
        raise ConfigError("未設定 FFmpeg 路徑")

    try:
        # 先讀取影片原始尺寸並記錄
        original_width, original_height = get_video_dimensions(video_path, ffmpeg_path)
        if original_width and original_height:
            logging.info(f"📹 影片原始尺寸：{original_width}x{original_height}")
        else:
            logging.warning("⚠️ 無法讀取影片原始尺寸，將使用原始尺寸處理")
        
        # 確保輸出目錄存在
        os.makedirs(output_folder, exist_ok=True)

        # 根據格式設定輸出參數
        output_ext = output_format.lower()

        # 設定輸出檔案路徑
        output_path = os.path.join(output_folder, f"{output_name}_%d.{output_ext}")

        # 建立濾鏡列表
        filters = [f"fps={fps}"]
        
        # 如果啟用縮放
        if enable_resize and target_width and target_height:
            logging.info(f"🎯 目標尺寸：{target_width}x{target_height}")
            logging.info(f"🔧 縮放模式：{resize_mode}")
            if original_width and original_height:
                logging.info(f"📊 縮放比例：{original_width}x{original_height} → {target_width}x{target_height}")
            
            if resize_mode == "stretch":
                # 拉伸變形 - 直接縮放到目標尺寸
                filters.append(f"scale={target_width}:{target_height}")
                
            elif resize_mode == "crop":
                # 裁切中心 - 保持比例，放大後裁切
                filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase")
                filters.append(f"crop={target_width}:{target_height}")
                
            elif resize_mode in ["pad_black", "pad_transparent"]:
                # 填充模式 - 手動計算精確的縮放尺寸
                
                # 檢查是否需要降級透明邊
                use_transparent = (resize_mode == "pad_transparent" and output_format.upper() != "JPG")
                if resize_mode == "pad_transparent" and output_format.upper() == "JPG":
                    logging.warning("JPG 格式不支援透明邊，自動降級為黑邊模式")
                
                # 手動計算縮放後的尺寸，確保不超過目標
                if original_width and original_height:
                    # 計算兩個方向的縮放比例
                    scale_w = target_width / original_width
                    scale_h = target_height / original_height
                    # 使用較小的比例，確保不超過任何一邊
                    scale_ratio = min(scale_w, scale_h)
                    # 計算縮放後的尺寸（必須是偶數）
                    scaled_width = int(original_width * scale_ratio)
                    scaled_height = int(original_height * scale_ratio)
                    # 確保是偶數（H.264 要求）
                    if scaled_width % 2 != 0:
                        scaled_width -= 1
                    if scaled_height % 2 != 0:
                        scaled_height -= 1
                    
                    logging.info(f"📐 計算縮放：比例={scale_ratio:.4f}, 縮放後={scaled_width}x{scaled_height}")
                    
                    # 品質警告
                    if scale_ratio < 0.5:
                        logging.warning(f"⚠️ 縮放比例較小({scale_ratio:.1%})，建議使用較大的目標尺寸或降低品質參數以獲得更好效果")
                    
                    # 使用高品質縮放演算法
                    # lanczos: 高品質但較慢
                    # bicubic: 平衡品質和速度
                    scale_filter = f"scale={scaled_width}:{scaled_height}:flags=lanczos"
                else:
                    # 如果無法獲取原始尺寸，使用 force_original_aspect_ratio
                    scale_filter = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease:flags=lanczos"
                
                filters.append(scale_filter)
                logging.info(f"Scale 濾鏡：{scale_filter}")
                
                # 添加 format 濾鏡以確保支持透明（PNG 需要）
                if use_transparent:
                    # 先轉換為支持透明的 pixel format
                    filters.append("format=rgba")
                    logging.info(f"Format 濾鏡：format=rgba")
                    
                    # 使用完全透明的顏色
                    # FFmpeg pad filter 的透明色：black@0 表示黑色且完全透明
                    pad_filter = f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black@0"
                    logging.info(f"✨ 使用透明邊填充")
                else:
                    # 使用黑色
                    pad_filter = f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black"
                    logging.info(f"⬛ 使用黑邊填充")
                
                filters.append(pad_filter)
                logging.info(f"Pad 濾鏡：{pad_filter}")
        else:
            logging.info("使用原始尺寸（未啟用縮放）")
        
        # 組合濾鏡
        filter_str = ",".join(filters)
        
        # 執行 FFmpeg 命令
        cmd = [ffmpeg_path, 
               "-i", video_path, 
               "-vf", filter_str,
               "-frame_pts", "1", 
               "-q:v", str(quality), 
               "-y", 
               output_path]

        # 記錄完整命令以便除錯
        logging.info(f"FFmpeg 完整命令：{' '.join(cmd)}")
        logging.info(f"濾鏡字串：{filter_str}")
        
        # 品質提示
        if quality > 10:
            logging.warning(f"⚠️ 輸出品質設定較低 (q:v={quality})，建議使用 1-5 獲得更好畫質")
        else:
            logging.info(f"✅ 輸出品質：{quality} (1=最好, 31=最差)")

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "未知錯誤"
            logging.error(f"FFmpeg 錯誤輸出：{error_msg}")
            raise ConversionError("影格提取失敗", details=error_msg)

        # 計算提取的影格數量
        frame_count = len(glob.glob(os.path.join(output_folder, f"{output_name}_*.{output_ext}")))
        if frame_count == 0:
            raise ConversionError("沒有提取到任何影格")

        return frame_count

    except (FileError, ConfigError, ConversionError):
        raise
    except Exception as e:
        raise ConversionError("影格提取過程發生錯誤", details=str(e))


def _process_with_texturepacker(texture_packer_path, frames_dir, output_dir, output_name, 
                               max_width, max_height, output_format, progress):
    """使用 TexturePacker 進行打包"""
    logging.info("開始執行 TexturePacker 打包")
    
    tp_cmd = [
        texture_packer_path, 
        "--data", os.path.join(output_dir, f"{output_name}_{{n}}.plist"), 
        "--format", "cocos2d", 
        "--texture-format", output_format.lower(), 
        "--png-opt-level", "2", 
        "--sheet", os.path.join(output_dir, f"{output_name}_{{n}}.{output_format.lower()}"), 
        "--max-width", str(max_width), 
        "--max-height", str(max_height), 
        "--size-constraints", "POT", 
        "--multipack", 
        "--algorithm", "MaxRects", 
        "--maxrects-heuristics", "Best", 
        "--trim-mode", "None",
        "--opt", "RGBA8888" if output_format == "PNG" else "RGB888", 
        "--extrude", "0", 
        "--disable-auto-alias", 
        "--shape-padding", "0", 
        "--border-padding","0", 
        "--disable-clean-transparency", 
        "--basic-sort-by", "Name", 
        frames_dir
    ]

    try:
        result = subprocess.run(tp_cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        logging.info(f"TexturePacker 執行成功：{result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"TexturePacker 命令：{' '.join(tp_cmd)}")
        logging.error(f"TexturePacker 錯誤輸出：{e.stderr}")
        logging.error(f"TexturePacker 標準輸出：{e.stdout}")
        logging.error(f"影格目錄內容：{os.listdir(frames_dir) if os.path.exists(frames_dir) else '目錄不存在'}")
        raise ConversionError("TexturePacker 執行失敗", details=f"stderr: {e.stderr}\nstdout: {e.stdout}\ncmd: {' '.join(tp_cmd)}")

    # 計算 plist 數量
    plist_count = len(glob.glob(os.path.join(output_dir, f"{output_name}*.plist")))
    if plist_count == 0:
        raise ConversionError("沒有生成任何 plist 檔案")
    
    logging.info(f"TexturePacker 完成，生成 {plist_count} 個 plist 檔案")
    return plist_count


def _process_with_python_packer(frames_dir, output_dir, output_name, 
                               max_width, max_height, output_format, progress):
    """使用 Python 打包器進行打包"""
    try:
        from .python_packer import PythonTexturePacker
        
        logging.info("開始執行 Python 打包器")
        progress(0.6, desc="正在使用 Python 打包器打包...")
        
        # 獲取所有影格檔案
        frame_pattern = os.path.join(frames_dir, f"*.{output_format.lower()}")
        image_paths = sorted(glob.glob(frame_pattern))
        
        if not image_paths:
            # 嘗試其他格式
            for ext in ['png', 'jpg', 'jpeg']:
                if ext != output_format.lower():
                    frame_pattern = os.path.join(frames_dir, f"*.{ext}")
                    image_paths = sorted(glob.glob(frame_pattern))
                    if image_paths:
                        logging.info(f"找到 {len(image_paths)} 個 {ext.upper()} 影格檔案")
                        break
        
        if not image_paths:
            raise ConversionError(f"在 {frames_dir} 中找不到任何影格檔案")
        
        logging.info(f"找到 {len(image_paths)} 個影格檔案")
        
        # 創建 Python 打包器
        packer = PythonTexturePacker(max_width, max_height, output_format)
        
        # 執行打包
        result = packer.pack_images(image_paths, output_dir, output_name)
        
        if not result["success"]:
            raise ConversionError("Python 打包器執行失敗")
        
        plist_count = result["sheets_count"]
        logging.info(f"Python 打包器完成，生成 {plist_count} 個材質集，耗時 {result['elapsed_time']:.2f}s")
        
        return plist_count
        
    except ImportError as e:
        logging.error(f"無法導入 Python 打包器模組：{str(e)}")
        raise ConversionError("Python 打包器模組導入失敗", details=str(e))
    except Exception as e:
        logging.error(f"Python 打包器執行失敗：{str(e)}", exc_info=True)
        raise ConversionError("Python 打包器執行失敗", details=str(e))
