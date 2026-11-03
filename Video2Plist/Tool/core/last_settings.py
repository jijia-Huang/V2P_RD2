# -*- coding: utf-8 -*-
"""
「上次轉換設定」的讀寫

GUI 與 CLI 每次轉換成功後都會寫回 preferences.json 的 last_* 欄位，
CLI 沒指定的參數就從這裡補，達成「照上次的設定再跑一次」。
"""

# 轉換參數名稱 -> (preferences 欄位, 預設值)
LAST_SETTINGS_FIELDS = {
    "video_path": ("last_video_path", ""),
    "output_name": ("last_output_name", ""),
    "fps": ("last_fps", 24),
    "max_width": ("last_max_width", 2048),
    "max_height": ("last_max_height", 2048),
    "output_format": ("last_format", "PNG"),
    "quality": ("last_quality", 5),
    "use_tinypng": ("last_use_tinypng", False),
    "packer_choice": ("last_packer_choice", "自動選擇"),
    "enable_resize": ("last_enable_resize", False),
    "target_width": ("last_frame_width", None),
    "target_height": ("last_frame_height", None),
    "resize_mode": ("last_resize_mode", "stretch"),
    "enable_bg_removal": ("last_bg_removal_enabled", False),
    "bg_removal_tolerance": ("last_bg_removal_tolerance", 10),
}

PACKER_CHOICES = ("自動選擇", "TexturePacker", "Python 打包器")
RESIZE_MODES = ("stretch", "crop", "pad_black", "pad_transparent")


def load_last_settings(config_manager):
    """讀取上次的轉換設定（缺的欄位用預設值補）"""
    settings = {}
    for key, (pref_key, default) in LAST_SETTINGS_FIELDS.items():
        value = config_manager.get_preference(pref_key, default)
        settings[key] = default if value is None and default is not None else value
    return settings


def save_last_settings(config_manager, settings):
    """把本次轉換參數寫回 preferences.json（只寫有對應欄位的鍵）"""
    prefs = {}
    for key, (pref_key, _default) in LAST_SETTINGS_FIELDS.items():
        if key in settings:
            prefs[pref_key] = settings[key]
    if prefs:
        config_manager.save_preferences(prefs)
