# -*- coding: utf-8 -*-
"""
UI 管理模組
"""
import os
import logging
import gradio as gr
from .styles import CSS, load_styles
from .tabs import (
    create_settings_tab,
    create_main_tab,
    create_output_tab,
    create_manage_tab
)
from version import VERSION_STRING

class UIManager:
    """UI 管理器"""
    
    def __init__(self, config_manager):
        """初始化 UI 管理器"""
        logging.info("初始化 UI 管理器")
        self.config_manager = config_manager
        self.config_manager.ui_manager = self
        self.components = {}
    
    def create_ui(self):
        """建立使用者介面"""
        logging.info("開始建立使用者介面")
        
        try:
            with gr.Blocks(
                css=CSS,
                theme=gr.themes.Soft(),  # 改回 Soft 主題
                title=f"V2P工具 {VERSION_STRING}"
            ) as demo:
                gr.Markdown(f"# 🎬 V2P 工具 {VERSION_STRING}")
                
                with gr.Tabs() as tabs:  # 獲取 tabs 引用
                    # 建立頁籤
                    logging.debug("建立設定頁籤")
                    settings_components = create_settings_tab(self.config_manager)
                    
                    logging.debug("建立主要功能頁籤")
                    main_components = create_main_tab(self.config_manager)
                    
                    logging.debug("建立輸出頁籤")
                    output_components = create_output_tab(self.config_manager)
                    
                    logging.debug("建立管理頁籤")
                    manage_components = create_manage_tab(self.config_manager)
                
                # 儲存元件引用
                self.components.update(settings_components)
                self.components.update(main_components)
                self.components.update(output_components)
                self.components.update(manage_components)
                
                # 頁面載入時的處理
                # 注意：由於縮放相關元件在 main_tab 中，這裡不需要額外載入
                # 偏好設定已在各元件初始化時從 config_manager 讀取
                demo.load(
                    fn=self._on_page_load,
                    outputs=[
                        self.components["theme"],
                        self.components["default_fps"],
                        self.components["default_max_size"],
                        self.components["auto_clean"],
                        self.components["remember_settings"]
                    ]
                )
                
                # 檢查設定並自動切換頁面
                def check_and_switch():
                    if (self.config_manager.get_ffmpeg_path() and 
                        self.config_manager.get_texture_packer_path()):
                        return gr.update(selected=1)  # 切換到「轉換」頁面（index=1）
                    return gr.update()
                
                demo.load(
                    fn=check_and_switch,
                    outputs=[tabs]
                )
            
            logging.info("使用者介面建立完成")
            return demo
            
        except Exception as e:
            logging.error(f"建立使用者介面失敗：{str(e)}", exc_info=True)
            raise
    
    def _on_page_load(self):
        """
        頁面載入時的處理
        
        返回：
        - list: 包含以下元素：
            - theme: 主題設定
            - default_fps: 預設 FPS
            - default_max_size: 預設材質大小
            - auto_clean: 自動清理設定
            - remember_settings: 記住設定
        """
        # 載入使用者偏好設定
        prefs = self.config_manager.preferences
        
        return [
            prefs.get("theme", "light"),
            prefs.get("default_fps", 24),
            prefs.get("default_max_size", 2048),
            prefs.get("auto_clean", True),
            prefs.get("remember_settings", True)
        ]
    
    def get_component(self, name):
        """獲取 UI 元件"""
        try:
            return self.components.get(name)
        except Exception as e:
            logging.error(f"獲取 UI 元件失敗 [{name}]：{str(e)}")
            return None
    
    def update_component(self, name, value):
        """更新 UI 元件值"""
        try:
            component = self.get_component(name)
            if component:
                logging.debug(f"更新 UI 元件 [{name}]：{value}")
                component.update(value=value)
        except Exception as e:
            logging.error(f"更新 UI 元件失敗 [{name}]：{str(e)}") 