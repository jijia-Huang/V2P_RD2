# -*- coding: utf-8 -*-
"""
V2P 工具主程式
"""
import os
import argparse
import socket
import logging
import gradio as gr

from core.logger import setup_logger
from core.config import ConfigManager
from core.file_utils import get_application_path
from ui import UIManager
from version import get_version, check_compatibility

def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='V2P 工具 - 影片轉換為 Cocos2d 動畫工具',
        epilog='範例：python v2p.py --log-level DEBUG --port 8000'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'V2P 工具 {get_version()}',
        help='顯示版本資訊'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=7866,
        help='指定服務埠號（預設：7866）'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='啟動後不自動開啟瀏覽器'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='設置日誌記錄級別（DEBUG=詳細、INFO=一般、WARNING=警告、ERROR=錯誤）'
    )
    
    return parser.parse_args()

def find_available_port(start_port, max_tries=100):
    """尋找可用的 port"""
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise OSError(f"無法在 {start_port} 到 {start_port + max_tries - 1} 範圍內找到可用的 port")

def main():
    """主程式"""
    try:
        # 相容性檢查
        is_compatible, message = check_compatibility()
        if not is_compatible:
            print(f"\n❌ {message}")
            print("請更新相關套件後再試\n")
            input("按 Enter 鍵結束...")
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
        
        # 建立 UI 管理器
        ui_manager = UIManager(config_manager)
        
        # 建立並啟動 UI
        demo = ui_manager.create_ui()
        
        # 尋找可用的端口
        try:
            # 檢查指定端口是否可用
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                test_socket.bind(('127.0.0.1', args.port))
                test_socket.close()
                # 端口可用
                actual_port = args.port
                logging.info(f"使用端口: {actual_port}")
            except OSError:
                # 端口已被佔用，尋找可用端口
                test_socket.close()
                logging.warning(f"端口 {args.port} 已被佔用，正在尋找可用端口...")
                actual_port = find_available_port(args.port)
                logging.info(f"找到可用端口: {actual_port}")
        except Exception as e:
            # 如果檢查失敗，嘗試尋找可用端口
            logging.warning(f"無法檢查端口 {args.port}，正在尋找可用端口: {str(e)}")
            actual_port = find_available_port(args.port)
            logging.info(f"找到可用端口: {actual_port}")
        
        # 啟動提示
        print(f"\n🚀 啟動 V2P 工具 {get_version()}...")
        print(f"📱 網頁介面: http://127.0.0.1:{actual_port}")
        print("💡 提示：")
        print("   - 如果瀏覽器沒有自動開啟，請手動複製上方網址")
        print("   - 請確認是否有已經開啟的工具瀏覽器頁面，如有請關閉舊有頁面\n")
        
        # 啟動 Gradio
        demo.launch(
            server_name="127.0.0.1",
            server_port=actual_port,
            inbrowser=not args.no_browser,
            share=True
        )
    except KeyboardInterrupt:
        print("\n\n程式被使用者中斷")
        input("按 Enter 鍵結束...")
    except Exception as e:
        print(f"\n\n❌ 程式執行時發生錯誤：")
        print(f"錯誤類型：{type(e).__name__}")
        print(f"錯誤訊息：{str(e)}")
        print("\n詳細錯誤資訊：")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("請將上述錯誤訊息複製下來，以便進行問題排查")
        input("\n按 Enter 鍵結束...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ 發生未預期的錯誤：")
        print(f"錯誤類型：{type(e).__name__}")
        print(f"錯誤訊息：{str(e)}")
        print("\n詳細錯誤資訊：")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("請將上述錯誤訊息複製下來，以便進行問題排查")
        input("\n按 Enter 鍵結束...")
