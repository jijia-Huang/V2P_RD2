"""
去背預覽頁面
"""
import os
import glob
import logging
import gradio as gr
from core.video import extract_frames, get_video_dimensions
from core.filter import preview_single_frame
from core.file_utils import get_application_path
from core.error_handler import handle_error
from core.exceptions import FileError, ConfigError


def create_bg_removal_tab(config_manager):
    """建立去背預覽頁籤"""
    
    # 共享狀態
    state = {
        'temp_frames_dir': None,
        'frame_files': [],
        'current_video': None,
        'preview_cache': {},  # 快取已預覽的圖片 {(frame_idx, tolerance): (original_img, processed_img)}
        'last_check_time': 0  # 上次檢查時間戳，用於檢測更新
    }
    
    # 從配置讀取上次的設定
    last_tolerance = config_manager.get_preference("last_bg_removal_tolerance", 10)
    last_enabled = config_manager.get_preference("last_bg_removal_enabled", False)
    
    # 獲取 FFmpeg 路徑
    ffmpeg_path = config_manager.get_ffmpeg_path()
    if not ffmpeg_path:
        ffmpeg_path = os.path.join(get_application_path(), "ffmpeg", "ffmpeg.exe")
    
    with gr.Tab("🖼️ 去背預覽", id=2):
        gr.Markdown("""
        ## 去背參數預覽和調整
        
        自動使用轉換頁面的影片進行去背預覽，調整滿意後回到轉換頁面執行完整處理。
        
        ⚡ **自動預覽**：拖動 Slider 停下時自動更新預覽  
        💾 **智能快取**：已預覽的影格會被快取，再次查看瞬間載入  
        🤖 **全自動**：自動載入轉換頁面的影片並提取影格
        """)
        
        with gr.Row():
            # 左側：控制區
            with gr.Column(scale=1):
                gr.Markdown("### 📹 影片狀態")
                
                video_status = gr.Markdown(
                    value="🔄 正在檢查轉換頁面的影片...",
                    elem_classes=["video-status"]
                )
                
                refresh_btn = gr.Button(
                    "🔄 載入轉換頁面的影格",
                    variant="primary",
                    size="sm"
                )
                
                gr.Markdown("### 🎨 去背參數")
                
                enable_bg_removal = gr.Checkbox(
                    label="啟用去背",
                    value=last_enabled,
                    info="在轉換頁面執行時是否啟用去背"
                )
                
                tolerance_slider = gr.Slider(
                    minimum=0,
                    maximum=50,
                    value=last_tolerance,
                    step=1,
                    label="容差值",
                    info="數值越大，去除的背景區域越廣"
                )
                
                gr.Markdown("""
                💡 **說明**：
                - 自動從影格四個角落檢測背景顏色
                - 調整容差值以控制去背範圍
                - 透明區域在預覽中顯示為洋紅色
                """)
                
                gr.Markdown("### 🎬 影格選擇")
                
                frame_slider = gr.Slider(
                    minimum=1,
                    maximum=100,
                    value=1,
                    step=1,
                    label="影格編號",
                    info="拖動選擇要預覽的影格"
                )
                
                frame_info = gr.Markdown("請先提取影格")
                
                preview_btn = gr.Button(
                    "👁️ 預覽當前影格",
                    variant="secondary",
                    size="lg"
                )
                
                save_preview_btn = gr.Button(
                    "💾 保存去背後的圖片",
                    variant="primary",
                    size="lg"
                )
                
                save_message = gr.Markdown("")
            
            # 右側：預覽區
            with gr.Column(scale=2):
                gr.Markdown("### 🖼️ 預覽對比")
                
                preview_message = gr.Markdown("上傳影片並提取影格後，可以預覽去背效果")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 原始影格")
                        original_preview = gr.Image(
                            label="原始",
                            type="pil",
                            height=400
                        )
                    
                    with gr.Column():
                        gr.Markdown("#### 去背後效果")
                        processed_preview = gr.Image(
                            label="去背後（洋紅色=透明區域）",
                            type="pil",
                            height=400
                        )
        
        gr.Markdown("""
        ---
        ### 💡 使用提示
        
        1. **上傳影片**：到「轉換」頁面上傳 MP4 檔案，**會自動提取影格** 🤖
        2. **切換頁面**：回到此「去背預覽」頁面
        3. **載入影格**：點擊「🔄 載入轉換頁面的影格」按鈕
        4. **調整參數**：拖動容差值 Slider
        5. **選擇影格**：拖動影格編號 Slider，**停下時自動預覽** ⚡
        6. **查看效果**：左右對比原始和去背後的效果
        7. **快速切換**：已預覽的影格會被快取，瞬間載入 💾
        8. **確認滿意**：回到「轉換」頁面，勾選「啟用去背」執行完整處理
        
        ⚠️ **注意**：
        - 上傳影片時會自動提取影格，但需要手動點擊載入按鈕
        - 拖動 Slider 停下時會自動預覽
        - 快取會在切換影片時自動清空
        - 轉換時會複用已提取的影格，節省時間
        """)
    
    # 事件處理函數
    
    def auto_load_and_extract():
        """自動載入已提取的影格"""
        try:
            # 從偏好設定讀取預覽影格資訊
            preview_frames_dir = config_manager.get_preference("preview_frames_dir", "")
            preview_frame_count = config_manager.get_preference("preview_frame_count", 0)
            preview_fps = config_manager.get_preference("preview_fps", 24)
            preview_video_path = config_manager.get_preference("preview_video_path", "")
            preview_update_time = config_manager.get_preference("preview_update_time", 0)
            
            # 檢查是否有更新
            if preview_update_time > state.get('last_check_time', 0):
                logging.info(f"檢測到影格更新：{preview_update_time} > {state.get('last_check_time', 0)}")
                # 強制重新載入
                state['last_check_time'] = preview_update_time
                force_reload = True
            else:
                force_reload = False
            
            # 檢查預覽影格目錄是否存在且有檔案
            if (preview_frames_dir and 
                os.path.exists(preview_frames_dir) and 
                preview_frame_count > 0):
                
                # 獲取影格檔案列表（排除 filter_ 前綴的去背檔案，只使用原始影格）
                all_png_files = sorted(glob.glob(os.path.join(preview_frames_dir, "*.png")))
                frame_files = [f for f in all_png_files if not os.path.basename(f).startswith('filter_')]
                logging.info(f"掃描到 {len(all_png_files)} 個 PNG 檔案，過濾後剩餘 {len(frame_files)} 個原始影格")
                
                if len(frame_files) > 0:
                    # 檢查是否已經載入過相同的影格
                    # 需要比較：目錄路徑、檔案列表、FPS、影片路徑
                    current_fps = state.get('current_fps', 0)
                    current_video_path = state.get('current_video', "")
                    
                    is_same_frames = (
                        state.get('temp_frames_dir') == preview_frames_dir and
                        state.get('frame_files') == frame_files and
                        current_fps == preview_fps and
                        current_video_path == preview_video_path and
                        not force_reload  # 如果有更新，強制重新載入
                    )
                    
                    if is_same_frames:
                        status_msg = f"✅ 影格已載入完成\n\n"
                        status_msg += f"📁 來源：{os.path.basename(preview_video_path)}\n"
                        status_msg += f"🎬 FPS：{preview_fps}\n"
                        status_msg += f"📊 影格數量：{len(frame_files)}\n\n"
                        status_msg += f"⚡ 拖動 Slider 可立即預覽"
                        
                        # 如果影格數量沒變，不要重置 Slider 的值
                        current_max = len(frame_files)
                        slider_update = gr.update(maximum=current_max)  # 不設定 value，保持當前值
                        
                        # 計算當前影格資訊（不重置）
                        current_frame = min(state.get('current_frame_index', 1), current_max)
                        frame_info_text = f"第 {current_frame} 幀 / 共 {current_max} 幀"
                        
                        return status_msg, slider_update, frame_info_text
                    
                    # 載入影格到狀態（新的或更新的影格）
                    state['temp_frames_dir'] = preview_frames_dir
                    state['frame_files'] = frame_files
                    state['current_video'] = preview_video_path
                    state['current_fps'] = preview_fps  # 新增：記錄當前 FPS
                    
                    # 清空快取（因為是新的或更新的影格）
                    old_cache_size = len(state.get('preview_cache', {}))
                    state['preview_cache'] = {}
                    
                    if old_cache_size > 0:
                        logging.info(f"影格已更新，清空預覽快取（原有 {old_cache_size} 個）")
                    else:
                        logging.info("載入新影格，初始化預覽快取")
                    
                    # 判斷是新載入還是更新
                    if force_reload:
                        update_type = "自動檢測到更新"
                    elif current_fps != preview_fps and current_fps > 0:
                        update_type = f"FPS 已更新：{current_fps} → {preview_fps}"
                    elif current_video_path != preview_video_path:
                        update_type = "影片已更換"
                    else:
                        update_type = "首次載入"
                    
                    status_msg = f"✅ 自動載入完成！\n\n"
                    status_msg += f"📁 來源：{os.path.basename(preview_video_path)}\n"
                    status_msg += f"🎬 FPS：{preview_fps}（來自轉換）\n"
                    status_msg += f"📊 影格數量：{len(frame_files)}\n"
                    status_msg += f"🔄 狀態：{update_type}\n\n"
                    status_msg += f"⚡ 拖動 Slider 可立即預覽\n"
                    status_msg += f"💾 已預覽的影格會被快取"
                    
                    slider_update = gr.update(maximum=len(frame_files), value=1)
                    frame_info_text = f"第 1 幀 / 共 {len(frame_files)} 幀"
                    
                    logging.info(f"自動載入完成：使用已提取的 {len(frame_files)} 個影格")
                    
                    return status_msg, slider_update, frame_info_text
            
            # 如果沒有預覽影格，顯示提示
            status_msg = f"💡 請先到「轉換」頁面處理影片\n\n"
            status_msg += f"轉換時會自動提取影格供此頁面預覽使用\n\n"
            status_msg += f"🔄 處理完成後，此頁面會自動載入影格"
            
            return status_msg, gr.update(), ""
                
        except Exception as e:
            logging.error(f"自動載入失敗：{str(e)}", exc_info=True)
            return f"❌ 自動載入失敗：{str(e)}", gr.update(), ""
    
    def update_frame_info(frame_index):
        """更新影格資訊"""
        if state['frame_files']:
            total = len(state['frame_files'])
            # 記錄當前影格索引
            state['current_frame_index'] = int(frame_index)
            return f"第 {int(frame_index)} 幀 / 共 {total} 幀"
        return "請先提取影格"
    
    def preview_current_frame(frame_index, tolerance):
        """預覽當前選擇的影格"""
        try:
            if not state['frame_files']:
                return None, None, "❌ 請先提取影格"
            
            # 獲取選擇的影格
            frame_idx = int(frame_index) - 1  # Slider 從 1 開始，索引從 0 開始
            
            if frame_idx < 0 or frame_idx >= len(state['frame_files']):
                return None, None, f"❌ 影格索引超出範圍：{frame_idx + 1}"
            
            # 檢查快取
            cache_key = (frame_idx, int(tolerance))
            if cache_key in state['preview_cache']:
                logging.info(f"🎯 從快取載入預覽：第 {frame_idx + 1} 幀，容差 {tolerance}")
                original_img, processed_img = state['preview_cache'][cache_key]
                
                message = f"✅ 預覽完成（從快取載入）\n\n"
                message += f"📁 影格：第 {frame_idx + 1}/{len(state['frame_files'])} 幀\n"
                message += f"🎨 模式：自動檢測（從四個角落）\n"
                message += f"📏 容差值：{tolerance}\n"
                message += f"🎨 洋紅色區域 = 透明（已去背）\n"
                message += f"⚡ 快取命中！瞬間載入"
                
                return original_img, processed_img, message
            
            frame_path = state['frame_files'][frame_idx]
            
            logging.info(f"🔄 處理新預覽：第 {frame_idx + 1}/{len(state['frame_files'])} 幀：{os.path.basename(frame_path)}")
            logging.info(f"容差值：{tolerance}")
            
            # 使用去背函數預覽
            original_img, processed_img = preview_single_frame(
                frame_path,
                bg_color=None,
                tolerance=tolerance,
                auto_detect=True
            )
            
            # 存入快取
            state['preview_cache'][cache_key] = (original_img, processed_img)
            cache_size = len(state['preview_cache'])
            logging.info(f"💾 已存入快取，當前快取數量：{cache_size}")
            
            message = f"✅ 預覽完成\n\n"
            message += f"📁 影格：第 {frame_idx + 1}/{len(state['frame_files'])} 幀\n"
            message += f"🎨 模式：自動檢測（從四個角落）\n"
            message += f"📏 容差值：{tolerance}\n"
            message += f"🎨 洋紅色區域 = 透明（已去背）\n\n"
            message += f"💾 已快取（共 {cache_size} 個）\n"
            message += f"💡 調整 Slider 會自動預覽，已快取的會瞬間載入"
            
            return original_img, processed_img, message
        
        except Exception as e:
            logging.error(f"預覽失敗：{str(e)}", exc_info=True)
            return None, None, handle_error(e, ui_component=True)
    
    def save_bg_removal_preference(enabled, tolerance):
        """保存去背偏好設定"""
        try:
            config_manager.save_preferences({
                "last_bg_removal_enabled": enabled,
                "last_bg_removal_tolerance": tolerance
            })
            logging.debug(f"已保存去背偏好設定：enabled={enabled}, tolerance={tolerance}")
            logging.info(f"去背容差值已更新: {tolerance}")
        except Exception as e:
            logging.error(f"保存偏好設定失敗：{str(e)}")
    
    def save_preview_image(frame_slider_value, tolerance):
        """保存當前預覽的去背圖片"""
        try:
            if not state['frame_files']:
                return "❌ 請先提取影格"
            
            frame_idx = int(frame_slider_value) - 1
            if frame_idx < 0 or frame_idx >= len(state['frame_files']):
                return "❌ 影格索引超出範圍"
            
            # 檢查快取中是否有這個影格
            cache_key = (frame_idx, tolerance)
            if cache_key not in state['preview_cache']:
                return "❌ 請先預覽此影格"
            
            # 從快取中獲取去背後的圖片
            _, processed_img = state['preview_cache'][cache_key]
            
            # 保存到 videos 目錄
            from core.file_utils import get_application_path
            videos_dir = os.path.join(get_application_path(), "videos")
            os.makedirs(videos_dir, exist_ok=True)
            
            # 生成檔案名
            frame_path = state['frame_files'][frame_idx]
            frame_name = os.path.splitext(os.path.basename(frame_path))[0]
            output_filename = f"preview_{frame_name}_tolerance{tolerance}.png"
            output_path = os.path.join(videos_dir, output_filename)
            
            # 保存圖片
            processed_img.save(output_path, 'PNG')
            
            logging.info(f"已保存預覽圖片：{output_path}")
            return f"✅ 已保存到：\n`{output_path}`"
            
        except Exception as e:
            logging.error(f"保存預覽圖片失敗：{str(e)}", exc_info=True)
            return handle_error(e, ui_component=True)
    
    # 事件綁定
    
    # 手動載入按鈕
    refresh_btn.click(
        fn=auto_load_and_extract,
        inputs=[],
        outputs=[video_status, frame_slider, frame_info]
    )
    
    # 減少自動檢查頻率（每 5 秒檢查一次，避免干擾用戶操作）
    auto_check_timer = gr.Timer(value=5)
    auto_check_timer.tick(
        fn=auto_load_and_extract,
        inputs=[],
        outputs=[video_status, frame_slider, frame_info]
    )
    
    # 影格 Slider 拖動時更新資訊
    frame_slider.change(
        fn=update_frame_info,
        inputs=[frame_slider],
        outputs=[frame_info]
    )
    
    # 影格 Slider 停下時自動預覽（release 事件）
    frame_slider.release(
        fn=preview_current_frame,
        inputs=[frame_slider, tolerance_slider],
        outputs=[original_preview, processed_preview, preview_message]
    )
    
    # 容差值 Slider 停下時自動預覽
    tolerance_slider.release(
        fn=preview_current_frame,
        inputs=[frame_slider, tolerance_slider],
        outputs=[original_preview, processed_preview, preview_message]
    )
    
    # 手動預覽按鈕（保留，方便用戶立即刷新）
    preview_btn.click(
        fn=preview_current_frame,
        inputs=[frame_slider, tolerance_slider],
        outputs=[original_preview, processed_preview, preview_message]
    )
    
    # 保存預覽圖片按鈕
    save_preview_btn.click(
        fn=save_preview_image,
        inputs=[frame_slider, tolerance_slider],
        outputs=[save_message]
    )
    
    # 參數變更時自動保存
    enable_bg_removal.change(
        fn=lambda enabled, tolerance: save_bg_removal_preference(enabled, tolerance),
        inputs=[enable_bg_removal, tolerance_slider],
        outputs=[]
    )
    
    tolerance_slider.change(
        fn=lambda enabled, tolerance: save_bg_removal_preference(enabled, tolerance),
        inputs=[enable_bg_removal, tolerance_slider],
        outputs=[]
    )
    
    # 返回元件引用
    components = {
        "bg_removal_video_status": video_status,
        "bg_removal_enable": enable_bg_removal,
        "bg_removal_tolerance": tolerance_slider
    }
    
    return components

