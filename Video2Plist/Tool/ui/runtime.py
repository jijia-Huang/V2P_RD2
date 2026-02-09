# -*- coding: utf-8 -*-
"""
UI 執行入口
"""
import logging

SUPPORTED_UI_MODES = ("webview",)


def create_ui_manager(ui_mode, config_manager):
    """
    根據模式建立對應的 UI 管理器
    """
    if ui_mode == "webview":
        from .webview import WebViewUIManager
        return WebViewUIManager(config_manager)
    
    # 預設使用 webview
    logging.warning(f"未知 UI 模式 {ui_mode}，將使用 webview")
    from .webview import WebViewUIManager
    return WebViewUIManager(config_manager)


def launch_ui(ui_mode, config_manager, **kwargs):
    """
    啟動指定模式的 UI
    """
    ui_mode = ui_mode or "webview"
    ui_mode = ui_mode.lower()

    if ui_mode not in SUPPORTED_UI_MODES:
        logging.warning(f"未知 UI 模式 {ui_mode}，將使用 webview")
        ui_mode = "webview"

    manager = create_ui_manager(ui_mode, config_manager)

    logging.info("使用 WebView 模式啟動 UI")
    port = kwargs.get('port', None)
    debug = kwargs.get('debug', False)
    manager.run(port=port, debug=debug)
    return None

