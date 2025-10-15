"""
主要轉換頁面
"""
import gradio as gr
from core.video import get_video_info, process_video
from core.file_utils import get_application_path
from core.error_handler import handle_error
from core.exceptions import ConfigError, FileError, ConversionError
import os

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
                                
                        gr.Markdown("### 📝材質設定")
                        with gr.Row():
                            max_width_slider = gr.Slider(512, 8192, value=config_manager.get_preference("last_max_width", 2048), step=512, label="Max Texture Width")
                            max_height_slider = gr.Slider(512, 8192, value=config_manager.get_preference("last_max_height", 2048), step=512, label="Max Texture Height")
                        
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
        
        def update_preview(video):
            """更新預覽"""
            try:
                if not video:
                    return None, gr.update(value="ⓘ 提示：請先上傳影片")
                # 只檢查檔案是否可用，不顯示詳細資訊
                get_video_info(video.name, config_manager.get_ffmpeg_path())
                
                # 獲取影片尺寸並更新提示
                width, height = get_video_dimensions(video.name)
                if width and height:
                    return video.name, gr.update(value=f"ⓘ 原始尺寸：{width}x{height}")
                
                return video.name, gr.update(value="ⓘ 提示：無法讀取影片尺寸")
            except Exception:
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

        def on_convert_click(video, fps, output_name, max_width, max_height, output_format, quality, use_tinypng_compression,
                            enable_resize, lock_aspect, aspect_w, aspect_h, frame_w, frame_h, resize_mode_value):
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
                    "last_enable_resize": enable_resize,
                    "last_lock_aspect": lock_aspect,
                    "last_aspect_width": aspect_w,
                    "last_aspect_height": aspect_h,
                    "last_frame_width": frame_w,
                    "last_frame_height": frame_h,
                    "last_resize_mode": resize_mode_value
                })
                
                # 加上 v2p_ 前綴
                final_name = f"v2p_{output_name}" if output_name else None
                return process_video(
                    video, fps, final_name, max_width, max_height,
                    config_manager.get_ffmpeg_path(),
                    config_manager.get_texture_packer_path(),
                    output_format,
                    quality,
                    use_tinypng=use_tinypng_compression,
                    tinypng_api_key=config_manager.get_tinypng_api_key(),
                    enable_resize=enable_resize,
                    target_width=int(frame_w) if enable_resize else None,
                    target_height=int(frame_h) if enable_resize else None,
                    resize_mode=resize_mode_value if enable_resize else "stretch"
                )
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
                enable_frame_resize,
                lock_aspect_ratio,
                aspect_width,
                aspect_height,
                frame_width_slider,
                frame_height_slider,
                resize_mode
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

        # 返回需要在其他地方使用的元件
        return {
            "mp4_file": mp4_file,
            "output_name": output_name,
            "preview_video": preview_video,
            "result_output": result_output,
            "fps_slider": fps_slider,
            "max_width_slider": max_width_slider,
            "max_height_slider": max_height_slider,
            "use_tinypng": use_tinypng,
            "output_path_display": output_path_display,
            "process_button": process_button
        } 