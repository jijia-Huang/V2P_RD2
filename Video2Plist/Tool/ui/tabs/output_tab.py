"""
輸出記錄頁面
"""
import os
import json
import gradio as gr
from core.file_utils import get_videos_dir
import logging
from core.error_handler import handle_error
from core.exceptions import FileError

def get_animation_list():
    """獲取所有已輸出的動畫列表"""
    videos_dir = get_videos_dir()
    animations = []
    
    if not os.path.exists(videos_dir):
        return []
    
    # 收集所有動畫及其建立時間
    for subfolder in os.listdir(videos_dir):
        subfolder_path = os.path.join(videos_dir, subfolder)
        if not os.path.isdir(subfolder_path):
            continue
            
        # 尋找所有 metadata 檔案
        for file in os.listdir(subfolder_path):
            if file.endswith("_metadata.json"):
                file_path = os.path.join(subfolder_path, file)
                base_name = file.replace("_metadata.json", "")
                # 獲取檔案建立時間
                created_time = os.path.getctime(file_path)
                animations.append((base_name, base_name, created_time))
    
    # 按建立時間降序排序（最新的在前面）
    animations.sort(key=lambda x: x[2], reverse=True)
    
    # 移除時間戳記，只返回顯示名稱和值
    return [(name, value) for name, value, _ in animations]

def create_output_tab(config_manager):
    """建立輸出記錄頁籤"""
    logging.debug("開始建立輸出記錄頁籤")
    
    try:
        with gr.Tab("輸出記錄", id=2) as tab:
            with gr.Row():
                # 左側：列表和操作區
                with gr.Column(scale=1):
                    output_selector = gr.Dropdown(
                        label="選擇要操作的動畫",
                        choices=get_animation_list(),
                        interactive=True
                    )
                    
                    with gr.Row():
                        refresh_btn = gr.Button("🔄 重新整理")
                        preview_btn = gr.Button("👁️ 預覽", variant="primary")
                        export_btn = gr.Button("📦 匯出")
                    
                    # 匯出結果顯示
                    export_result = gr.File(
                        label="匯出結果",
                        visible=False,
                        interactive=True,
                        type="filepath"
                    )
                
                # 右側：詳細資訊區
                with gr.Column(scale=1):
                    # 基本資訊顯示
                    info_box = gr.Markdown()

                    plist_info = gr.Markdown(label="PLIST 檔案")
                    metadata_info = gr.JSON(label="動畫資訊")

                with gr.Column(scale=2):
                    
                    # 預覽區域（預設隱藏）
                    preview_area = gr.Row(visible=False)
                    with preview_area:
                        preview_image = gr.Gallery(
                            label="材質圖預覽",
                            show_label=True,
                            elem_id="preview_gallery",
                            columns=2,
                            # height=620,
                            show_download_button=False,
                            show_share_button=False,
                        )

            # 頁面選中時更新列表和詳細資訊
            def update_list_and_info(current_value):
                new_choices = get_animation_list()
                
                # 決定要顯示的值
                if current_value and current_value in [choice[1] for choice in new_choices]:
                    selected_value = current_value
                elif new_choices:
                    selected_value = new_choices[0][1]
                else:
                    selected_value = None
                
                # 獲取詳細資訊
                info, preview_visible, images, plist_content, metadata = get_animation_info(selected_value)
                
                return [
                    gr.update(choices=new_choices, value=selected_value),  # 更新下拉選單
                    info,                   # 更新基本資訊
                    preview_visible,        # 更新預覽區域可見性
                    images,                 # 更新預覽圖片
                    plist_content,          # 更新 PLIST 內容
                    metadata               # 更新 metadata
                ]

            tab.select(
                update_list_and_info,
                inputs=[output_selector],
                outputs=[
                    output_selector,
                    info_box,
                    preview_area,
                    preview_image,
                    plist_info,
                    metadata_info
                ]
            )

            # 綁定事件
            refresh_btn.click(
                refresh_list,
                outputs=[output_selector]
            )

            # 當選擇器值改變時更新資訊
            output_selector.change(
                get_animation_info,
                inputs=[output_selector],
                outputs=[
                    info_box,
                    preview_area,
                    preview_image,
                    plist_info,
                    metadata_info
                ]
            )

            preview_btn.click(
                preview_animation,
                inputs=[output_selector],
                outputs=[
                    preview_area,
                    preview_image,
                    plist_info,
                    metadata_info
                ]
            )

            export_btn.click(
                export_animation,
                inputs=[output_selector],
                outputs=[export_result]
            )

        logging.debug("輸出記錄頁籤建立完成")
        return {
            "output_selector": output_selector,
            "info_box": info_box,
            "preview_area": preview_area,
            "preview_image": preview_image,
            "plist_info": plist_info,
            "metadata_info": metadata_info
        }
        
    except Exception as e:
        logging.error(f"建立輸出記錄頁籤失敗：{str(e)}", exc_info=True)
        raise

def refresh_list():
    """重新整理動畫列表"""
    return gr.update(choices=get_animation_list())

def get_animation_info(selected):
    """獲取動畫詳細資訊"""
    if not selected:
        return "選擇一個動畫來查看詳細資訊", gr.update(visible=False), None, "", {}
    
    try:
        # 讀取 metadata
        metadata_path = os.path.join(get_videos_dir(), selected, f"{selected}_metadata.json")
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # 格式化資訊
        info = f"""### 🎬 {selected}

#### 📁 基本資訊
- 影格數量：{metadata.get('frame_count', '未知')}
- 材質數量：{metadata.get('plist_count', '未知')}

#### ⚙️ 設定
- FPS：{metadata.get('fps', '未知')}
- 材質大小限制：{metadata.get('max_width', '未知')}x{metadata.get('max_height', '未知')}
- 輸出格式：{metadata.get('output_format', 'PNG')}
- 輸出品質：{metadata.get('quality', '5')}

#### 📌 其他資訊
- 建立時間：{metadata.get('creation_time', '未知')}
- 工具版本：{metadata.get('tool_version', '未知')}
"""
        return info, gr.update(visible=False), None, "", metadata
        
    except Exception as e:
        return f"讀取資訊失敗：{str(e)}", gr.update(visible=False), None, "", {}

def preview_animation(selected):
    """預覽動畫"""
    if not selected:
        return gr.update(visible=False), None, "", {}
    
    try:
        base_path = os.path.join(get_videos_dir(), selected)
        
        # 讀取 metadata 以獲取輸出格式
        metadata_path = os.path.join(base_path, f"{selected}_metadata.json")
        metadata = {}
        output_format = "PNG"  # 預設格式
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                output_format = metadata.get("output_format", "PNG")
        
        # 讀取所有圖片檔案
        images = []
        for i in range(100):  # 最多預覽100個檔案
            image_path = os.path.join(base_path, f"{selected}_{i}.{output_format.lower()}")
            if os.path.exists(image_path):
                images.append(image_path)
            else:
                break
        
        return (
            gr.update(visible=True),
            images,
            "",  # 不顯示 PLIST 內容
            metadata
        )
        
    except Exception as e:
        return gr.update(visible=False), None, f"預覽失敗：{str(e)}", {}

def export_animation(selected):
    """匯出動畫"""
    if not selected:
        return gr.update(visible=False)
    
    try:
        base_path = os.path.join(get_videos_dir(), selected)
        
        # 讀取 metadata 以獲取輸出格式
        metadata_path = os.path.join(base_path, f"{selected}_metadata.json")
        metadata = {}
        output_format = "PNG"  # 預設格式
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                output_format = metadata.get("output_format", "PNG")
        
        # 建立臨時壓縮檔
        import tempfile
        import zipfile
        
        temp_dir = tempfile.gettempdir()
        zip_path = os.path.join(temp_dir, f"{selected}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加所有相關檔案
            for file in os.listdir(base_path):
                if file.startswith(selected) and (
                    file.endswith(f".{output_format.lower()}") or 
                    file.endswith(".plist") or 
                    file.endswith("_metadata.json")
                ):
                    file_path = os.path.join(base_path, file)
                    zipf.write(file_path, file)
        
        return gr.update(value=zip_path, visible=True)
        
    except Exception as e:
        logging.error(f"匯出失敗：{str(e)}")
        return gr.update(visible=False)

def load_metadata(subfolder, name):
    """載入 metadata 檔案"""
    try:
        logging.debug(f"嘗試載入 metadata：子資料夾={subfolder}, 名稱={name}")
        
        if not subfolder or not name:
            logging.warning("子資料夾或名稱為空")
            return None
            
        metadata_path = os.path.join(get_videos_dir(), subfolder, f"{name}_metadata.json")
        if not os.path.exists(metadata_path):
            logging.warning(f"找不到 metadata 檔案：{metadata_path}")
            return None
            
        logging.debug(f"讀取 metadata 檔案：{metadata_path}")
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        logging.debug(f"metadata 內容：{metadata}")
        return metadata
        
    except Exception as e:
        logging.error(f"載入 metadata 失敗：{str(e)}", exc_info=True)
        return None 