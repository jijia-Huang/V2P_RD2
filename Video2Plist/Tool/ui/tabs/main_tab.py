"""
主要轉換頁面
"""
import os
import logging
import gradio as gr
from core.video import get_video_info, process_video
from core.file_utils import get_application_path
from core.error_handler import handle_error
from core.exceptions import ConfigError, FileError, ConversionError

def create_main_tab(config_manager):
    """建立主要功能頁籤"""
    # 讀取上次的設定
    last_format = config_manager.get_preference("last_format", "PNG")
    last_quality = config_manager.get_preference("last_quality", 5)
    
    with gr.Tab("轉換", id=1):
        with gr.Row():
            # 左側：上傳和基本設定
            with gr.Column(scale=2):
                mp4_file = gr.File(label="上傳 MP4 檔案", file_types=[".mp4"], height=100)

                with gr.Accordion("[點擊展開] 進階設定，設定影格率、材質大小", open=False):
                    with gr.Group():
                        with gr.Row():
                            fps_slider = gr.Slider(
                                minimum=1,
                                maximum=60,
                                value=config_manager.get_preference("last_fps", 24),
                                step=1,
                                label="FPS（影格率）",
                                info="建議用原影片的 FPS，容量大時請降低",
                                scale=2,
                            )
                            format_dropdown = gr.Dropdown(
                                choices=["PNG", "JPG"],
                                value=last_format,
                                label="輸出格式",
                                info="JPG 格式檔案較小，但不支援透明度",
                                scale=1,
                            )
                            quality_slider = gr.Slider(
                                minimum=1,
                                maximum=31,
                                value=last_quality,
                                step=1,
                                label="輸出品質",
                                info="數值越小品質越好（1-31，建議值：5）",
                                scale=2,
                            )
                            
                        # FPS 狀態顯示
                        fps_status = gr.Markdown(
                            value="ⓘ 修改 FPS 會自動重新提取影格供預覽",
                            elem_classes=["fps-status"]
                        )
                                
                        gr.Markdown("### 📝材質設定")
                        with gr.Row():
                            max_width_slider = gr.Slider(512, 8192, value=config_manager.get_preference("last_max_width", 2048), step=512, label="Max Texture Width")
                            max_height_slider = gr.Slider(512, 8192, value=config_manager.get_preference("last_max_height", 2048), step=512, label="Max Texture Height")
                        
                        # 打包器選擇
                        with gr.Row():
                            with gr.Column(scale=2):
                                packer_choice = gr.Radio(
                                    choices=["自動選擇", "TexturePacker", "Python 打包器"],
                                    value=config_manager.get_preference("last_packer_choice", "自動選擇"),
                                    label="材質打包器",
                                    info="自動選擇：優先使用 TexturePacker，未設定時使用 Python 打包器"
                                )
                            with gr.Column(scale=1):
                                packer_status = gr.Markdown(
                                    value="",
                                    elem_classes=["packer-status"]
                                )
                        
                        gr.Markdown("### 📝壓縮設定")
                        use_tinypng = gr.Checkbox(
                            label="使用 TinyPNG 壓縮 PNG",
                            value=config_manager.get_preference("last_use_tinypng", False),
                            info="啟用後會使用 TinyPNG API 對生成的 PNG 檔案進行進階壓縮，需要先在設定頁面設定 API 金鑰"
                        )
                        
                        gr.Markdown("### 📐 Frame 尺寸縮放")
                        enable_frame_resize = gr.Checkbox(
                            label="啟用 Frame 尺寸縮放",
                            value=config_manager.get_preference("last_enable_resize", False),
                            info="啟用後會在擷取影格時調整尺寸"
                        )
                        
                        # 縮放選項組（預設不可用）
                        with gr.Group(visible=True) as resize_options:
                            # 讀取初始啟用狀態
                            initial_resize_enabled = config_manager.get_preference("last_enable_resize", False)
                            
                            lock_aspect_ratio = gr.Checkbox(
                                label="鎖定長寬比",
                                value=config_manager.get_preference("last_lock_aspect", True),
                                interactive=initial_resize_enabled
                            )
                            
                            with gr.Row():
                                with gr.Column(scale=1, min_width=80):
                                    gr.HTML("<p style='margin: auto 0; padding-top: 24px;'>比例設定：</p>")
                                aspect_width = gr.Number(
                                    label="寬",
                                    value=config_manager.get_preference("last_aspect_width", 16),
                                    minimum=1,
                                    maximum=999,
                                    precision=0,
                                    interactive=initial_resize_enabled,
                                    scale=1
                                )
                                with gr.Column(scale=0, min_width=20):
                                    gr.HTML("<p style='margin: auto 0; text-align: center; padding-top: 24px;'>:</p>")
                                aspect_height = gr.Number(
                                    label="高",
                                    value=config_manager.get_preference("last_aspect_height", 9),
                                    minimum=1,
                                    maximum=999,
                                    precision=0,
                                    interactive=initial_resize_enabled,
                                    scale=1
                                )
                            
                            # 快速比例選擇按鈕
                            with gr.Row():
                                with gr.Column(scale=1, min_width=80):
                                    gr.HTML("<p style='margin: auto 0; padding-top: 8px;'>快速選擇：</p>")
                                btn_ratio_1_1 = gr.Button("1:1", size="sm", variant="secondary", scale=1)
                                btn_ratio_16_9 = gr.Button("16:9", size="sm", variant="secondary", scale=1)
                                btn_ratio_9_16 = gr.Button("9:16", size="sm", variant="secondary", scale=1)
                                btn_ratio_4_3 = gr.Button("4:3", size="sm", variant="secondary", scale=1)
                                btn_ratio_original = gr.Button("原始", size="sm", variant="secondary", scale=1)
                            
                            # 尺寸控制 Sliders
                            frame_width_slider = gr.Slider(
                                minimum=1,
                                maximum=8192,
                                value=config_manager.get_preference("last_frame_width", 1920),
                                step=1,
                                label="Frame 寬度 (Width)",
                                info="Frame 寬度（像素）",
                                interactive=initial_resize_enabled
                            )
                            
                            frame_height_slider = gr.Slider(
                                minimum=1,
                                maximum=8192,
                                value=config_manager.get_preference("last_frame_height", 1080),
                                step=1,
                                label="Frame 高度 (Height)",
                                info="Frame 高度（像素）",
                                interactive=initial_resize_enabled
                            )
                            
                            # 縮放模式選擇
                            resize_mode = gr.Radio(
                                choices=[
                                    ("拉伸變形 - 填滿目標尺寸", "stretch"),
                                    ("裁切中心 - 保持比例，裁切超出", "crop"),
                                    ("填充黑邊 - 保持比例，填充黑色", "pad_black"),
                                    ("填充透明邊 - 保持比例，填充透明 (PNG)", "pad_transparent")
                                ],
                                value=config_manager.get_preference("last_resize_mode", "stretch"),
                                label="縮放模式",
                                interactive=initial_resize_enabled
                            )
                            
                            # 提示資訊
                            frame_size_info = gr.Markdown(
                                value="ⓘ 提示：請先上傳影片",
                                elem_classes=["frame-size-info"]
                            )
                        
                        gr.Markdown("### 🎨 去背設定")
                        enable_bg_removal = gr.Checkbox(
                            label="啟用去背處理",
                            value=config_manager.get_preference("last_bg_removal_enabled", False),
                            info="提取影格後自動去背（僅 PNG 格式支援，在「去背預覽」頁面調整參數）"
                        )
                        
                        bg_removal_tolerance_display = gr.Number(
                            label="容差值（在「去背預覽」頁面調整）",
                            value=config_manager.get_preference("last_bg_removal_tolerance", 10),
                            interactive=False,
                            precision=0
                        )
                        
                        gr.Markdown("""
                        💡 **說明**：
                        - 去背功能只對 PNG 格式有效
                        - 在「去背預覽」頁面調整容差值並預覽效果
                        - 自動從影格四個角落檢測背景顏色
                        
                        ⚠️ **重要提示**：
                        - 如果啟用「Frame 尺寸縮放」且選擇「**填充透明邊**」或「**填充黑邊**」模式，可能會影響去背效果
                        - 建議搭配去背使用「**拉伸變形**」或「**裁切中心**」縮放模式
                        """)
                
            # 右側：預覽
            with gr.Column(scale=1):
                preview_video = gr.Video(label="影片預覽", show_download_button=False, show_share_button=False, include_audio=False, height="500px")
        
        with gr.Group():
            gr.Markdown("### 📝輸出設定")
            with gr.Row():
                output_name = gr.Textbox(
                    label="輸出名稱",
                    placeholder="輸入動畫名稱（例如：walk_animation）",
                    info="將會作為名稱辨識用，請盡量維持其唯一性",
                    max_lines=1,
                )
            with gr.Row():
                gr.Text("預訂輸出路徑：", show_label=False, interactive=False, text_align="right", max_lines=1, min_width=1, scale=1)
                output_path_display = gr.Textbox(interactive=False, show_label=False, max_lines=1, scale=11)

        # 進度顯示區域
        with gr.Row():
            with gr.Column(scale=3):
                result_output = gr.Markdown(
                    label="處理結果",
                    value="",
                    visible=True,
                    elem_classes=["result-display"]
                )

        # 操作按鈕
        with gr.Row():
            with gr.Column(scale=2):
                process_button = gr.Button(
                    "開始轉換",
                    variant="primary"
                )
            with gr.Column(scale=1):
                clear_button = gr.Button(
                    "清除",
                    variant="secondary"
                )

        # 事件處理函數
        import math
        
        def gcd(a, b):
            """計算最大公約數"""
            while b:
                a, b = b, a % b
            return a
        
        def get_video_dimensions(video_path):
            """獲取影片原始尺寸"""
            try:
                import subprocess
                ffmpeg_path = config_manager.get_ffmpeg_path()
                if not ffmpeg_path:
                    return None, None
                
                # 使用 ffprobe 獲取影片尺寸
                cmd = [
                    ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe") if "ffmpeg.exe" in ffmpeg_path else ffmpeg_path,
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height",
                    "-of", "csv=s=x:p=0",
                    video_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.returncode == 0 and result.stdout:
                    dimensions = result.stdout.strip().split('x')
                    if len(dimensions) == 2:
                        return int(dimensions[0]), int(dimensions[1])
                
                # 如果 ffprobe 失敗，嘗試從 ffmpeg -i 輸出解析
                cmd = [ffmpeg_path, "-i", video_path]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                for line in result.stderr.split('\n'):
                    if 'Stream' in line and 'Video:' in line:
                        # 查找類似 "1920x1080" 的模式
                        import re
                        match = re.search(r'(\d{3,4})x(\d{3,4})', line)
                        if match:
                            return int(match.group(1)), int(match.group(2))
                
                return None, None
            except Exception as e:
                import logging
                logging.error(f"獲取影片尺寸失敗：{str(e)}")
                return None, None
        
        def update_frame_size_info(original_w, original_h, target_w, target_h, mode_value):
            """更新 Frame 尺寸提示資訊"""
            if not original_w or not original_h:
                return "ⓘ 提示：請先上傳影片"
            
            # 計算原始比例
            orig_gcd = gcd(original_w, original_h)
            orig_ratio = f"{original_w//orig_gcd}:{original_h//orig_gcd}"
            
            # 計算目標比例
            if target_w and target_h:
                target_gcd = gcd(int(target_w), int(target_h))
                target_ratio = f"{int(target_w)//target_gcd}:{int(target_h)//target_gcd}"
            else:
                target_ratio = orig_ratio
                target_w, target_h = original_w, original_h
            
            # 模式說明
            mode_names = {
                "stretch": "拉伸變形",
                "crop": "裁切中心",
                "pad_black": "填充黑邊",
                "pad_transparent": "填充透明邊"
            }
            mode_name = mode_names.get(mode_value, "拉伸變形")
            
            return f"""ⓘ **原始尺寸**：{original_w}x{original_h} ({orig_ratio})  
→ **縮放後**：{int(target_w)}x{int(target_h)} ({target_ratio})  
**模式**：{mode_name}"""
        
        def on_enable_resize_change(enable):
            """啟用/停用 Frame 縮放"""
            if enable:
                # 啟用所有子元件
                return [
                    gr.update(interactive=True),  # lock_aspect_ratio
                    gr.update(interactive=True),  # aspect_width
                    gr.update(interactive=True),  # aspect_height
                    gr.update(interactive=True),  # frame_width_slider
                    gr.update(interactive=True),  # frame_height_slider
                    gr.update(interactive=True),  # resize_mode
                ]
            else:
                # 停用所有子元件
                return [
                    gr.update(interactive=False),  # lock_aspect_ratio
                    gr.update(interactive=False),  # aspect_width
                    gr.update(interactive=False),  # aspect_height
                    gr.update(interactive=False),  # frame_width_slider
                    gr.update(interactive=False),  # frame_height_slider
                    gr.update(interactive=False),  # resize_mode
                ]
        
        def on_width_change(width, lock, aspect_w, aspect_h, current_height):
            """寬度改變時的處理"""
            if not lock or not aspect_w or not aspect_h or aspect_w <= 0 or aspect_h <= 0:
                return gr.update()
            
            # 根據比例計算新高度
            new_height = int(width * aspect_h / aspect_w)
            
            # 只有當計算出的高度與當前高度不同時才更新（避免循環觸發）
            if abs(new_height - current_height) <= 1:  # 容許 1 像素誤差
                return gr.update()
            
            return gr.update(value=new_height)
        
        def on_height_change(height, lock, aspect_w, aspect_h, current_width):
            """高度改變時的處理"""
            if not lock or not aspect_w or not aspect_h or aspect_w <= 0 or aspect_h <= 0:
                return gr.update()
            
            # 根據比例計算新寬度
            new_width = int(height * aspect_w / aspect_h)
            
            # 只有當計算出的寬度與當前寬度不同時才更新（避免循環觸發）
            if abs(new_width - current_width) <= 1:  # 容許 1 像素誤差
                return gr.update()
            
            return gr.update(value=new_width)
        
        def on_aspect_ratio_change(aspect_w, aspect_h, width, lock, current_height):
            """比例設定改變時的處理"""
            if not lock or not aspect_w or not aspect_h or aspect_w <= 0 or aspect_h <= 0:
                return gr.update()
            
            # 重新計算高度
            new_height = int(width * aspect_h / aspect_w)
            
            # 只有當計算出的高度與當前高度不同時才更新（避免循環觸發）
            if abs(new_height - current_height) <= 1:  # 容許 1 像素誤差
                return gr.update()
            
            return gr.update(value=new_height)
        
        def on_ratio_button_click(ratio_w, ratio_h):
            """快速比例按鈕點擊處理"""
            def handler(current_width):
                # 計算新高度
                new_height = int(current_width * ratio_h / ratio_w)
                return [
                    True,  # lock_aspect_ratio
                    ratio_w,  # aspect_width
                    ratio_h,  # aspect_height
                    gr.update(value=new_height)  # frame_height_slider
                ]
            return handler
        
        def on_original_ratio_click(video):
            """原始比例按鈕點擊處理"""
            if not video:
                return [gr.update(), gr.update(), gr.update(), gr.update()]
            
            # 獲取影片尺寸
            width, height = get_video_dimensions(video.name)
            if not width or not height:
                return [gr.update(), gr.update(), gr.update(), gr.update()]
            
            # 計算最簡比例
            ratio_gcd = gcd(width, height)
            ratio_w = width // ratio_gcd
            ratio_h = height // ratio_gcd
            
            return [
                True,  # lock_aspect_ratio
                ratio_w,  # aspect_width
                ratio_h,  # aspect_height
                gr.update(value=width),  # frame_width_slider
                gr.update(value=height)  # frame_height_slider
            ]
        
        def cleanup_temp_files():
            """清理預覽影格檔案（不清理轉換臨時檔案）"""
            try:
                from core.file_utils import get_application_path
                
                # 只清理預覽影格目錄（完全獨立的目錄）
                preview_base = os.path.join(get_application_path(), "preview")
                if os.path.exists(preview_base):
                    import shutil
                    shutil.rmtree(preview_base, ignore_errors=True)
                    logging.info(f"已清理預覽影格目錄：{preview_base}")
                
                # 清除 config 中的預覽資訊
                config_manager.save_preferences({
                    "preview_frames_dir": "",
                    "preview_frame_count": 0,
                    "preview_fps": 24,
                    "preview_video_path": "",
                    "preview_update_time": 0
                })
                
                logging.info("預覽檔案清理完成")
            except Exception as e:
                logging.error(f"清理預覽檔案失敗：{str(e)}")

        def cleanup_all_temp_files():
            """清理所有臨時檔案（包括預覽和轉換）"""
            try:
                from core.file_utils import get_application_path
                
                # 清理預覽影格目錄
                preview_base = os.path.join(get_application_path(), "preview")
                if os.path.exists(preview_base):
                    import shutil
                    shutil.rmtree(preview_base, ignore_errors=True)
                    logging.info(f"已清理預覽影格目錄：{preview_base}")
                
                # 清理所有轉換臨時目錄
                temp_base = os.path.join(get_application_path(), "temp")
                if os.path.exists(temp_base):
                    import shutil
                    for item in os.listdir(temp_base):
                        item_path = os.path.join(temp_base, item)
                        # 清理 v2p_ 開頭的目錄（轉換臨時目錄）
                        if os.path.isdir(item_path) and item.startswith("v2p_"):
                            shutil.rmtree(item_path, ignore_errors=True)
                            logging.info(f"已清理轉換臨時目錄：{item_path}")
                
                # 清除 config 中的預覽資訊
                config_manager.save_preferences({
                    "preview_frames_dir": "",
                    "preview_frame_count": 0,
                    "preview_fps": 24,
                    "preview_video_path": "",
                    "preview_update_time": 0
                })
                
                logging.info("所有臨時檔案清理完成")
            except Exception as e:
                logging.error(f"清理臨時檔案失敗：{str(e)}")

        def update_preview(video):
            """更新預覽並提取影格"""
            try:
                if not video:
                    # 清除影片路徑和預覽資訊
                    config_manager.save_preferences({
                        "last_video_path": "",
                        "preview_frames_dir": "",
                        "preview_frame_count": 0
                    })
                    return None, gr.update(value="ⓘ 提示：請先上傳影片")
                
                # 檢查是否是新影片，如果是則清理所有舊檔案
                current_video_path = config_manager.get_preference("last_video_path", "")
                if current_video_path and current_video_path != video.name:
                    logging.info(f"檢測到新影片，清理所有舊檔案：{current_video_path} → {video.name}")
                    cleanup_all_temp_files()
                
                # 檢查檔案是否可用
                get_video_info(video.name, config_manager.get_ffmpeg_path())
                
                # 保存影片路徑
                config_manager.save_preferences({"last_video_path": video.name})
                logging.info(f"已保存影片路徑：{video.name}")
                
                # 獲取影片尺寸
                width, height = get_video_dimensions(video.name)
                
                # 立即提取影格供預覽使用
                try:
                    from core.video import extract_frames
                    
                    # 獲取當前 FPS 設定
                    current_fps = config_manager.get_preference("last_fps", 24)
                    
                    # 創建完全獨立的預覽目錄（不在 temp 下）
                    import hashlib
                    video_hash = hashlib.md5(video.name.encode()).hexdigest()[:8]
                    preview_base = os.path.join(get_application_path(), "preview")
                    frames_dir = os.path.join(preview_base, f"bg_preview_{video_hash}")
                    
                    # 清理舊的預覽影格（只清理當前預覽目錄）
                    if os.path.exists(frames_dir):
                        import shutil
                        shutil.rmtree(frames_dir, ignore_errors=True)
                    
                    os.makedirs(frames_dir, exist_ok=True)
                    
                    logging.info(f"開始提取影格供預覽：{video.name}，FPS={current_fps}")
                    
                    # 提取影格
                    frame_count = extract_frames(
                        video.name,
                        frames_dir,
                        current_fps,
                        config_manager.get_ffmpeg_path(),
                        "preview",
                        output_format="PNG",
                        quality=5
                    )
                    
                    # 保存預覽資訊
                    import time
                    config_manager.save_preferences({
                        "preview_frames_dir": frames_dir,
                        "preview_frame_count": frame_count,
                        "preview_fps": current_fps,
                        "preview_video_path": video.name,
                        "preview_update_time": time.time()  # 添加更新時間戳
                    })
                    
                    logging.info(f"預覽影格提取完成：{frame_count} 個影格，已通知去背預覽頁面")
                    
                    # 更新提示資訊
                    if width and height:
                        info_text = f"ⓘ 原始尺寸：{width}x{height}\n✅ 已提取 {frame_count} 個影格供預覽"
                    else:
                        info_text = f"✅ 已提取 {frame_count} 個影格供預覽"
                    
                    return video.name, gr.update(value=info_text)
                    
                except Exception as e:
                    logging.error(f"提取預覽影格失敗：{str(e)}")
                    # 即使提取失敗，也不影響基本功能
                    if width and height:
                        return video.name, gr.update(value=f"ⓘ 原始尺寸：{width}x{height}\n⚠️ 預覽影格提取失敗")
                    else:
                        return video.name, gr.update(value="⚠️ 預覽影格提取失敗")
                
            except Exception as e:
                logging.error(f"更新預覽失敗：{str(e)}")
                return None, gr.update(value="ⓘ 提示：影片讀取失敗")

        def clear_inputs():
            """清除輸入"""
            return [
                None,  # mp4_file
                "",    # output_name
                None,  # preview_video
                ""     # result_output
            ]

        def update_output_path(output_name):
            """更新輸出路徑顯示"""
            if not output_name:
                return ""
            # 確保輸出名稱有 v2p_ 前綴
            if not output_name.startswith("v2p_"):
                output_name = f"v2p_{output_name}"
            output_dir = os.path.join(get_application_path(), "videos", output_name)
            return f"預訂輸出目錄：{output_dir}"

        def on_fps_change(fps_value, current_video):
            """當 FPS 改變時重新提取影格"""
            try:
                if not current_video:
                    return "ⓘ 提示：請先上傳影片"
                
                # 檢查是否需要重新提取
                current_preview_fps = config_manager.get_preference("preview_fps", 24)
                if current_preview_fps == fps_value:
                    # FPS 沒變，不需要重新提取
                    frame_count = config_manager.get_preference("preview_frame_count", 0)
                    if frame_count > 0:
                        return f"ⓘ FPS={fps_value}，已有 {frame_count} 個預覽影格"
                
                # FPS 改變了，需要重新提取並清理所有臨時檔案
                logging.info(f"FPS 改變：{current_preview_fps} → {fps_value}，重新提取影格")
                
                # 清理所有臨時檔案（包括轉換臨時檔案）
                cleanup_all_temp_files()
                
                from core.video import extract_frames
                
                # 創建完全獨立的預覽目錄（不在 temp 下）
                import hashlib
                video_hash = hashlib.md5(current_video.encode()).hexdigest()[:8]
                preview_base = os.path.join(get_application_path(), "preview")
                frames_dir = os.path.join(preview_base, f"bg_preview_{video_hash}")
                
                # 清理舊的預覽影格（只清理當前預覽目錄）
                if os.path.exists(frames_dir):
                    import shutil
                    shutil.rmtree(frames_dir, ignore_errors=True)
                
                os.makedirs(frames_dir, exist_ok=True)
                
                # 重新提取影格
                frame_count = extract_frames(
                    current_video,
                    frames_dir,
                    fps_value,
                    config_manager.get_ffmpeg_path(),
                    "preview",
                    output_format="PNG",
                    quality=5
                )
                
                # 更新預覽資訊
                import time
                config_manager.save_preferences({
                    "preview_frames_dir": frames_dir,
                    "preview_frame_count": frame_count,
                    "preview_fps": fps_value,
                    "preview_video_path": current_video,
                    "preview_update_time": time.time()  # 添加更新時間戳
                })
                
                logging.info(f"FPS 更新完成：重新提取 {frame_count} 個影格，已通知去背預覽頁面")
                
                return f"✅ FPS 已更新為 {fps_value}，重新提取 {frame_count} 個影格"
                
            except Exception as e:
                logging.error(f"FPS 更新失敗：{str(e)}")
                return f"⚠️ FPS 更新失敗：{str(e)}"
        
        def on_format_change(output_format):
            """當輸出格式改變時"""
            if output_format == "JPG":
                return gr.update(value=False, interactive=False, info="JPG 不支援透明度，已禁用去背")
            else:
                return gr.update(interactive=True, info="提取影格後自動去背（僅 PNG 格式支援，在「去背預覽」頁面調整參數）")
        
        def on_packer_choice_change(packer_choice_value):
            """當打包器選擇改變時更新狀態顯示"""
            try:
                if packer_choice_value == "自動選擇":
                    # 檢查 TexturePacker 是否可用
                    tp_path = config_manager.get_texture_packer_path()
                    if tp_path and os.path.exists(tp_path):
                        return "🔧 將使用 TexturePacker"
                    else:
                        return "🐍 將使用 Python 打包器"
                elif packer_choice_value == "TexturePacker":
                    tp_path = config_manager.get_texture_packer_path()
                    if tp_path and os.path.exists(tp_path):
                        return "✅ TexturePacker 可用"
                    else:
                        return "❌ TexturePacker 未設定或不存在"
                elif packer_choice_value == "Python 打包器":
                    return "🐍 將使用 Python 打包器"
                else:
                    return ""
            except Exception as e:
                logging.error(f"更新打包器狀態失敗: {str(e)}")
                return "❓ 狀態未知"
        
        def on_convert_click(video, fps, output_name, max_width, max_height, output_format, quality, use_tinypng_compression,
                            packer_choice_value, enable_resize, lock_aspect, aspect_w, aspect_h, frame_w, frame_h, resize_mode_value,
                            enable_bg_removal_value, bg_removal_tolerance_value):
            """當點擊轉換按鈕時的處理"""
            try:
                # 儲存設定
                config_manager.save_preferences({
                    "last_fps": fps,
                    "last_max_width": max_width,
                    "last_max_height": max_height,
                    "last_format": output_format,
                    "last_quality": quality,
                    "last_use_tinypng": use_tinypng_compression,
                    "last_packer_choice": packer_choice_value,
                    "last_enable_resize": enable_resize,
                    "last_lock_aspect": lock_aspect,
                    "last_aspect_width": aspect_w,
                    "last_aspect_height": aspect_h,
                    "last_frame_width": frame_w,
                    "last_frame_height": frame_h,
                    "last_resize_mode": resize_mode_value,
                    "last_bg_removal_enabled": enable_bg_removal_value,
                    "last_bg_removal_tolerance": bg_removal_tolerance_value
                })
                
                # 加上 v2p_ 前綴
                final_name = f"v2p_{output_name}" if output_name else None
                
                # 執行轉換
                result = process_video(
                    video, fps, final_name, max_width, max_height,
                    config_manager.get_ffmpeg_path(),
                    config_manager.get_texture_packer_path(),
                    output_format,
                    quality,
                    use_tinypng=use_tinypng_compression,
                    tinypng_api_key=config_manager.get_tinypng_api_key(),
                    packer_choice=packer_choice_value,
                    enable_resize=enable_resize,
                    target_width=int(frame_w) if enable_resize else None,
                    target_height=int(frame_h) if enable_resize else None,
                    resize_mode=resize_mode_value if enable_resize else "stretch",
                    enable_bg_removal=enable_bg_removal_value,
                    bg_removal_tolerance=int(bg_removal_tolerance_value),
                    config_manager=config_manager
                )
                
                # 轉換成功後不需要清理預覽檔案（預覽檔案在獨立目錄）
                # 轉換臨時檔案會在 video.py 中自動清理
                if result and "✅" in result:
                    logging.info("轉換成功完成！")
                
                return result
            except (ConfigError, FileError, ConversionError) as e:
                return handle_error(e, ui_component=True)
            except Exception as e:
                return handle_error(e, ui_component=True)

        # 綁定事件
        mp4_file.change(
            update_preview,
            inputs=[mp4_file],
            outputs=[preview_video, frame_size_info]
        )
        
        # FPS 變更事件
        fps_slider.change(
            fn=on_fps_change,
            inputs=[fps_slider, preview_video],
            outputs=[fps_status]
        )
        
        # Frame 縮放相關事件
        enable_frame_resize.change(
            on_enable_resize_change,
            inputs=[enable_frame_resize],
            outputs=[lock_aspect_ratio, aspect_width, aspect_height, 
                    frame_width_slider, frame_height_slider, resize_mode]
        )
        
        # 寬度改變時聯動高度（使用 release 避免拖動時連續觸發）
        frame_width_slider.release(
            on_width_change,
            inputs=[frame_width_slider, lock_aspect_ratio, aspect_width, aspect_height, frame_height_slider],
            outputs=[frame_height_slider]
        )
        
        # 高度改變時聯動寬度（使用 release 避免拖動時連續觸發）
        frame_height_slider.release(
            on_height_change,
            inputs=[frame_height_slider, lock_aspect_ratio, aspect_width, aspect_height, frame_width_slider],
            outputs=[frame_width_slider]
        )
        
        # 比例改變時重新計算高度
        aspect_width.change(
            on_aspect_ratio_change,
            inputs=[aspect_width, aspect_height, frame_width_slider, lock_aspect_ratio, frame_height_slider],
            outputs=[frame_height_slider]
        )
        
        aspect_height.change(
            on_aspect_ratio_change,
            inputs=[aspect_width, aspect_height, frame_width_slider, lock_aspect_ratio, frame_height_slider],
            outputs=[frame_height_slider]
        )
        
        # 快速比例按鈕
        btn_ratio_1_1.click(
            on_ratio_button_click(1, 1),
            inputs=[frame_width_slider],
            outputs=[lock_aspect_ratio, aspect_width, aspect_height, frame_height_slider]
        )
        
        btn_ratio_16_9.click(
            on_ratio_button_click(16, 9),
            inputs=[frame_width_slider],
            outputs=[lock_aspect_ratio, aspect_width, aspect_height, frame_height_slider]
        )
        
        btn_ratio_9_16.click(
            on_ratio_button_click(9, 16),
            inputs=[frame_width_slider],
            outputs=[lock_aspect_ratio, aspect_width, aspect_height, frame_height_slider]
        )
        
        btn_ratio_4_3.click(
            on_ratio_button_click(4, 3),
            inputs=[frame_width_slider],
            outputs=[lock_aspect_ratio, aspect_width, aspect_height, frame_height_slider]
        )
        
        btn_ratio_original.click(
            on_original_ratio_click,
            inputs=[mp4_file],
            outputs=[lock_aspect_ratio, aspect_width, aspect_height, 
                    frame_width_slider, frame_height_slider]
        )

        # 格式變更事件
        format_dropdown.change(
            fn=on_format_change,
            inputs=[format_dropdown],
            outputs=[enable_bg_removal]
        )
        
        # 打包器選擇變更事件
        packer_choice.change(
            fn=on_packer_choice_change,
            inputs=[packer_choice],
            outputs=[packer_status]
        )
        
        process_button.click(
            fn=on_convert_click,
            inputs=[
                mp4_file,
                fps_slider,
                output_name,
                max_width_slider,
                max_height_slider,
                format_dropdown,
                quality_slider,
                use_tinypng,
                packer_choice,
                enable_frame_resize,
                lock_aspect_ratio,
                aspect_width,
                aspect_height,
                frame_width_slider,
                frame_height_slider,
                resize_mode,
                enable_bg_removal,
                bg_removal_tolerance_display
            ],
            outputs=[result_output]
        )

        clear_button.click(
            clear_inputs,
            outputs=[
                mp4_file,
                output_name,
                preview_video,
                result_output
            ]
        )

        output_name.change(
            update_output_path,
            inputs=[output_name],
            outputs=[output_path_display]
        )

        # 初始化打包器狀態（在返回後由 UI 管理器處理）
        
        # 返回需要在其他地方使用的元件
        return {
            "mp4_file": mp4_file,
            "output_name": output_name,
            "preview_video": preview_video,
            "result_output": result_output,
            "fps_slider": fps_slider,
            "fps_status": fps_status,
            "max_width_slider": max_width_slider,
            "max_height_slider": max_height_slider,
            "use_tinypng": use_tinypng,
            "output_path_display": output_path_display,
            "process_button": process_button,
            "enable_bg_removal": enable_bg_removal,
            "bg_removal_tolerance_display": bg_removal_tolerance_display,
            "packer_choice": packer_choice,
            "packer_status": packer_status
        } 