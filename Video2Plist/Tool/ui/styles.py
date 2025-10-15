"""
UI 樣式定義
"""
import os
import logging
from core.file_utils import get_application_path

def load_styles():
    """載入 UI 樣式"""
    try:
        logging.debug("開始載入 UI 樣式")
        
        # 基礎樣式
        styles = [
            """
            /* 全局樣式 */
            .gradio-container {
                max-width: 1200px !important;
            }
            
            /* 日誌顯示區域 */
            .log-display textarea {
                font-family: monospace;
                font-size: 12px;
                line-height: 1.4;
            }
            
            /* 結果顯示區域 */
            .result-display {
                min-height: 100px;
                padding: 2px;
                border-radius: 2px;
                background-color: #f5f5f5;
            }
            """
        ]
        
        # 載入自定義樣式檔案
        custom_css_path = os.path.join(get_application_path(), "custom.css")
        if os.path.exists(custom_css_path):
            logging.debug(f"載入自定義樣式：{custom_css_path}")
            try:
                with open(custom_css_path, "r", encoding="utf-8") as f:
                    styles.append(f.read())
            except Exception as e:
                logging.warning(f"載入自定義樣式失敗：{str(e)}")
        
        css = "\n".join(styles)
        logging.debug("UI 樣式載入完成")
        return css
        
    except Exception as e:
        logging.error(f"載入 UI 樣式失敗：{str(e)}", exc_info=True)
        # 返回基本樣式
        return """
        .gradio-container {
            max-width: 1200px !important;
        }
        """

# 預設樣式定義
CSS = load_styles()

CSS = """
.success-message {
    background: #e6ffe6;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #4CAF50;
    color: #000;
    margin: 15px 0;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.success-message-dark {
    background: #1a2e1a;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #4CAF50;
    color: #e0e0e0;
    margin: 15px 0;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.error-message {
    background: #ffe6e6;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #f44336;
    color: #000;
    margin: 15px 0;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error-message-dark {
    background: #2b0f0f;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #f44336;
    color: #e0e0e0;
    margin: 15px 0;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.progress-container {
    margin: 20px 0;
    padding: 15px;
    border-radius: 8px;
}

.dark .progress-container {
    background: rgba(0, 0, 0, 0.3);
}

.dark .result-display {
    background: rgba(0, 0, 0, 0.3);
    color: #e0e0e0;
}

.result-display {
    min-height: 60px;
    margin: 2px 0;
    padding: 2px;
    border-radius: 2px;
}

/* 等寬字體設置 */
.monospace-text {
    font-family: "IBM Plex Mono", Consolas, "Courier New", monospace !important;
    font-size: 14px !important;
    line-height: 1.5 !important;
}

/* TextArea 樣式 */
.monospace-text > label > textarea {
    min-height: 400px !important;
    overflow-y: scroll !important;
    white-space: pre !important;
    padding: 8px !important;
}

/* 滾動條樣式 */
.monospace-text > label > textarea::-webkit-scrollbar {
    width: 8px !important;
}

.monospace-text > label > textarea::-webkit-scrollbar-track {
    background: #f1f1f1 !important;
}

.monospace-text > label > textarea::-webkit-scrollbar-thumb {
    background: #888 !important;
    border-radius: 4px !important;
}

.monospace-text > label > textarea::-webkit-scrollbar-thumb:hover {
    background: #555 !important;
}

/* 日誌顯示樣式 */
#log_display {
    font-family: "IBM Plex Mono", Consolas, "Courier New", monospace !important;
    font-size: 14px !important;
    line-height: 1.5 !important;
}

#log_display textarea {
    min-height: 400px !important;
    overflow-y: auto !important;
    white-space: pre !important;
    padding: 8px !important;
}
""" 