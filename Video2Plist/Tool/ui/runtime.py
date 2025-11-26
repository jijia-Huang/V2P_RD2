# -*- coding: utf-8 -*-
"""
UI 執行入口
"""
import logging

SUPPORTED_UI_MODES = ("gradio", "webview")


def create_ui_manager(ui_mode, config_manager):
    """
    根據模式建立對應的 UI 管理器
    """
    if ui_mode == "webview":
        from .webview import WebViewUIManager
        return WebViewUIManager(config_manager)
    from .manager import UIManager
    return UIManager(config_manager)


def launch_ui(ui_mode, config_manager, **kwargs):
    """
    啟動指定模式的 UI
    """
    ui_mode = ui_mode or "gradio"
    ui_mode = ui_mode.lower()

    if ui_mode not in SUPPORTED_UI_MODES:
        logging.warning(f"未知 UI 模式 {ui_mode}，將回退為 gradio")
        ui_mode = "gradio"

    manager = create_ui_manager(ui_mode, config_manager)

    if ui_mode == "webview":
        logging.info("使用 WebView 模式啟動 UI")
        port = kwargs.get('port', None)
        debug = kwargs.get('debug', False)
        manager.run(port=port, debug=debug)
        return None

    logging.info("使用 Gradio 模式啟動 UI")
    return manager.create_ui()

