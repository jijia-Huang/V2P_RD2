# -*- coding: utf-8 -*-
"""
V2P 打包腳本：執行 PyInstaller 後將 ffmpeg 目錄複製到 dist，供預設路徑 ffmpeg/ffmpeg.exe 使用。
在 Tool 目錄下執行：python build_v2p.py
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    tool_dir = Path(__file__).resolve().parent
    os.chdir(tool_dir)
    ffmpeg_src = tool_dir / "ffmpeg"
    if not ffmpeg_src.is_dir() or not (ffmpeg_src / "ffmpeg.exe").exists():
        print("錯誤：找不到 Tool/ffmpeg/ffmpeg.exe，請確認 ffmpeg 目錄存在。")
        sys.exit(1)
    # 1. 執行 PyInstaller
    ret = subprocess.run(
        [sys.executable, "-m", "PyInstaller.__main__", "v2p.spec"],
        cwd=tool_dir,
    )
    if ret.returncode != 0:
        sys.exit(ret.returncode)
    # 2. 複製 ffmpeg 到 dist
    dist_dir = tool_dir / "dist"
    ffmpeg_dst = dist_dir / "ffmpeg"
    if ffmpeg_dst.exists():
        shutil.rmtree(ffmpeg_dst)
    shutil.copytree(ffmpeg_src, ffmpeg_dst)
    print(f"已複製 ffmpeg 至 {ffmpeg_dst}")

if __name__ == "__main__":
    main()
