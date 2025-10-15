"""
設定頁面
"""
import gradio as gr
from core.error_handler import handle_error
from core.exceptions import ConfigError
from ..components.tk_file_picker import TkFilePicker
from core.file_utils import get_application_path

def create_settings_tab(config_manager):
    """建立設定頁籤"""
    with gr.Tab("設定", id=0):
        gr.Markdown("### 目前設定值")
        
        # FFmpeg 設定
        ffmpeg_picker = TkFilePicker(
            title="選擇 FFmpeg.exe",
            file_types=[("執行檔", "*.exe")],
            initial_dir=get_application_path()
        )
        
        ffmpeg_path_input, _ = ffmpeg_picker.create_ui(
            textbox_label="FFmpeg.exe 路徑",
            button_text="📁 選擇目標",
            scale=(4, 1),
            value=config_manager.get_ffmpeg_path()
        )

        # 事件處理
        def test_texture_packer(path):
            """測試 TexturePacker"""
            try:
                if not path:
                    raise ConfigError("請選擇 TexturePacker 執行檔")
                version = config_manager.test_executable(path, "TexturePacker")
                if version and version != "":
                    if version.startswith("TexturePacker"):
                        return f"✅ TexturePacker 可用！\n版本：{version}"
                    else:
                        # 需要幫助輸入 agree 去同意 TexturePacker 第一次執行 Console 的輸出
                        agree_result = config_manager.agree_texture_packer(path)
                        if agree_result == "ok":
                            return test_texture_packer(path)
                        else:
                            return "❌ TexturePacker 無法執行"
                else:
                    return "❌ TexturePacker 無法執行"
            except (ConfigError, Exception) as e:
                return handle_error(e, ui_component=True)
        
        # TexturePacker 設定
        tp_picker = TkFilePicker(
            title="選擇 TexturePacker.exe",
            file_types=[("執行檔", "*.exe")],
            initial_dir="C:/Program Files/CodeAndWeb/TexturePacker/bin",
            callback=test_texture_packer
        )
        
        texture_packer_path_input, _ = tp_picker.create_ui(
            textbox_label="TexturePacker.exe 路徑",
            button_text="📁 選擇目標",
            scale=(4, 1),
            value=config_manager.get_texture_packer_path()
        )
        
        # TinyPNG API 金鑰設定
        tinypng_api_key_input = gr.Textbox(
            label="TinyPNG API 金鑰（可選）",
            placeholder="輸入 TinyPNG API 金鑰以啟用進階 PNG 壓縮",
            info="可在 https://tinypng.com/developers 取得免費 API 金鑰，每月可壓縮 500 張圖片",
            max_lines=1,
            value=config_manager.get_tinypng_api_key()
        )
        
        with gr.Row():
            test_tp_btn = gr.Button("🔍 測試", scale=1)
            save_button = gr.Button("💾 儲存設定", scale=1)

        test_result = gr.Textbox(label="測試結果", interactive=False)
        save_output = gr.Textbox(label="設定狀態", interactive=False)

        # 進階設定
        with gr.Accordion("進階設定", open=False):
            default_fps = gr.Slider(1, 60, value=24, label="預設 FPS")
            default_max_size = gr.Slider(512, 8192, value=2048, step=512, label="預設材質大小")
            auto_clean = gr.Checkbox(label="自動清理暫存檔", value=True)

        # 使用者偏好
        with gr.Accordion("使用者偏好", open=False):
            theme = gr.Radio(
                choices=["light", "dark"],
                value="light",
                label="介面主題"
            )
            remember_settings = gr.Checkbox(
                label="記住上次使用的設定",
                value=True
            )

        def save_settings(ffmpeg_path, texture_packer_path, tinypng_api_key):
            """儲存設定"""
            try:
                if not ffmpeg_path:
                    raise ConfigError("請選擇 FFmpeg 執行檔")
                if not texture_packer_path:
                    raise ConfigError("請選擇 TexturePacker 執行檔")
                    
                return config_manager.save_config(ffmpeg_path, texture_packer_path, tinypng_api_key)
            except (ConfigError, Exception) as e:
                return handle_error(e, ui_component=True)

        # 綁定事件
        test_tp_btn.click(
            test_texture_packer,
            inputs=[texture_packer_path_input],
            outputs=[test_result]
        )

        save_button.click(
            save_settings,
            inputs=[
                ffmpeg_path_input,
                texture_packer_path_input,
                tinypng_api_key_input
            ],
            outputs=[save_output]
        )

        # 返回需要在其他地方使用的元件
        return {
            "theme": theme,
            "default_fps": default_fps,
            "default_max_size": default_max_size,
            "auto_clean": auto_clean,
            "remember_settings": remember_settings
        } 