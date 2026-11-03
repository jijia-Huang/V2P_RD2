# -*- coding: utf-8 -*-
"""
V2P 命令列介面（給人與 AI 使用）

所有子命令都在 stdout 輸出一個 JSON 物件，日誌與進度一律走 stderr。
結束碼：0=成功、1=執行失敗、2=參數錯誤。

    python v2p.py settings                     # 看「上次的設定」
    python v2p.py convert                      # 完全照上次設定重跑
    python v2p.py convert -i a.mp4 --tolerance 12
    python v2p.py check videos/v2p_xxx         # 檢查去背品質 + 產生對照圖
    python v2p.py bg-sweep --tolerances 4,8,12,16
    python v2p.py inspect videos/v2p_xxx
    python v2p.py info a.mp4
"""
import argparse
import glob
import hashlib
import json
import logging
import os
import shutil
import sys

COMMANDS = ("settings", "convert", "check", "bg-sweep", "inspect", "info")

PACKER_ALIASES = {
    "auto": "自動選擇",
    "python": "Python 打包器",
    "texturepacker": "TexturePacker",
}


class CliError(Exception):
    """參數或環境錯誤（結束碼 2）"""


# --------------------------------------------------------------------------- #
# 共用工具
# --------------------------------------------------------------------------- #

def _setup_io(verbose):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    from core.logger import setup_logger
    if not verbose:
        logging.disable(logging.INFO)  # 不顯示 setup_logger 自己的啟動訊息
    setup_logger(logging.DEBUG if verbose else logging.INFO)
    logging.disable(logging.NOTSET)
    # 檔案日誌保留完整 INFO；主控台（stderr）只顯示警告以上，避免洗版
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(logging.DEBUG if verbose else logging.WARNING)


def _emit(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.flush()


def _progress(value, desc=""):
    sys.stderr.write(f"[progress] {value:.0%} {desc}\n")
    sys.stderr.flush()


def _parse_size(text, name):
    try:
        w, h = text.lower().split("x")
        w, h = int(w), int(h)
        if w < 1 or h < 1:
            raise ValueError
        return w, h
    except Exception:
        raise CliError(f"{name} 格式錯誤：{text}（應為 寬x高，例如 1024x1024）")


def _config_manager():
    from core.config import ConfigManager
    return ConfigManager()


def _resolve_ffmpeg(cm, override=None):
    candidates = [override, cm.get_ffmpeg_path(), shutil.which("ffmpeg")]
    for path in candidates:
        if path and os.path.exists(path):
            return os.path.abspath(path)
    raise CliError("找不到 FFmpeg：請用 --ffmpeg 指定，或把 ffmpeg 放到工具目錄 ffmpeg/ffmpeg.exe / PATH")


def _check_dir(output_name):
    from core.file_utils import get_application_path
    return os.path.join(get_application_path(), "bgcheck", output_name)


def _default_name(video_path):
    stem = os.path.splitext(os.path.basename(video_path))[0]
    return stem[4:] if stem.startswith("v2p_") else stem


def _resolve_convert_settings(args, cm):
    """上次設定 → 被命令列參數覆蓋"""
    from core.last_settings import load_last_settings, RESIZE_MODES

    last = load_last_settings(cm)
    s = dict(last)

    if args.input:
        video = os.path.abspath(args.input)
        s["video_path"] = video
        if not args.name and os.path.normcase(video) != os.path.normcase(os.path.abspath(last["video_path"] or ".")):
            s["output_name"] = _default_name(video)
    if args.name:
        s["output_name"] = args.name
    if not s["video_path"]:
        raise CliError("沒有指定影片，且沒有上次使用的影片紀錄：請加 -i <影片路徑>")
    if not os.path.exists(s["video_path"]):
        raise CliError(f"影片不存在：{s['video_path']}")
    if not s["output_name"]:
        s["output_name"] = _default_name(s["video_path"])

    if args.fps is not None:
        s["fps"] = args.fps
    if args.max:
        s["max_width"], s["max_height"] = _parse_size(args.max, "--max")
    if args.format:
        s["output_format"] = args.format.upper()
    if args.quality is not None:
        s["quality"] = args.quality
    if args.packer:
        s["packer_choice"] = PACKER_ALIASES[args.packer]
    if args.tinypng is not None:
        s["use_tinypng"] = args.tinypng
    if args.resize:
        if args.resize.lower() == "off":
            s["enable_resize"] = False
        else:
            s["enable_resize"] = True
            s["target_width"], s["target_height"] = _parse_size(args.resize, "--resize")
    if args.resize_mode:
        s["resize_mode"] = args.resize_mode
    if args.bg is not None:
        s["enable_bg_removal"] = args.bg
    if args.tolerance is not None:
        if not 0 <= args.tolerance <= 255:
            raise CliError("--tolerance 必須在 0~255 之間（GUI 範圍 0~50）")
        s["bg_removal_tolerance"] = args.tolerance
        s["enable_bg_removal"] = True if args.bg is None else s["enable_bg_removal"]

    if s["enable_resize"] and not (s["target_width"] and s["target_height"]):
        raise CliError("啟用了縮放但沒有目標尺寸：請加 --resize 寬x高 或 --resize off")
    if s["resize_mode"] not in RESIZE_MODES:
        raise CliError(f"不支援的縮放模式：{s['resize_mode']}")
    return s


def _load_output_frames(folder):
    """用 V2P Editor 的 inspector 從 plist + 材質集切回每一格"""
    from v2p_editor.inspector import ProjectInspector
    report = ProjectInspector().inspect(folder)
    frames = [(f.index, f.name, f.image) for f in report.frames]
    return report, frames


def _run_check(folder, tolerance=None, sheet_path=None, full=False):
    from core.bg_check import analyze_frames, render_contact_sheet, strip_frame_details

    inspection, frames = _load_output_frames(folder)
    if inspection.errors:
        raise CliError("輸出資料夾不完整：" + "；".join(inspection.errors))
    if tolerance is None:
        tolerance = inspection.metadata.get("bg_removal_tolerance")
    report = analyze_frames(frames, tolerance=tolerance)
    name = inspection.metadata.get("name") or os.path.basename(os.path.normpath(folder))
    if sheet_path is None:
        sheet_path = os.path.join(_check_dir(name), f"contact_t{tolerance if tolerance is not None else 'na'}.png")
    report["contact_sheet"] = render_contact_sheet(frames, report, sheet_path)
    report["inspect_warnings"] = inspection.warnings
    return report if full else strip_frame_details(report)


# --------------------------------------------------------------------------- #
# 子命令
# --------------------------------------------------------------------------- #

def cmd_settings(args):
    from core.last_settings import load_last_settings
    cm = _config_manager()
    try:
        ffmpeg = _resolve_ffmpeg(cm)
    except CliError as exc:
        ffmpeg = f"(找不到) {exc}"
    tp = cm.get_texture_packer_path() or ""
    return {
        "ok": True,
        "last_settings": load_last_settings(cm),
        "tools": {
            "ffmpeg": ffmpeg,
            "texture_packer": tp if tp and os.path.exists(tp) else f"(未安裝) {tp}".strip(),
        },
    }


def cmd_info(args):
    from core.video import get_video_dimensions, get_video_info
    cm = _config_manager()
    ffmpeg = _resolve_ffmpeg(cm, args.ffmpeg)
    video = os.path.abspath(args.video)
    if not os.path.exists(video):
        raise CliError(f"影片不存在：{video}")
    width, height = get_video_dimensions(video, ffmpeg)
    return {"ok": True, "video": video, "width": width, "height": height,
            "ffmpeg_info": get_video_info(video, ffmpeg).splitlines()}


def cmd_convert(args):
    from ui.services.conversion_service import ConversionService
    cm = _config_manager()
    s = _resolve_convert_settings(args, cm)
    ffmpeg = _resolve_ffmpeg(cm, args.ffmpeg)

    if args.dry_run:
        return {"ok": True, "dry_run": True, "settings": s}

    result = ConversionService(cm).run(
        video=s["video_path"],
        fps=s["fps"],
        output_name=s["output_name"],
        max_width=s["max_width"],
        max_height=s["max_height"],
        output_format=s["output_format"],
        quality=s["quality"],
        use_tinypng=s["use_tinypng"],
        packer_choice=s["packer_choice"],
        enable_resize=s["enable_resize"],
        target_width=s["target_width"],
        target_height=s["target_height"],
        resize_mode=s["resize_mode"],
        enable_bg_removal=s["enable_bg_removal"],
        bg_removal_tolerance=s["bg_removal_tolerance"],
        ffmpeg_path=ffmpeg,
        output_root=args.output_dir,
        update_preview_prefs=False,
        save_as_last=not args.no_save,
        progress=None if args.quiet else _progress,
    )
    payload = {"ok": True, "settings": s, "result": result}

    do_check = s["enable_bg_removal"] and s["output_format"] == "PNG" and not args.no_check
    if do_check:
        payload["check"] = _run_check(result["output_dir"], tolerance=s["bg_removal_tolerance"])
    return payload


def cmd_check(args):
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        raise CliError(f"資料夾不存在：{folder}")
    report = _run_check(folder, tolerance=args.tolerance, sheet_path=args.sheet, full=args.full)
    return {"ok": True, "folder": folder, "check": report}


def cmd_bg_sweep(args):
    """抽影格一次，對取樣影格試多個容差，輸出比較表與比較圖（不產生 plist）"""
    from core.video import extract_frames
    from core.filter import flood_fill_remove_background
    from core.bg_check import analyze_frames, render_sweep_sheet, strip_frame_details
    from core.file_utils import get_application_path
    from PIL import Image
    import numpy as np

    cm = _config_manager()
    s = _resolve_convert_settings(args, cm)
    ffmpeg = _resolve_ffmpeg(cm, args.ffmpeg)
    try:
        tolerances = sorted({int(t) for t in args.tolerances.split(",") if t.strip()})
    except ValueError:
        raise CliError(f"--tolerances 格式錯誤：{args.tolerances}")
    if not tolerances:
        raise CliError("--tolerances 不能是空的")

    key = hashlib.md5(s["video_path"].encode("utf-8")).hexdigest()[:8]
    work = os.path.join(get_application_path(), "temp", f"_sweep_{key}")
    shutil.rmtree(work, ignore_errors=True)
    frames_dir = os.path.join(work, "frames")
    try:
        if not args.quiet:
            _progress(0.05, "提取影格")
        count = extract_frames(
            s["video_path"], frames_dir, s["fps"], ffmpeg, "f", "PNG", s["quality"],
            enable_resize=s["enable_resize"], target_width=s["target_width"],
            target_height=s["target_height"], resize_mode=s["resize_mode"],
        )
        files = sorted(glob.glob(os.path.join(frames_dir, "f_*.png")),
                       key=lambda p: int(os.path.splitext(p)[0].rsplit("_", 1)[-1]))
        pick_pos = np.linspace(0, len(files) - 1, min(args.samples, len(files))).astype(int)
        samples = [(int(os.path.splitext(files[i])[0].rsplit("_", 1)[-1]), files[i]) for i in sorted(set(pick_pos))]

        rows, table = [], []
        for n, tol in enumerate(tolerances):
            if not args.quiet:
                _progress(0.1 + 0.85 * n / len(tolerances), f"容差 {tol}")
            out_dir = os.path.join(work, f"t{tol}")
            frames = []
            for idx, path in samples:
                out = os.path.join(out_dir, os.path.basename(path))
                flood_fill_remove_background(path, tolerance=tol, output_path=out, auto_detect=True)
                with Image.open(out) as im:
                    frames.append((idx, os.path.basename(path), im.convert("RGBA")))
            report = analyze_frames(frames, tolerance=tol)
            rows.append((tol, report, frames))
            table.append({"tolerance": tol, "verdict": report["verdict"], "summary": report["summary"],
                          "issues": strip_frame_details(report, keep_flagged=False)["issues"]})

        ok = [r["tolerance"] for r in table if r["verdict"] == "ok"]
        # 吃主體通常是「過了某個值就整片崩」，只抽樣幾格可能沒抽到，
        # 所以取 OK 區間偏低的中位數保留安全距離；最終仍以完整轉換後的 check 為準
        recommended = ok[(len(ok) - 1) // 2] if ok else None
        name = s["output_name"] if s["output_name"].startswith("v2p_") else "v2p_" + s["output_name"]
        sheet = args.sheet or os.path.join(_check_dir(name), "sweep.png")
        render_sweep_sheet(rows, sheet)
        return {
            "ok": True,
            "video": s["video_path"],
            "frame_count": count,
            "sample_frames": [i for i, _ in samples],
            "fixed_settings": {k: s[k] for k in ("fps", "enable_resize", "target_width", "target_height", "resize_mode")},
            "results": table,
            "ok_tolerances": ok,
            "max_ok_tolerance": ok[-1] if ok else None,
            "recommended_tolerance": recommended,
            "sweep_sheet": sheet,
        }
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)


def cmd_inspect(args):
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        raise CliError(f"資料夾不存在：{folder}")
    report, _frames = _load_output_frames(folder)
    return {"ok": not report.errors, "inspect": report.to_dict()}


# --------------------------------------------------------------------------- #
# 參數解析
# --------------------------------------------------------------------------- #

def _add_convert_options(p):
    p.add_argument("-i", "--input", help="影片路徑（預設：上次的影片）")
    p.add_argument("-n", "--name", help="輸出名稱（會自動加 v2p_ 前綴；預設：上次名稱或影片檔名）")
    p.add_argument("--fps", type=int, help="影格率")
    p.add_argument("--max", help="材質集最大尺寸，例如 1024x1024")
    p.add_argument("--format", choices=["PNG", "JPG", "png", "jpg"], help="輸出格式")
    p.add_argument("--quality", type=int, help="FFmpeg 品質 1(最好)~31")
    p.add_argument("--packer", choices=sorted(PACKER_ALIASES), help="打包器")
    p.add_argument("--tinypng", dest="tinypng", action="store_true", default=None, help="啟用 TinyPNG 壓縮")
    p.add_argument("--no-tinypng", dest="tinypng", action="store_false", help="停用 TinyPNG 壓縮")
    p.add_argument("--resize", help="影格縮放尺寸，例如 240x427；off 表示不縮放")
    p.add_argument("--resize-mode", choices=["stretch", "crop", "pad_black", "pad_transparent"], help="縮放模式")
    p.add_argument("--bg", dest="bg", action="store_true", default=None, help="啟用去背")
    p.add_argument("--no-bg", dest="bg", action="store_false", help="停用去背")
    p.add_argument("--tolerance", type=int, help="去背容差（0~50，越大去得越多）")
    p.add_argument("--ffmpeg", help="FFmpeg 執行檔路徑")


def build_parser():
    parser = argparse.ArgumentParser(prog="v2p", description="V2P 命令列工具：影片 → Cocos2d plist 動畫")
    parser.add_argument("--verbose", action="store_true", help="在 stderr 顯示詳細日誌")
    parser.add_argument("--quiet", action="store_true", help="不顯示進度")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("settings", help="顯示上次的轉換設定與工具路徑")

    p = sub.add_parser("info", help="顯示影片資訊")
    p.add_argument("video")
    p.add_argument("--ffmpeg")

    p = sub.add_parser("convert", help="轉換影片（沒給的參數沿用上次設定）")
    _add_convert_options(p)
    p.add_argument("--output-dir", help="輸出根目錄（預設：工具目錄下的 videos/）")
    p.add_argument("--no-save", action="store_true", help="不要把這次參數存成「上次設定」")
    p.add_argument("--no-check", action="store_true", help="轉換後不做去背品質檢查")
    p.add_argument("--dry-run", action="store_true", help="只顯示最終參數，不轉換")

    p = sub.add_parser("check", help="檢查輸出資料夾的去背品質並產生對照圖")
    p.add_argument("folder")
    p.add_argument("--tolerance", type=int, help="（僅用於建議值）此輸出使用的容差，預設讀 metadata")
    p.add_argument("--sheet", help="對照圖輸出路徑")
    p.add_argument("--full", action="store_true", help="輸出每一格的指標")

    p = sub.add_parser("bg-sweep", help="對取樣影格試多個容差並比較（不產生 plist）")
    _add_convert_options(p)
    p.add_argument("--tolerances", default="2,4,6,8,10,12,16,20,25,30", help="要試的容差，逗號分隔")
    p.add_argument("--samples", type=int, default=6, help="取樣影格數")
    p.add_argument("--sheet", help="比較圖輸出路徑")
    p.add_argument("--keep", action="store_true", help="保留暫存影格")

    p = sub.add_parser("inspect", help="檢查輸出資料夾結構（plist / 材質 / metadata）")
    p.add_argument("folder")
    return parser


HANDLERS = {
    "settings": cmd_settings,
    "info": cmd_info,
    "convert": cmd_convert,
    "check": cmd_check,
    "bg-sweep": cmd_bg_sweep,
    "inspect": cmd_inspect,
}


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0

    _setup_io(args.verbose)
    from core.error_handler import V2PError

    try:
        payload = HANDLERS[args.command](args)
        payload.setdefault("command", args.command)
        _emit(payload)
        return 0 if payload.get("ok") else 1
    except CliError as exc:
        _emit({"ok": False, "command": args.command, "error_type": "usage", "error": str(exc)})
        return 2
    except V2PError as exc:
        _emit({"ok": False, "command": args.command, "error_type": exc.error_type.value,
               "error": exc.message, "details": exc.details})
        return 1
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("CLI 執行失敗")
        _emit({"ok": False, "command": args.command, "error_type": "unexpected", "error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
