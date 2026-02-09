"""
影格濾鏡處理模組 - 洪水填充去背
"""
import os
import glob
import logging
import subprocess
import shutil
import cv2
import numpy as np
from PIL import Image
from .exceptions import ConversionError, FileError


def hex_to_bgr(hex_color):
    """
    將十六進制顏色轉換為 BGR 格式
    
    Args:
        hex_color: 十六進制顏色字串 (例如: "#00FF00")
    
    Returns:
        tuple: (B, G, R) 顏色值
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (b, g, r)  # OpenCV 使用 BGR 格式


def flood_fill_remove_background(image_path, bg_color=None, tolerance=10, output_path=None, auto_detect=True):
    """
    使用洪水填充算法去除背景
    
    Args:
        image_path: 輸入影格路徑
        bg_color: 背景顏色（十六進制），僅在 auto_detect=False 時使用
        tolerance: 容差值（0-255），數值越大容許的顏色差異越大
        output_path: 輸出路徑，如果為 None 則覆蓋原檔案
        auto_detect: 是否自動檢測角落顏色（True=自動，False=使用指定顏色）
    
    Returns:
        str: 輸出檔案路徑
    
    Raises:
        FileError: 檔案不存在或無法讀取
        ConversionError: 處理過程發生錯誤
    """
    if not os.path.exists(image_path):
        raise FileError("找不到影格檔案", details=f"路徑：{image_path}")
    
    try:
        logging.info(f"🔍 開始處理影格：{os.path.basename(image_path)}")
        
        # 讀取圖片（處理中文路徑問題）
        # OpenCV 的 imread 無法正確處理中文路徑，使用 numpy + imdecode
        img_array = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ConversionError("無法讀取影格檔案", details=f"路徑：{image_path}")
        
        height, width = img.shape[:2] if len(img.shape) >= 2 else (0, 0)
        channels = img.shape[2] if len(img.shape) > 2 else 1
        
        logging.info(f"📏 影格資訊：尺寸={width}x{height}, 通道數={channels}, dtype={img.dtype}")
        
        # 檢查圖片數據
        if channels >= 3:
            # 檢查像素值範圍
            logging.info(f"📊 像素值範圍：R[{img[:,:,0].min()}-{img[:,:,0].max()}], G[{img[:,:,1].min()}-{img[:,:,1].max()}], B[{img[:,:,2].min()}-{img[:,:,2].max()}]")
            if channels == 4:
                logging.info(f"📊 Alpha 通道範圍：[{img[:,:,3].min()}-{img[:,:,3].max()}]")
        
        # 準備用於 floodFill 的 BGR 圖像（floodFill 只支援 1 或 3 通道）
        if len(img.shape) == 2:  # 灰階圖
            img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            logging.info("🔄 圖片格式：灰階 → BGR")
        elif img.shape[2] == 3:  # 已經是 BGR
            img_bgr = img.copy()
            logging.info("✅ 圖片格式：BGR（無需轉換）")
        elif img.shape[2] == 4:  # BGRA，提取 BGR
            img_bgr = img[:, :, :3].copy()
            logging.info("🔄 圖片格式：BGRA → BGR（提取前3通道）")
        else:
            raise ConversionError("不支援的圖片格式", details=f"通道數：{img.shape[2]}")
        
        # 檢查原始圖片是否已經有透明區域
        if channels == 4:
            orig_alpha = img[:, :, 3]
            orig_transparent = np.sum(orig_alpha < 255)
            if orig_transparent > 0:
                logging.warning(f"⚠️ 警告：原始圖片已有 {orig_transparent} 個像素不是完全不透明（Alpha < 255），這可能影響去背效果")
        
        # 創建遮罩（需要比圖片大 2 像素）
        mask = np.zeros((height + 2, width + 2), np.uint8)
        logging.info(f"🎭 創建遮罩：{mask.shape}")
        
        # 從四個角落開始洪水填充
        corners = [
            (0, 0),                    # 左上
            (width - 1, 0),            # 右上
            (0, height - 1),           # 左下
            (width - 1, height - 1)    # 右下
        ]
        logging.info(f"🔍 準備從 {len(corners)} 個角落進行洪水填充")
        
        if auto_detect:
            # 自動模式：直接從四個角落填充，使用角落實際的顏色
            logging.info(f"使用自動檢測模式，容差：{tolerance}")
            
            for i, (x, y) in enumerate(corners):
                if x < 0 or x >= width or y < 0 or y >= height:
                    continue
                
                # 獲取角落實際顏色（從 BGR 圖像）
                corner_color = img_bgr[y, x]
                logging.debug(f"角落 {i+1} ({x}, {y})：顏色 BGR={corner_color}")
                
                # 執行洪水填充（在 BGR 圖像上，只更新遮罩）
                flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY
                
                _, _, _, rect = cv2.floodFill(
                    img_bgr, 
                    mask, 
                    (x, y), 
                    (0, 0, 0),  # 新顏色（BGR，但因為 MASK_ONLY 不會實際改變圖像）
                    loDiff=(tolerance, tolerance, tolerance),
                    upDiff=(tolerance, tolerance, tolerance),
                    flags=flags
                )
                
                logging.debug(f"角落 {i+1} 填充完成，矩形範圍：{rect}")
        else:
            # 手動模式：只填充與指定顏色相近的區域
            if not bg_color:
                raise ConversionError("手動模式需要指定背景顏色 (bg_color)")
            
            target_bgr = hex_to_bgr(bg_color)
            logging.info(f"使用手動指定顏色模式，目標顏色 BGR：{target_bgr}，容差：{tolerance}")
            
            for i, (x, y) in enumerate(corners):
                if x < 0 or x >= width or y < 0 or y >= height:
                    continue
                
                # 獲取當前像素顏色（從 BGR 圖像）
                current_color = img_bgr[y, x]
                
                # 計算與目標顏色的差異
                color_diff = np.abs(current_color.astype(int) - np.array(target_bgr).astype(int)).max()
                
                logging.debug(f"角落 {i+1} ({x}, {y})：顏色 {current_color}，與目標差異 {color_diff}")
                
                # 如果顏色接近目標背景色，進行填充
                if color_diff <= tolerance:
                    flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY
                    
                    _, _, _, rect = cv2.floodFill(
                        img_bgr, 
                        mask, 
                        (x, y), 
                        (0, 0, 0),
                        loDiff=(tolerance, tolerance, tolerance),
                        upDiff=(tolerance, tolerance, tolerance),
                        flags=flags
                    )
                    
                    logging.debug(f"角落 {i+1} 填充完成，矩形範圍：{rect}")
                else:
                    logging.debug(f"角落 {i+1} 顏色差異過大 ({color_diff} > {tolerance})，跳過")
        
        # 將遮罩應用到 Alpha 通道
        # mask 的值：0=未填充，1=填充後的值
        mask_crop = mask[1:-1, 1:-1]  # 移除邊界
        
        # 調試：檢查遮罩狀態
        mask_filled_pixels = np.sum(mask_crop > 0)
        mask_unique_values = np.unique(mask_crop)
        logging.info(f"🎭 遮罩統計：填充像素={mask_filled_pixels}/{mask_crop.size}, 唯一值={mask_unique_values}")
        
        if mask_filled_pixels == 0:
            logging.error(f"❌ 錯誤：遮罩沒有填充任何像素！洪水填充可能失敗了")
        
        # 創建帶有 Alpha 通道的輸出圖像
        # 無論原圖是否有 Alpha 通道，都使用處理後的 img_bgr 創建新的 RGBA 圖像
        img_rgba = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2BGRA)
        
        # 將填充區域設為透明（mask > 0 表示被填充的區域）
        img_rgba[:, :, 3] = np.where(mask_crop > 0, 0, 255)
        
        # 調試：檢查應用遮罩後的 Alpha 通道
        alpha_after_mask = img_rgba[:, :, 3]
        alpha_transparent_after = np.sum(alpha_after_mask == 0)
        logging.info(f"🎨 應用遮罩後 Alpha：透明像素={alpha_transparent_after}/{alpha_after_mask.size}")
        
        # 計算透明像素數量
        transparent_pixels = np.sum(img_rgba[:, :, 3] == 0)
        transparent_percentage = (transparent_pixels / (width * height)) * 100
        
        logging.info(f"去背完成：透明像素 {transparent_pixels}/{width * height} ({transparent_percentage:.1f}%)")
        
        # 調試：如果透明像素很少，說明演算法可能有問題
        if transparent_percentage < 1:
            logging.info(f"警告：透明像素比例很低（{transparent_percentage:.1f}%），去背效果可能不佳")
            # 輸出一些調試資訊
            logging.info(f"遮罩值統計：最小={np.min(mask_crop)}, 最大={np.max(mask_crop)}, 平均={np.mean(mask_crop):.2f}")
        
        # 保存結果
        if output_path is None:
            output_path = image_path
        
        # 確保輸出目錄存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 使用 PIL 保存以確保透明度正確
        # OpenCV 的 imwrite 在某些情況下處理透明度有問題
        img_rgb = cv2.cvtColor(img_rgba, cv2.COLOR_BGRA2RGBA)
        pil_img = Image.fromarray(img_rgb)
        
        # 調試：檢查圖片模式和透明度
        logging.info(f"💾 準備保存：PIL 模式={pil_img.mode}, 尺寸={pil_img.size}")
        if pil_img.mode == 'RGBA':
            # 檢查 Alpha 通道
            alpha_channel = pil_img.split()[3]
            alpha_array = np.array(alpha_channel)
            transparent_count = np.sum(alpha_array == 0)
            semi_transparent_count = np.sum((alpha_array > 0) & (alpha_array < 255))
            opaque_count = np.sum(alpha_array == 255)
            logging.info(f"📊 Alpha 統計：透明={transparent_count}, 半透明={semi_transparent_count}, 不透明={opaque_count}, 總計={alpha_array.size}")
            logging.info(f"📊 Alpha 百分比：透明={transparent_count/alpha_array.size*100:.2f}%, 不透明={opaque_count/alpha_array.size*100:.2f}%")
        
        # 保存為 PNG 格式
        pil_img.save(output_path, 'PNG', compress_level=6)
        
        # 驗證保存後的檔案
        if os.path.exists(output_path):
            saved_size = os.path.getsize(output_path)
            logging.info(f"✅ 已保存處理後的影格：{os.path.basename(output_path)}（透明度: {transparent_percentage:.1f}%, 檔案大小: {saved_size/1024:.2f} KB）")
            
            # 驗證讀取：確保透明度確實被保存
            verify_img = Image.open(output_path)
            if verify_img.mode == 'RGBA':
                verify_alpha = np.array(verify_img.split()[3])
                verify_transparent = np.sum(verify_alpha == 0)
                verify_percentage = (verify_transparent / verify_alpha.size) * 100
                logging.debug(f"保存驗證：重新讀取後透明像素 {verify_transparent}/{verify_alpha.size} ({verify_percentage:.1f}%)")
                
                if abs(verify_percentage - transparent_percentage) > 0.1:
                    logging.error(f"⚠️ 警告：保存前後透明度不一致！保存前 {transparent_percentage:.1f}%，保存後 {verify_percentage:.1f}%")
        else:
            logging.error(f"❌ 錯誤：檔案保存失敗，檔案不存在：{output_path}")
        
        return output_path
    
    except (FileError, ConversionError):
        raise
    except Exception as e:
        logging.error(f"去背處理失敗：{str(e)}", exc_info=True)
        raise ConversionError("去背處理失敗", details=str(e))


def process_frames_batch(frames_dir, bg_color=None, tolerance=10, output_dir=None, auto_detect=True, progress_callback=None):
    """
    批次處理資料夾中的所有影格
    
    Args:
        frames_dir: 影格資料夾路徑
        bg_color: 背景顏色（僅在 auto_detect=False 時使用）
        tolerance: 容差值
        output_dir: 輸出資料夾路徑，如果為 None 則覆蓋原檔案
        auto_detect: 是否自動檢測角落顏色
        progress_callback: 進度回調函數 (current, total, message)
    
    Returns:
        dict: 處理結果統計
            - success: 成功數量
            - failed: 失敗數量
            - total: 總數量
            - failed_files: 失敗的檔案列表
    
    Raises:
        FileError: 資料夾不存在
    """
    if not os.path.exists(frames_dir):
        raise FileError("找不到影格資料夾", details=f"路徑：{frames_dir}")
    
    # 尋找所有圖片檔案
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(frames_dir, ext)))
        image_files.extend(glob.glob(os.path.join(frames_dir, ext.upper())))
    
    if not image_files:
        raise FileError("資料夾中沒有找到任何圖片檔案", details=f"路徑：{frames_dir}")
    
    # 排序檔案
    image_files.sort()
    
    total = len(image_files)
    success = 0
    failed = 0
    failed_files = []
    
    mode_str = "自動檢測角落" if auto_detect else f"指定顏色 {bg_color}"
    logging.info(f"開始批次處理 {total} 個影格...")
    logging.info(f"參數：模式={mode_str}，容差={tolerance}")
    
    for i, image_file in enumerate(image_files, 1):
        try:
            # 計算輸出路徑
            if output_dir:
                filename = os.path.basename(image_file)
                # 強制輸出為 PNG 格式，並添加 filter_ 前綴
                filename = 'filter_' + os.path.splitext(filename)[0] + '.png'
                output_path = os.path.join(output_dir, filename)
            else:
                output_path = None
            
            # 處理影格
            flood_fill_remove_background(image_file, bg_color, tolerance, output_path, auto_detect)
            success += 1
            
            # 回調進度
            if progress_callback:
                progress_callback(i, total, f"處理完成：{os.path.basename(image_file)}")
            
            if i % 10 == 0:
                logging.info(f"進度：{i}/{total} ({i/total*100:.1f}%)")
        
        except Exception as e:
            failed += 1
            failed_files.append(image_file)
            logging.error(f"處理失敗 [{image_file}]：{str(e)}")
            
            if progress_callback:
                progress_callback(i, total, f"處理失敗：{os.path.basename(image_file)}")
    
    result = {
        "success": success,
        "failed": failed,
        "total": total,
        "failed_files": failed_files
    }
    
    logging.info(f"批次處理完成：成功 {success}/{total}，失敗 {failed}")
    
    return result


def preview_single_frame(frame_path, bg_color=None, tolerance=10, auto_detect=True):
    """
    處理單張影格並返回處理前後的圖片（用於預覽）
    
    Args:
        frame_path: 影格路徑
        bg_color: 背景顏色（僅在 auto_detect=False 時使用）
        tolerance: 容差值
        auto_detect: 是否自動檢測角落顏色
    
    Returns:
        tuple: (原始圖片 PIL.Image, 處理後圖片 PIL.Image)
    
    Raises:
        FileError: 檔案不存在
        ConversionError: 處理失敗
    """
    if not os.path.exists(frame_path):
        raise FileError("找不到影格檔案", details=f"路徑：{frame_path}")
    
    try:
        # 讀取原始圖片
        original_img = Image.open(frame_path)
        
        # 創建臨時輸出路徑
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_output = os.path.join(temp_dir, "preview_processed.png")
        
        # 處理圖片
        flood_fill_remove_background(frame_path, bg_color, tolerance, temp_output, auto_detect)
        
        # 讀取處理後的圖片
        processed_img = Image.open(temp_output)
        
        # 清理臨時檔案
        try:
            os.remove(temp_output)
        except:
            pass
        
        return original_img, processed_img
    
    except (FileError, ConversionError):
        raise
    except Exception as e:
        logging.error(f"預覽生成失敗：{str(e)}", exc_info=True)
        raise ConversionError("預覽生成失敗", details=str(e))


def create_video_from_frames(frames_dir, output_video_path, fps, ffmpeg_path, frame_pattern=None, preview_bg_color="#FF00FF"):
    """
    將影格序列重新組合成影片
    
    Args:
        frames_dir: 影格資料夾路徑
        output_video_path: 輸出影片路徑
        fps: 影格率
        ffmpeg_path: FFmpeg 執行檔路徑
        frame_pattern: 影格檔名模式（例如 "frame_%d.png"），None 表示自動檢測
        preview_bg_color: 預覽背景顏色（透明區域會顯示此顏色），預設洋紅色 #FF00FF
    
    Returns:
        str: 輸出影片路徑
    
    Raises:
        FileError: 資料夾不存在或沒有影格
        ConversionError: 轉換失敗
    """
    if not os.path.exists(frames_dir):
        raise FileError("找不到影格資料夾", details=f"路徑：{frames_dir}")
    
    # 尋找所有 PNG 檔案
    frame_files = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
    if not frame_files:
        raise FileError("資料夾中沒有找到任何 PNG 檔案", details=f"路徑：{frames_dir}")
    
    temp_preview_dir = None
    
    try:
        logging.info(f"開始生成影片：{len(frame_files)} 個影格 @ {fps} FPS")
        logging.info(f"影格目錄：{frames_dir}")
        logging.info(f"第一個影格：{os.path.basename(frame_files[0])}")
        logging.info(f"最後一個影格：{os.path.basename(frame_files[-1])}")
        logging.info(f"預覽背景顏色：{preview_bg_color}")
        
        # 確保輸出目錄存在
        output_dir = os.path.dirname(output_video_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 創建臨時目錄，用於存放添加背景色的影格
        import tempfile
        temp_preview_dir = tempfile.mkdtemp(prefix="v2p_preview_")
        logging.info(f"創建臨時預覽目錄：{temp_preview_dir}")
        
        # 將透明區域替換為指定背景色
        # 轉換背景顏色
        bg_rgb = tuple(int(preview_bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        logging.info(f"背景 RGB 顏色：{bg_rgb}")
        
        preview_frame_files = []
        for i, frame_file in enumerate(frame_files):
            # 讀取帶透明度的 PNG
            img_rgba = cv2.imread(frame_file, cv2.IMREAD_UNCHANGED)
            
            if img_rgba is None:
                logging.warning(f"無法讀取影格：{frame_file}，跳過")
                continue
            
            # 檢查是否有 Alpha 通道
            if len(img_rgba.shape) == 2 or img_rgba.shape[2] != 4:
                # 沒有 Alpha 通道，直接複製（處理中文路徑問題）
                preview_frame_path = os.path.join(temp_preview_dir, f"frame_{i:06d}.png")
                # 使用 imencode + tofile 處理中文路徑
                success, encoded_img = cv2.imencode('.png', img_rgba)
                if success:
                    encoded_img.tofile(preview_frame_path)
                preview_frame_files.append(preview_frame_path)
                continue
            
            # 創建背景色圖層
            bg_layer = np.zeros_like(img_rgba)
            bg_layer[:, :, 0] = bg_rgb[2]  # B
            bg_layer[:, :, 1] = bg_rgb[1]  # G
            bg_layer[:, :, 2] = bg_rgb[0]  # R
            bg_layer[:, :, 3] = 255        # Alpha
            
            # Alpha 混合：將透明區域替換成背景色
            alpha = img_rgba[:, :, 3:4] / 255.0
            result = (img_rgba[:, :, :3] * alpha + bg_layer[:, :, :3] * (1 - alpha)).astype(np.uint8)
            
            # 保存為 BGR（不需要 Alpha，處理中文路徑問題）
            preview_frame_path = os.path.join(temp_preview_dir, f"frame_{i:06d}.png")
            # 使用 imencode + tofile 處理中文路徑
            success, encoded_img = cv2.imencode('.png', result)
            if success:
                encoded_img.tofile(preview_frame_path)
            preview_frame_files.append(preview_frame_path)
        
        logging.info(f"已創建 {len(preview_frame_files)} 個帶背景色的預覽影格")
        
        # 使用帶背景色的影格生成影片
        frame_files = preview_frame_files
        frames_dir = temp_preview_dir
        
        # 創建臨時的檔案列表給 FFmpeg 使用
        # 這是最穩定的方式，不依賴檔名模式
        list_file = None
        
        try:
            list_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
            # 寫入所有影格的完整路徑
            for frame_file in frame_files:
                # FFmpeg concat demuxer 需要特定格式
                # Windows 路徑需要轉換為正斜線或使用絕對路徑
                frame_path = frame_file.replace('\\', '/')
                list_file.write(f"file '{frame_path}'\n")
                list_file.write(f"duration {1/fps}\n")
            # 最後一幀需要再寫一次（FFmpeg 的要求）
            last_frame_path = frame_files[-1].replace('\\', '/')
            list_file.write(f"file '{last_frame_path}'\n")
            list_file.close()
            
            logging.info(f"創建影格列表檔案：{list_file.name}")
            logging.info(f"列表包含 {len(frame_files)} 個影格")
            
            # 構建 FFmpeg 命令
            # 使用 concat demuxer 從檔案列表讀取
            
            cmd = [
                ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", list_file.name,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-crf", "18",  # 高品質（0-51，越小越好）
                "-preset", "medium",
                "-y",
                output_video_path
            ]
            
            logging.info(f"FFmpeg 命令：{' '.join(cmd)}")
            
            # 執行 FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "未知錯誤"
                logging.error(f"FFmpeg 錯誤：{error_msg}")
                raise ConversionError("生成影片失敗", details=error_msg)
            
            # 檢查輸出檔案是否存在
            if not os.path.exists(output_video_path):
                raise ConversionError("影片生成失敗", details="輸出檔案不存在")
            
            file_size = os.path.getsize(output_video_path) / (1024 * 1024)  # MB
            logging.info(f"影片生成完成：{output_video_path} ({file_size:.2f} MB)")
            
            return output_video_path
        
        finally:
            # 清理臨時列表檔案
            try:
                if list_file and os.path.exists(list_file.name):
                    os.unlink(list_file.name)
                    logging.debug(f"已清理臨時列表檔案：{list_file.name}")
            except:
                pass
            
            # 清理臨時預覽目錄
            try:
                if temp_preview_dir and os.path.exists(temp_preview_dir):
                    shutil.rmtree(temp_preview_dir, ignore_errors=True)
                    logging.debug(f"已清理臨時預覽目錄：{temp_preview_dir}")
            except:
                pass
    
    except (FileError, ConversionError):
        raise
    except Exception as e:
        logging.error(f"生成影片失敗：{str(e)}", exc_info=True)
        raise ConversionError("生成影片失敗", details=str(e))


def detect_corner_colors(image_path):
    """
    檢測圖片四個角落的顏色
    
    Args:
        image_path: 圖片路徑
    
    Returns:
        dict: 四個角落的顏色資訊
            - colors: [(x, y, hex_color), ...]
            - most_common: 最常見的顏色（十六進制）
    
    Raises:
        FileError: 檔案不存在
    """
    if not os.path.exists(image_path):
        raise FileError("找不到圖片檔案", details=f"路徑：{image_path}")
    
    try:
        # 讀取圖片（處理中文路徑問題）
        img_array = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ConversionError("無法讀取圖片檔案", details=f"路徑：{image_path}")
        
        height, width = img.shape[:2]
        
        # 四個角落的座標
        corners = [
            (0, 0, "左上"),
            (width - 1, 0, "右上"),
            (0, height - 1, "左下"),
            (width - 1, height - 1, "右下")
        ]
        
        colors = []
        color_counts = {}
        
        for x, y, name in corners:
            # 獲取 BGR 顏色
            bgr = img[y, x]
            # 轉換為 RGB
            rgb = (int(bgr[2]), int(bgr[1]), int(bgr[0]))
            # 轉換為十六進制
            hex_color = "#{:02x}{:02x}{:02x}".format(*rgb)
            
            colors.append({
                "position": name,
                "x": x,
                "y": y,
                "rgb": rgb,
                "hex": hex_color
            })
            
            # 統計顏色出現次數
            color_counts[hex_color] = color_counts.get(hex_color, 0) + 1
            
            logging.debug(f"角落 {name} ({x}, {y})：{hex_color}")
        
        # 找出最常見的顏色
        most_common_color = max(color_counts, key=color_counts.get)
        
        return {
            "colors": colors,
            "most_common": most_common_color,
            "color_counts": color_counts
        }
    
    except (FileError, ConversionError):
        raise
    except Exception as e:
        logging.error(f"檢測角落顏色失敗：{str(e)}", exc_info=True)
        raise ConversionError("檢測角落顏色失敗", details=str(e))

