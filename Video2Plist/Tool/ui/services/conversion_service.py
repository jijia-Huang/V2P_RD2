# -*- coding: utf-8 -*-
"""
轉換流程服務
"""
import logging

from core.video import process_video
from core.error_handler import handle_error
from core.exceptions import ConfigError, FileError, ConversionError


class ConversionService:
    """封裝轉換流程，提供給不同 UI 重複使用"""

    def __init__(self, config_manager):
        self.config_manager = config_manager

    def convert(self,
                *,
                video,
                fps,
                output_name,
                max_width,
                max_height,
                output_format,
                quality,
                use_tinypng=False,
                packer_choice="自動選擇",
                enable_resize=False,
                target_width=None,
                target_height=None,
                resize_mode="stretch",
                enable_bg_removal=False,
                bg_removal_tolerance=10,
                tinypng_api_key=None,
                ffmpeg_path=None,
                texture_packer_path=None,
                progress=None,
                raise_exception=False):
        """
        執行影片轉換
        """
        ffmpeg_path = ffmpeg_path or self.config_manager.get_ffmpeg_path()
        texture_packer_path = texture_packer_path or self.config_manager.get_texture_packer_path()
        effective_tinypng = tinypng_api_key or self.config_manager.get_tinypng_api_key()

        try:
            return process_video(
                video,
                fps,
                output_name,
                max_width,
                max_height,
                ffmpeg_path,
                texture_packer_path,
                output_format,
                quality,
                use_tinypng=use_tinypng,
                tinypng_api_key=effective_tinypng,
                packer_choice=packer_choice,
                enable_resize=enable_resize,
                target_width=target_width,
                target_height=target_height,
                resize_mode=resize_mode,
                enable_bg_removal=enable_bg_removal,
                bg_removal_tolerance=bg_removal_tolerance,
                config_manager=self.config_manager,
                progress=progress
            )
        except (ConfigError, FileError, ConversionError) as error:
            logging.error(f"轉換失敗：{error}")
            if raise_exception:
                raise
            return handle_error(error, ui_component=True)
        except Exception as error:
            logging.exception("轉換流程發生未預期錯誤")
            if raise_exception:
                raise
            return handle_error(error, ui_component=True)

