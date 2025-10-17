"""
頁面模組
"""
from .settings_tab import create_settings_tab
from .main_tab import create_main_tab
from .bg_removal_tab import create_bg_removal_tab
from .output_tab import create_output_tab
from .manage_tab import create_manage_tab

__all__ = [
    'create_settings_tab',
    'create_main_tab',
    'create_bg_removal_tab',
    'create_output_tab',
    'create_manage_tab'
] 