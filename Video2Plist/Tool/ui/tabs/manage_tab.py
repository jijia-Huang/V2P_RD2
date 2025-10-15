"""
管理頁面
"""
import os
import glob
import logging
import json
from datetime import datetime
import gradio as gr
from core.file_utils import get_application_path, get_videos_dir
from core.error_handler import handle_error
from core.exceptions import FileError

def get_available_logs():
    """獲取可用的日誌檔案列表"""
    try:
        log_dir = os.path.join("log")
        if not os.path.exists(log_dir):
            return []
        
        log_files = []
        for file in os.listdir(log_dir):
            if file.startswith("v2p_") and file.endswith(".log"):
                # 從檔名解析日期
                date_str = file[4:-4]  # 移除 "v2p_" 和 ".log"
                try:
                    date = datetime.strptime(date_str, '%Y%m%d')
                    log_files.append(date.strftime('%Y-%m-%d'))
                except ValueError:
                    continue
        
        return sorted(log_files, reverse=True)
    except Exception as e:
        logging.error(f"讀取日誌檔案列表失敗：{str(e)}")
        return []

def read_log_file(date_str):
    """讀取日誌檔案內容"""
    try:
        if not date_str:
            raise FileError("未選擇日期")
            
        # 轉換日期格式
        date = datetime.strptime(date_str, '%Y-%m-%d')
        log_path = os.path.join("log", f"v2p_{date.strftime('%Y%m%d')}.log")
        
        if not os.path.exists(log_path):
            raise FileError(
                "找不到日誌檔案",
                details=f"路徑：{log_path}"
            )
        
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            raise FileError(
                "日誌檔案編碼錯誤",
                details="請確認檔案是否使用 UTF-8 編碼"
            )
            
    except FileError:
        raise
    except Exception as e:
        raise FileError(
            "讀取日誌失敗",
            details=str(e)
        )

def create_manage_tab(config_manager):
    """建立管理頁籤"""
    with gr.Tab("管理", id=3):
        # 輸出管理
        gr.Markdown("### 🗑️ 輸出管理")
        
        with gr.Row():
            cleanup_days = gr.Slider(1, 90, value=30, label="清理超過幾天的檔案")
            cleanup_btn = gr.Button("清理舊檔案")
        
        with gr.Row():
            analyze_btn = gr.Button("分析磁碟使用")
            open_folder_btn = gr.Button("開啟輸出資料夾")
        
        manage_output = gr.Markdown("點擊上方按鈕執行相關操作")

        # 日誌查看
        gr.Markdown("### 📝 操作日誌")
        
        with gr.Row():
            log_dropdown = gr.Dropdown(
                label="選擇日誌檔案",
                choices=get_available_logs(),
                value=datetime.now().strftime('%Y-%m-%d'),
                interactive=True
            )
            view_log_btn = gr.Button("查看日誌")
        
        log_display = gr.TextArea(
            label="日誌內容",
            interactive=False,
            lines=25,
            elem_classes=["log-display"],
            elem_id="log_display"  # 添加唯一 ID
        )

        def get_log_path(date_str=None):
            """統一獲取日誌檔案路徑"""
            if date_str is None:
                date_str = datetime.now().strftime('%Y%m%d')
            else:
                # 轉換日期格式
                date = datetime.strptime(date_str, '%Y-%m-%d')
                date_str = date.strftime('%Y%m%d')
            return os.path.join(get_application_path(), "log", f"v2p_{date_str}.log")

        def update_log_display(selected_date):
            """讀取並顯示日誌內容"""
            try:
                if not selected_date:
                    return "請選擇日期"
                
                return read_log_file(selected_date)
                
            except FileError as e:
                return handle_error(e, ui_component=True)
            except Exception as e:
                logging.error(f"讀取日誌時發生錯誤：{str(e)}")
                return handle_error(e, ui_component=True)

        def view_log(date_str):
            """查看日誌"""
            try:
                return read_log_file(date_str)
            except (FileError, Exception) as e:
                return handle_error(e, ui_component=True)

        def analyze_disk_usage():
            """分析輸出目錄的磁碟使用情況"""
            try:
                videos_dir = get_videos_dir()
                if not os.path.exists(videos_dir):
                    raise FileError(
                        "輸出目錄不存在",
                        details=f"路徑：{videos_dir}"
                    )
                
                total_size = 0
                subfolder_sizes = {}
                
                for subfolder in os.listdir(videos_dir):
                    subfolder_path = os.path.join(videos_dir, subfolder)
                    if not os.path.isdir(subfolder_path):
                        continue
                        
                    size = 0
                    for dirpath, _, filenames in os.walk(subfolder_path):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            size += os.path.getsize(fp)
                    
                    subfolder_sizes[subfolder] = size
                    total_size += size
                
                # 格式化輸出
                lines = ["### 📊 磁碟使用分析"]
                lines.append(f"- 總使用空間：{total_size / 1024 / 1024:.2f} MB")
                lines.append("\n#### 子資料夾使用情況：")
                for folder, size in sorted(subfolder_sizes.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"- {folder}: {size / 1024 / 1024:.2f} MB")
                
                return "\n".join(lines)
            
            except FileError:
                raise
            except Exception as e:
                raise FileError(
                    "分析磁碟使用失敗",
                    details=str(e)
                )

        # 綁定事件
        cleanup_btn.click(
            fn=lambda days: config_manager.cleanup_old_files(days),
            inputs=[cleanup_days],
            outputs=[manage_output]
        )

        view_log_btn.click(
            fn=view_log,
            inputs=[log_dropdown],
            outputs=[log_display]
        )

        analyze_btn.click(
            fn=lambda: analyze_disk_usage(),
            outputs=[manage_output]
        )

        open_folder_btn.click(
            fn=lambda: config_manager.open_output_folder(),
            outputs=[manage_output]
        )

        # 返回需要在其他地方使用的元件
        return {
            "manage_output": manage_output,
            "log_display": log_display
        } 