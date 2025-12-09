"""Entrypoint for the V2P editor viewer."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 確保可以導入當前目錄的模組
# 在打包環境中，需要將父目錄添加到路徑，以便導入 v2p_editor 包
if getattr(sys, 'frozen', False):
    # PyInstaller 打包環境：將執行檔所在目錄添加到路徑
    if hasattr(sys, '_MEIPASS'):
        # 單檔案模式：資源在 _MEIPASS
        base_path = sys._MEIPASS
    else:
        # 單目錄模式：資源在執行檔目錄
        base_path = os.path.dirname(sys.executable)
    
    # 將 base_path 添加到 sys.path，確保可以導入 v2p_editor
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
    
    # 使用絕對導入
    from v2p_editor.webview_ui.manager import WebViewUIManager
elif __package__ in (None, ""):
    # 當作為腳本運行時（開發環境）
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    
    # 將父目錄添加到路徑，以便導入 v2p_editor 包
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # 使用絕對導入
    from v2p_editor.webview_ui.manager import WebViewUIManager
else:
    # 當作為包導入時
    from .webview_ui.manager import WebViewUIManager


def main() -> None:
    try:
        parser = argparse.ArgumentParser(description="啟動 V2P Viewer 進行檢查與預覽")
        parser.add_argument(
            "-i",
            "--input",
            type=str,
            help="預先載入的 V2P 輸出資料夾路徑",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="啟用 WebView 開發者工具（按 F12 打開）",
        )
        args = parser.parse_args()
        initial_path = Path(args.input).expanduser() if args.input else None
        
        manager = WebViewUIManager()
        manager.run(initial_path=str(initial_path) if initial_path else None, debug=args.debug)
    except Exception as e:
        import traceback
        error_msg = f"啟動失敗：{str(e)}"
        print(f"\n❌ {error_msg}")
        print("\n詳細錯誤訊息：")
        traceback.print_exc()
        input("\n按 Enter 鍵退出...")  # 暫停以便查看錯誤訊息
        raise


if __name__ == "__main__":
    main()

