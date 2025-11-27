# -*- coding: utf-8 -*-
"""
V2P 工具主程式
"""
import os
import argparse
import logging
from core.logger import setup_logger
from core.config import ConfigManager
from core.file_utils import get_application_path
from ui import launch_ui
from version import get_version, check_compatibility

def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='V2P 工具 - 影片轉換為 Cocos2d 動畫工具',
        epilog='範例：python v2p.py --log-level DEBUG'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'V2P 工具 {get_version()}',
        help='顯示版本資訊'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='設置日誌記錄級別（DEBUG=詳細、INFO=一般、WARNING=警告、ERROR=錯誤）'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='啟用 WebView 開發者工具（按 F12 打開）'
    )
    
    return parser.parse_args()

def main():
    """主程式"""
    try:
        # 相容性檢查
        is_compatible, message = check_compatibility()
        if not is_compatible:
            print(f"\n❌ {message}")
            print("請更新相關套件後再試\n")
            input("按 Enter 鍵退出...")  # 暫停以便查看錯誤訊息
            return
        
        # 解析命令列參數
        args = parse_args()
        
        # 設定日誌
        log_level = getattr(logging, args.log_level.upper())
        setup_logger(log_level)
        logging.info(f"V2P 工具 {get_version()} 啟動")
        
        # 設定工作目錄
        os.chdir(get_application_path())
        
        # 建立設定管理器
        config_manager = ConfigManager()
        
        # 啟動 WebView UI
        print(f"\n🖥️ 啟動 V2P 工具 {get_version()} - WebView 桌面介面")
        if args.debug:
            print("🔧 開發者工具已啟用：按 F12 或右鍵選擇「檢查」可打開開發者工具")
        launch_ui("webview", config_manager, debug=args.debug)
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
