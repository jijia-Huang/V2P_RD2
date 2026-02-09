# -*- coding: utf-8 -*-
"""
V2P 工具主程式
"""
import os
import argparse
import logging
from core.logger import setup_logger, get_log_path
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
    import traceback
    
    # 先設置基本日誌，確保錯誤能被記錄
    try:
        setup_logger(logging.INFO)
    except:
        pass  # 如果日誌設置失敗，繼續執行
    
    try:
        # 相容性檢查
        is_compatible, message = check_compatibility()
        if not is_compatible:
            error_msg = f"相容性檢查失敗：{message}"
            print(f"\n❌ {error_msg}")
            print("請更新相關套件後再試\n")
            logging.error(error_msg)
            input("按 Enter 鍵退出...")
            return
        
        # 解析命令列參數
        args = parse_args()
        
        # 設定日誌（重新設置，使用用戶指定的級別）
        log_level = getattr(logging, args.log_level.upper())
        setup_logger(log_level)
        logging.info(f"V2P 工具 {get_version()} 啟動")
        
        # 設定工作目錄
        app_path = get_application_path()
        logging.debug(f"應用程式路徑：{app_path}")
        os.chdir(app_path)
        
        # 建立設定管理器
        logging.info("初始化配置管理器...")
        config_manager = ConfigManager()
        logging.info("配置管理器初始化完成")
        
        # 啟動 WebView UI
        print(f"\n🖥️ 啟動 V2P 工具 {get_version()} - WebView 桌面介面")
        if args.debug:
            print("🔧 開發者工具已啟用：按 F12 或右鍵選擇「檢查」可打開開發者工具")
        
        logging.info("啟動 WebView UI...")
        launch_ui("webview", config_manager, debug=args.debug)
        
    except KeyboardInterrupt:
        logging.info("使用者中斷（Ctrl+C）")
        print("\n\n程式已中斷")
    except SystemExit:
        # 正常退出，不顯示錯誤
        pass
    except Exception as e:
        # 記錄完整錯誤訊息
        error_msg = f"啟動失敗：{str(e)}"
        error_traceback = traceback.format_exc()
        
        # 輸出到控制台
        print("\n" + "=" * 60)
        print("❌ 發生錯誤")
        print("=" * 60)
        print(f"\n錯誤訊息：{error_msg}")
        print("\n詳細錯誤訊息：")
        print(error_traceback)
        print("=" * 60)
        
        # 記錄到日誌文件
        try:
            logging.critical(f"程式啟動失敗：{error_msg}")
            logging.critical(f"錯誤堆疊：\n{error_traceback}")
            try:
                log_path = get_log_path()
                print(f"\n錯誤已記錄到日誌文件：{log_path}")
            except:
                # 如果無法獲取日誌路徑，嘗試從處理器獲取
                if logging.handlers:
                    for handler in logging.handlers:
                        if hasattr(handler, 'baseFilename'):
                            print(f"\n錯誤已記錄到日誌文件：{handler.baseFilename}")
                            break
        except Exception as log_error:
            print(f"\n無法記錄錯誤到日誌文件：{log_error}")
        
        # 暫停以便查看錯誤訊息
        print("\n按 Enter 鍵退出...")
        try:
            input()
        except:
            import time
            time.sleep(5)  # 如果無法輸入，等待 5 秒
        
        # 重新拋出異常以便調試
        raise

if __name__ == "__main__":
    main()
