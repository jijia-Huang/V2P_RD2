"""
檔案選擇器元件
"""
import os
import tkinter as tk
from tkinter import filedialog
import logging
import gradio as gr
from core.exceptions import FileError
from core.error_handler import handle_error

class TkFilePicker:
    """整合 tkinter 文件選擇器的 Gradio 元件"""
    
    def __init__(self, 
                 title="選擇檔案",
                 file_types=None,
                 initial_dir=None,
                 select_dir=False,
                 callback=None):
        """
        初始化文件選擇器
        
        Args:
            title (str): 選擇器視窗標題
            file_types (list): 檔案類型列表，例如 [("執行檔", "*.exe")]
            initial_dir (str): 初始目錄
            select_dir (bool): True 為選擇目錄，False 為選擇檔案
        """
        logging.debug(f"初始化檔案選擇器：title={title}, initial_dir={initial_dir}")
        self.title = title
        self.file_types = file_types or [("所有檔案", "*.*")]
        self.initial_dir = initial_dir
        self.select_dir = select_dir
        self.callback = callback
    
    def create_ui(self, textbox_label="檔案路徑", button_text="📁 瀏覽", scale=(4, 1), value=None):
        """
        建立 UI 元件
        
        Args:
            textbox_label (str): 文字框標籤
            button_text (str): 按鈕文字
            scale (tuple): 文字框和按鈕的寬度比例
            value (str): 初始值
            
        Returns:
            tuple: (文字框元件, 按鈕元件)
        """
        logging.debug(f"建立檔案選擇器 UI：label={textbox_label}, value={value}")
        
        try:
            with gr.Row():
                path_input = gr.Textbox(
                    label=textbox_label,
                    interactive=True,
                    scale=scale[0],
                    value=value
                )
                browse_btn = gr.Button(button_text, scale=scale[1])

            browse_btn.click(
                self.browse_file,
                outputs=[path_input]
            )
            
            return path_input, browse_btn
            
        except Exception as e:
            logging.error(f"建立檔案選擇器 UI 失敗：{str(e)}", exc_info=True)
            raise
    
    def browse_file(self):
        """開啟檔案選擇對話框"""
        try:
            logging.debug(f"開啟檔案選擇對話框：select_dir={self.select_dir}")
            root = tk.Tk()
            root.attributes("-topmost", True)
            root.withdraw()
            
            try:
                initial_dir = self.initial_dir
                logging.debug(f"初始目錄：{initial_dir}")
                
                if self.select_dir:
                    file_path = filedialog.askdirectory(
                        title=self.title,
                        initialdir=initial_dir
                    )
                else:
                    file_path = filedialog.askopenfilename(
                        title=self.title,
                        filetypes=self.file_types,
                        initialdir=initial_dir
                    )
                    
                if file_path:
                    normalized_path = file_path.replace("\\", "/")
                    logging.debug(f"選擇的檔案：{normalized_path}")

                    if self.callback and callable(self.callback):
                        self.callback(normalized_path)

                    return normalized_path
                    
                logging.debug("未選擇檔案")
                return None
                
            finally:
                root.destroy()
                
        except Exception as e:
            logging.error(f"檔案選擇失敗：{str(e)}", exc_info=True)
            raise FileError(
                "選擇檔案失敗",
                details=str(e)
            ) 