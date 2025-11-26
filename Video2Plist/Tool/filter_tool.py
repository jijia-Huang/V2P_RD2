#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影格濾鏡工具 - 獨立的去背預覽和處理工具

使用說明：
    python filter_tool.py

功能：
    - 從影片中提取影格
    - 使用洪水填充算法去除背景
    - 預覽處理效果
    - 批次處理所有影格
"""
import os
import sys
import json
import logging
import argparse
import shutil
import glob
from datetime import datetime

import gradio as gr

# 添加核心模組路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logger
from core.video import extract_frames, get_video_dimensions
from core.filter import (
    flood_fill_remove_background,
    process_frames_batch,
    preview_single_frame,
    detect_corner_colors,
    create_video_from_frames
)
from core.file_utils import get_application_path
from core.exceptions import FileError, ConfigError, ConversionError
from core.error_handler import handle_error
from version import VERSION_STRING


# 偏好設定檔案
PREFERENCES_FILE = "filter_preferences.json"


class FilterToolManager:
    """濾鏡工具管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.preferences = self.load_preferences()
        self.temp_frames_dir = None
        self.current_video_path = None  # 記錄當前處理的影片路徑
    
    def load_preferences(self):
        """載入偏好設定"""
        prefs_path = os.path.join(get_application_path(), PREFERENCES_FILE)
        default_prefs = {
            "last_fps": 24,
            "last_bg_color": "#00FF00",
            "last_tolerance": 10,
            "last_output_name": "filtered_video"
        }
        
        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, "r", encoding="utf-8") as f:
                    loaded_prefs = json.load(f)
                    default_prefs.update(loaded_prefs)
                    logging.info("已載入濾鏡工具偏好設定")
            except Exception as e:
                logging.warning(f"載入偏好設定失敗：{str(e)}")
        
        return default_prefs
    
    def save_preferences(self, **kwargs):
        """保存偏好設定"""
        self.preferences.update(kwargs)
        prefs_path = os.path.join(get_application_path(), PREFERENCES_FILE)
        
        try:
            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
            logging.info("已保存濾鏡工具偏好設定")
        except Exception as e:
            logging.error(f"保存偏好設定失敗：{str(e)}")
    
    def clear_temp_frames(self):
        """清除臨時影格目錄"""
        if self.temp_frames_dir and os.path.exists(self.temp_frames_dir):
            temp_base = os.path.dirname(self.temp_frames_dir)
            try:
                shutil.rmtree(temp_base, ignore_errors=True)
                logging.info(f"已清除臨時目錄：{temp_base}")
            except Exception as e:
                logging.warning(f"清除臨時目錄失敗：{str(e)}")
        
        self.temp_frames_dir = None
        self.current_video_path = None
    
    def check_video_changed(self, video_path):
        """檢查影片是否改變，如果改變則清除臨時影格"""
        if video_path != self.current_video_path:
            logging.info(f"檢測到影片改變：{self.current_video_path} → {video_path}")
            self.clear_temp_frames()
            self.current_video_path = video_path
            return True
        return False
    
    def force_re_extract(self, mp4_file, fps, output_name, ffmpeg_path):
        """強制重新提取影格"""
        try:
            if not mp4_file:
                return "❌ 請先上傳影片"
            
            # 清除舊的臨時影格
            self.clear_temp_frames()
            
            # 重新提取
            logging.info("用戶觸發強制重新提取影格")
            frame_count, frames_dir = self.extract_video_frames(mp4_file, fps, output_name, ffmpeg_path)
            
            message = f"✅ 重新提取完成！\n\n"
            message += f"📊 提取資訊：\n"
            message += f"  - 影片：{os.path.basename(mp4_file.name)}\n"
            message += f"  - FPS：{fps}\n"
            message += f"  - 影格數：{frame_count}\n"
            message += f"  - 臨時目錄：{frames_dir}\n\n"
            message += f"💡 現在可以預覽或開始處理"
            
            return message
        
        except Exception as e:
            return handle_error(e, ui_component=True)
    
    def extract_video_frames(self, mp4_file, fps, output_name, ffmpeg_path, progress=gr.Progress()):
        """提取影片影格"""
        if not mp4_file:
            raise FileError("請選擇 MP4 檔案")
        
        if not output_name:
            raise ConfigError("請輸入輸出名稱")
        
        # 創建臨時目錄
        temp_base = os.path.join(get_application_path(), "temp", f"filter_{output_name}")
        self.temp_frames_dir = os.path.join(temp_base, "frames")
        
        if os.path.exists(temp_base):
            shutil.rmtree(temp_base, ignore_errors=True)
        
        os.makedirs(self.temp_frames_dir, exist_ok=True)
        
        logging.info(f"開始提取影格：{mp4_file.name}")
        logging.info(f"FPS: {fps}, 輸出目錄: {self.temp_frames_dir}")
        
        # 提取影格（強制使用 PNG 格式，因為去背需要透明通道）
        frame_count = extract_frames(
            mp4_file.name,
            self.temp_frames_dir,
            fps,
            ffmpeg_path,
            output_name,
            output_format="PNG",
            quality=5
        )
        
        logging.info(f"成功提取 {frame_count} 個影格")
        
        return frame_count, self.temp_frames_dir
    
    def preview_first_frame(self, mp4_file, fps, output_name, bg_color, tolerance, auto_detect, ffmpeg_path):
        """預覽第一幀的處理效果"""
        try:
            # 檢查影片是否改變
            if mp4_file:
                self.check_video_changed(mp4_file.name)
            
            # 檢查是否需要重新提取影格
            if not self.temp_frames_dir or not os.path.exists(self.temp_frames_dir):
                logging.info("開始提取影格...")
                self.extract_video_frames(mp4_file, fps, output_name, ffmpeg_path)
            
            # 找到第一個影格檔案
            frame_files = sorted(glob.glob(os.path.join(self.temp_frames_dir, "*.png")))
            if not frame_files:
                return None, None, "❌ 沒有找到影格檔案"
            
            first_frame = frame_files[0]
            logging.info(f"預覽第一幀：{first_frame}")
            
            # 檢測角落顏色（總是顯示檢測結果）
            try:
                corner_info = detect_corner_colors(first_frame)
                detected_color = corner_info["most_common"]
                logging.info(f"檢測到的角落顏色：{detected_color}")
                logging.info(f"角落顏色詳情：{corner_info['colors']}")
            except Exception as e:
                logging.warning(f"檢測角落顏色失敗：{str(e)}")
                detected_color = "無法檢測"
            
            # 生成預覽
            original_img, processed_img = preview_single_frame(first_frame, bg_color, tolerance, auto_detect)
            
            message = f"✅ 預覽完成\n\n"
            message += f"📁 影格路徑：{first_frame}\n"
            message += f"🔍 檢測到的角落顏色：{detected_color}\n"
            
            if auto_detect:
                message += f"🎨 使用模式：自動檢測（從四個角落去除）\n"
            else:
                message += f"🎨 使用模式：手動指定顏色 {bg_color}\n"
            
            message += f"📏 容差值：{tolerance}\n\n"
            
            if not auto_detect and detected_color != "無法檢測" and detected_color != bg_color:
                message += f"💡 提示：檢測到的顏色與設定不同，建議使用自動檢測模式"
            
            return original_img, processed_img, message
        
        except Exception as e:
            return None, None, handle_error(e, ui_component=True)
    
    def process_all_frames(self, mp4_file, fps, output_name, bg_color, tolerance, auto_detect, ffmpeg_path, progress=gr.Progress()):
        """處理所有影格"""
        try:
            # 保存偏好設定
            self.save_preferences(
                last_fps=fps,
                last_bg_color=bg_color,
                last_tolerance=tolerance,
                last_output_name=output_name,
                last_auto_detect=auto_detect
            )
            
            # 檢查影片是否改變
            if mp4_file:
                self.check_video_changed(mp4_file.name)
            
            # 檢查是否需要重新提取影格
            if not self.temp_frames_dir or not os.path.exists(self.temp_frames_dir):
                progress(0, desc="正在提取影格...")
                frame_count, frames_dir = self.extract_video_frames(mp4_file, fps, output_name, ffmpeg_path, progress)
            else:
                frames_dir = self.temp_frames_dir
                frame_files = glob.glob(os.path.join(frames_dir, "*.png"))
                frame_count = len(frame_files)
            
            # 創建輸出目錄
            output_dir = os.path.join(get_application_path(), "videos", f"{output_name}_filtered")
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir, ignore_errors=True)
            os.makedirs(output_dir, exist_ok=True)
            
            logging.info(f"開始批次處理 {frame_count} 個影格")
            logging.info(f"輸出目錄：{output_dir}")
            
            # 進度回調
            def progress_callback(current, total, message):
                progress((current / total), desc=f"處理中：{current}/{total}")
            
            # 批次處理
            progress(0, desc="正在去背處理...")
            result = process_frames_batch(
                frames_dir,
                bg_color,
                tolerance,
                output_dir,
                auto_detect,
                progress_callback
            )
            
            # 保存處理參數
            metadata = {
                "output_name": output_name,
                "fps": fps,
                "auto_detect": auto_detect,
                "bg_color": bg_color if not auto_detect else "自動檢測",
                "tolerance": tolerance,
                "frame_count": frame_count,
                "success_count": result["success"],
                "failed_count": result["failed"],
                "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tool_version": VERSION_STRING
            }
            
            metadata_path = os.path.join(output_dir, f"{output_name}_filter_metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 清理臨時檔案
            if self.temp_frames_dir and os.path.exists(self.temp_frames_dir):
                temp_base = os.path.dirname(self.temp_frames_dir)
                shutil.rmtree(temp_base, ignore_errors=True)
                self.temp_frames_dir = None
            
            # 生成處理後的影片
            logging.info("開始生成處理後的影片...")
            output_video_path = os.path.join(output_dir, f"{output_name}_filtered.mp4")
            
            try:
                progress(0.9, desc="正在生成影片...")
                create_video_from_frames(output_dir, output_video_path, fps, ffmpeg_path)
                video_generated = True
                video_size = os.path.getsize(output_video_path) / (1024 * 1024)  # MB
                logging.info(f"影片生成成功：{output_video_path} ({video_size:.2f} MB)")
            except Exception as e:
                logging.error(f"生成影片失敗：{str(e)}")
                video_generated = False
                output_video_path = None
            
            message = f"✅ 處理完成！\n\n"
            message += f"📊 統計資訊：\n"
            message += f"  - 總影格數：{result['total']}\n"
            message += f"  - 成功處理：{result['success']}\n"
            message += f"  - 處理失敗：{result['failed']}\n"
            message += f"  - 成功率：{result['success']/result['total']*100:.1f}%\n\n"
            message += f"📁 輸出目錄：{output_dir}\n"
            
            if video_generated:
                message += f"🎬 處理後影片：{output_video_path} ({video_size:.2f} MB)\n"
                message += f"🎨 預覽背景色：洋紅色 #FF00FF（去背區域顯示為此顏色）\n\n"
                message += f"💡 影片已生成，可在下方預覽\n"
                message += f"📌 注意：PNG 影格保留完整透明資訊，MP4 預覽用洋紅色顯示透明區域\n"
            else:
                message += f"\n⚠️ 影片生成失敗（影格已保存）\n"
            
            if result['failed'] > 0:
                message += f"\n⚠️ 部分影格處理失敗，請檢查日誌"
            
            logging.info(message)
            
            return message, output_video_path if video_generated else None
        
        except Exception as e:
            # 清理臨時檔案
            if self.temp_frames_dir and os.path.exists(self.temp_frames_dir):
                temp_base = os.path.dirname(self.temp_frames_dir)
                shutil.rmtree(temp_base, ignore_errors=True)
                self.temp_frames_dir = None
            
            return handle_error(e, ui_component=True), None


def create_filter_ui(manager):
    """創建濾鏡工具 UI"""
    
    # 從配置文件讀取 FFmpeg 路徑
    config_path = os.path.join(get_application_path(), "config.yaml")
    ffmpeg_path = None
    
    if os.path.exists(config_path):
        import yaml
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                ffmpeg_path = config.get("ffmpeg_path", "")
        except:
            pass
    
    if not ffmpeg_path:
        ffmpeg_path = os.path.join(get_application_path(), "ffmpeg", "ffmpeg.exe")
    
    with gr.Blocks(
        css="""
        .container { max-width: 1400px; margin: auto; }
        .preview-box { border: 2px solid #ddd; border-radius: 8px; padding: 10px; }
        """,
        theme=gr.themes.Soft(),
        title=f"影格濾鏡工具 {VERSION_STRING}"
    ) as demo:
        gr.Markdown(f"# 🎨 影格濾鏡工具 - 洪水填充去背 {VERSION_STRING}")
        gr.Markdown("**獨立測試工具**：提取影格 → 去背處理 → 預覽效果 → 批次處理")
        
        with gr.Row():
            # 左側：設定區域
            with gr.Column(scale=1):
                gr.Markdown("## 📤 上傳影片")
                mp4_file = gr.File(
                    label="上傳 MP4 檔案",
                    file_types=[".mp4"],
                    height=100
                )
                
                video_info = gr.Textbox(
                    label="影片資訊",
                    interactive=False,
                    lines=3
                )
                
                gr.Markdown("## ⚙️ 提取設定")
                
                fps_slider = gr.Slider(
                    minimum=1,
                    maximum=60,
                    value=manager.preferences.get("last_fps", 24),
                    step=1,
                    label="FPS（影格率）",
                    info="建議使用原影片的 FPS"
                )
                
                output_name = gr.Textbox(
                    label="輸出名稱",
                    value=manager.preferences.get("last_output_name", "filtered_video"),
                    placeholder="例如：character_animation"
                )
                
                re_extract_btn = gr.Button(
                    "🔄 重新提取影格",
                    variant="secondary",
                    size="sm"
                )
                
                re_extract_result = gr.Markdown(visible=False)
                
                gr.Markdown("## 🎨 去背參數")
                
                auto_detect = gr.Checkbox(
                    label="自動檢測角落顏色",
                    value=manager.preferences.get("last_auto_detect", True),
                    info="啟用後會自動從四個角落檢測背景顏色並去除"
                )
                
                bg_color = gr.ColorPicker(
                    label="手動指定背景顏色",
                    value=manager.preferences.get("last_bg_color", "#00FF00"),
                    info="僅在關閉自動檢測時使用",
                    interactive=not manager.preferences.get("last_auto_detect", True)
                )
                
                tolerance_slider = gr.Slider(
                    minimum=0,
                    maximum=50,
                    value=manager.preferences.get("last_tolerance", 10),
                    step=1,
                    label="容差值",
                    info="數值越大，容許的顏色差異越大"
                )
                
                gr.Markdown("---")
                
                with gr.Row():
                    preview_btn = gr.Button("👁️ 預覽第一幀", variant="secondary", size="lg")
                    process_btn = gr.Button("🚀 開始處理", variant="primary", size="lg")
            
            # 右側：預覽區域
            with gr.Column(scale=2):
                gr.Markdown("## 🖼️ 預覽效果")
                
                preview_message = gr.Markdown("點擊「預覽第一幀」查看去背效果")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 原始影格")
                        original_preview = gr.Image(
                            label="原始",
                            type="pil",
                            height=400
                        )
                    
                    with gr.Column():
                        gr.Markdown("### 處理後效果")
                        processed_preview = gr.Image(
                            label="去背後",
                            type="pil",
                            height=400
                        )
                
                gr.Markdown("## 📊 處理結果")
                result_output = gr.Markdown("等待處理...")
                
                gr.Markdown("## 🎬 處理後影片預覽")
                processed_video = gr.Video(
                    label="去背後的影片",
                    height=400
                )
        
        # 事件綁定
        
        # 上傳影片後顯示資訊並清除舊的臨時影格
        def on_video_upload(video_file):
            if video_file:
                # 清除舊的臨時影格
                manager.clear_temp_frames()
                
                try:
                    width, height = get_video_dimensions(video_file.name, ffmpeg_path)
                    if width and height:
                        return f"📹 影片尺寸：{width}x{height}\n💡 已清除舊的臨時影格，準備重新提取"
                    else:
                        return "✅ 影片已上傳\n💡 已清除舊的臨時影格，準備重新提取"
                except:
                    return "✅ 影片已上傳\n💡 已清除舊的臨時影格，準備重新提取"
            return ""
        
        mp4_file.change(
            fn=on_video_upload,
            inputs=[mp4_file],
            outputs=[video_info]
        )
        
        # 重新提取按鈕
        def on_re_extract_click(*args):
            result = manager.force_re_extract(*args, ffmpeg_path)
            return result, gr.update(visible=True)
        
        re_extract_btn.click(
            fn=on_re_extract_click,
            inputs=[mp4_file, fps_slider, output_name],
            outputs=[re_extract_result, re_extract_result]
        )
        
        # auto_detect 切換時，啟用/禁用顏色選擇器
        def toggle_bg_color(auto_detect_enabled):
            return gr.update(interactive=not auto_detect_enabled)
        
        auto_detect.change(
            fn=toggle_bg_color,
            inputs=[auto_detect],
            outputs=[bg_color]
        )
        
        # 預覽按鈕
        preview_btn.click(
            fn=lambda *args: manager.preview_first_frame(*args, ffmpeg_path),
            inputs=[mp4_file, fps_slider, output_name, bg_color, tolerance_slider, auto_detect],
            outputs=[original_preview, processed_preview, preview_message]
        )
        
        # 處理按鈕
        process_btn.click(
            fn=lambda *args, progress=gr.Progress(): manager.process_all_frames(*args, ffmpeg_path, progress),
            inputs=[mp4_file, fps_slider, output_name, bg_color, tolerance_slider, auto_detect],
            outputs=[result_output, processed_video]
        )
        
        gr.Markdown("""
        ---
        ### 💡 使用提示
        
        1. **去背模式選擇**：
           - **自動檢測（推薦）**：從影格四個角落自動檢測背景顏色並去除
             - 適合大多數情況
             - 不需要知道準確的背景顏色
             - 自動處理顏色差異
           - **手動指定**：只去除指定的顏色
             - 適合需要精確控制的情況
             - 綠幕：#00FF00，藍幕：#0000FF
        
        2. **容差值調整**：
           - 純色背景：使用較小值（5-10）
           - 不均勻背景：使用較大值（15-30）
           - 先預覽第一幀，根據效果調整
           - 數值越大，去除的區域越廣
        
        3. **重新提取影格**：
           - 點擊「🔄 重新提取影格」按鈕可以強制重新提取
           - 適用情況：
             - 修改了 FPS 設定
             - 修改了輸出名稱
             - 想要清除快取重新開始
        
        4. **輸出內容**：
           - PNG 影格：支援透明通道，保存在 `Tool/videos/{輸出名稱}_filtered/`
           - MP4 影片：處理後自動生成，可直接預覽效果
           - Metadata：保存處理參數供參考
        
        5. **後續整合**：
           - 確認效果後，可將去背功能整合到主系統
           - 處理後的影格可直接用於材質打包
        """)
    
    return demo


def main():
    """主函數"""
    # 解析命令列參數
    parser = argparse.ArgumentParser(description="影格濾鏡工具 - 洪水填充去背")
    parser.add_argument("--port", type=int, default=7861, help="服務器端口（預設：7861）")
    parser.add_argument("--share", action="store_true", help="生成公開分享連結")
    parser.add_argument("--debug", action="store_true", help="啟用除錯模式")
    args = parser.parse_args()
    
    # 設定日誌
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)
    
    logging.info("="*60)
    logging.info(f"影格濾鏡工具 {VERSION_STRING} 啟動中...")
    logging.info("="*60)
    
    # 創建管理器
    manager = FilterToolManager()
    
    # 創建 UI
    demo = create_filter_ui(manager)
    
    # 啟動服務器
    logging.info(f"啟動 Gradio 服務器，端口：{args.port}")
    demo.launch(
        server_port=args.port,
        share=args.share,
        inbrowser=True
    )


if __name__ == "__main__":
    main()

