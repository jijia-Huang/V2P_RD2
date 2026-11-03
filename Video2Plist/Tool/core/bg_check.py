# -*- coding: utf-8 -*-
"""
去背品質檢查

針對「洪水填充去背」的輸出影格做量化檢查，並輸出一張對照圖讓人／AI 目視確認。

量化指標（每格）：
- transparent_ratio：透明像素比例
- leak_ratio：透明區域中「顏色離背景色很遠」的像素佔整格比例
               → 去背吃進主體（容差太大）
- fringe_ratio：主體邊緣（緊貼透明區的不透明像素）中「顏色接近背景色」的比例
               → 邊緣殘留背景色光暈（容差太小）
- residual_ratio：不透明像素中「顏色接近背景色」的面積佔整格比例
               → 背景沒去乾淨；其中 enclosed 為不與已去背區域相連的區塊
                 （被主體包住或被裁在畫面邊緣，洪水填充到不了；調容差無效，屬演算法限制）
- border_opaque_ratio：畫面四周邊框上仍不透明的比例

注意：透明像素的 RGB 會保留原色（Python 打包器與 TexturePacker
--disable-clean-transparency 皆如此），因此可從透明區估出背景色。
"""
import os
import logging

import cv2
import numpy as np
from PIL import Image, ImageDraw

# 判定門檻（Chebyshev 色差，0~255）
BG_LIKE_DIST = 24        # 與背景色差 <= 此值視為「背景色」
LEAK_DIST = 64           # 透明像素與背景色差 > 此值視為「被吃掉的主體」
FRINGE_DIST = 16         # 邊緣像素與背景色差 <= 此值視為「幾乎就是背景色」的殘留
                         # （柔邊主體的邊緣本來就混有背景色，門檻放寬會誤判）

# 問題判定門檻
LEAK_FRAME_RATIO = 0.005     # 單格 leak_ratio 超過 0.5% 視為該格吃到主體
FRINGE_WARN = 0.35           # 邊緣中超過 35% 是背景色 → 光暈明顯
RESIDUAL_WARN = 0.01         # 殘留背景色面積超過整格 1%
NO_REMOVAL_RATIO = 0.005     # 透明比例 < 0.5% 視為完全沒去到背景
ALL_REMOVED_RATIO = 0.98     # 透明比例 > 98% 視為整格幾乎被清空
OUTLIER_MIN_DELTA = 0.10     # 與中位數差超過 10% 才算離群格

_CONTRAST_CANDIDATES = [
    (255, 0, 255), (0, 255, 255), (255, 255, 0),
    (0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 0, 255),
]


def _to_rgba_array(image):
    if isinstance(image, np.ndarray):
        return image
    return np.asarray(image.convert("RGBA"))


def estimate_bg_color(arrays, max_samples=400_000):
    """用所有影格透明區的 RGB 中位數估計背景色；沒有透明像素就用四角顏色"""
    samples = []
    per_frame = max(1, max_samples // max(1, len(arrays)))
    for arr in arrays:
        transparent = arr[..., 3] == 0
        pixels = arr[..., :3][transparent]
        if len(pixels) > per_frame:
            idx = np.linspace(0, len(pixels) - 1, per_frame).astype(int)
            pixels = pixels[idx]
        if len(pixels):
            samples.append(pixels)
    if samples:
        merged = np.concatenate(samples)
        return tuple(int(v) for v in np.median(merged, axis=0))
    corners = []
    for arr in arrays:
        h, w = arr.shape[:2]
        corners.extend([arr[0, 0, :3], arr[0, w - 1, :3], arr[h - 1, 0, :3], arr[h - 1, w - 1, :3]])
    if corners:
        return tuple(int(v) for v in np.median(np.array(corners), axis=0))
    return (0, 0, 0)


def analyze_frame(arr, bg_color):
    """計算單格指標"""
    h, w = arr.shape[:2]
    total = float(h * w)
    alpha = arr[..., 3]
    transparent = alpha == 0
    opaque = ~transparent

    dist = np.abs(arr[..., :3].astype(np.int16) - np.array(bg_color, dtype=np.int16)).max(axis=2)
    bg_like = dist <= BG_LIKE_DIST

    # 透明區中顏色離背景很遠 → 主體被吃掉
    leak = transparent & (dist > LEAK_DIST)

    # 邊緣：與透明像素 4-相鄰的不透明像素
    kernel = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8)
    near_transparent = cv2.dilate(transparent.astype(np.uint8), kernel) > 0
    edge = opaque & near_transparent
    edge_count = int(edge.sum())
    fringe = edge & (dist <= FRINGE_DIST)

    # 殘留背景色（不透明但顏色像背景）
    residual = opaque & bg_like
    residual_count = int(residual.sum())
    enclosed_count = 0
    if residual_count:
        n, labels = cv2.connectedComponents(residual.astype(np.uint8), connectivity=4)
        if n > 1:
            # 只有緊貼已去背區域的殘留，調高容差才可能吃得到；
            # 其他（被主體包住、或被裁在畫面邊緣但不在四個角落）洪水填充根本到不了
            attached = set(np.unique(labels[near_transparent & residual]).tolist())
            attached.discard(0)
            sizes = np.bincount(labels.ravel())
            enclosed_count = int(sum(sizes[i] for i in range(1, n) if i not in attached and sizes[i] >= 16))

    border = np.concatenate([alpha[0, :], alpha[-1, :], alpha[:, 0], alpha[:, -1]])

    return {
        "transparent_ratio": float(transparent.sum() / total),
        "leak_ratio": float(leak.sum() / total),
        "fringe_ratio": float(fringe.sum() / edge_count) if edge_count else 0.0,
        "residual_ratio": float(residual_count / total),
        "enclosed_residual_ratio": float(enclosed_count / total),
        "border_opaque_ratio": float((border > 0).mean()),
    }


def _pick_contrast_color(bg_color):
    bg = np.array(bg_color)
    return max(_CONTRAST_CANDIDATES, key=lambda c: np.abs(np.array(c) - bg).max())


def _r(value, digits=4):
    return round(float(value), digits)


def analyze_frames(frames, tolerance=None):
    """
    分析整組影格

    Args:
        frames: [(index, name, PIL.Image 或 RGBA ndarray), ...]
        tolerance: 這組影格使用的去背容差（只用來產生建議值）

    Returns:
        dict: 檢查報告（含 verdict / issues / suggestion / per-frame 指標）
    """
    if not frames:
        return {"verdict": "error", "issues": [{"code": "NO_FRAMES", "message": "沒有可檢查的影格"}]}

    arrays = [_to_rgba_array(img) for _, _, img in frames]
    bg_color = estimate_bg_color(arrays)

    per_frame = []
    for (index, name, _img), arr in zip(frames, arrays):
        metrics = analyze_frame(arr, bg_color)
        per_frame.append({"index": index, "name": name, **{k: _r(v) for k, v in metrics.items()}})

    tr = np.array([f["transparent_ratio"] for f in per_frame])
    tr_median = float(np.median(tr))
    mad = float(np.median(np.abs(tr - tr_median)))
    outlier_delta = max(OUTLIER_MIN_DELTA, 4 * mad)

    def frames_where(pred):
        return [f["index"] for f in per_frame if pred(f)]

    no_removal = frames_where(lambda f: f["transparent_ratio"] < NO_REMOVAL_RATIO)
    all_removed = frames_where(lambda f: f["transparent_ratio"] > ALL_REMOVED_RATIO)
    leak_frames = frames_where(lambda f: f["leak_ratio"] > LEAK_FRAME_RATIO)
    outliers = frames_where(lambda f: abs(f["transparent_ratio"] - tr_median) > outlier_delta)
    fringe_median = float(np.median([f["fringe_ratio"] for f in per_frame]))
    residual_median = float(np.median([f["residual_ratio"] for f in per_frame]))
    enclosed_median = float(np.median([f["enclosed_residual_ratio"] for f in per_frame]))
    attached_residual = max(0.0, residual_median - enclosed_median)

    issues = []
    direction_votes = []
    n = len(per_frame)

    if no_removal:
        issues.append({
            "code": "NO_REMOVAL", "frames": no_removal,
            "message": f"{len(no_removal)}/{n} 格幾乎沒有去到背景（角落可能不是背景色，或容差太小）",
        })
        direction_votes.append("up")
    if all_removed:
        issues.append({
            "code": "ALL_REMOVED", "frames": all_removed,
            "message": f"{len(all_removed)}/{n} 格幾乎整格透明（主體被吃光，或該格本來就沒有主體）",
        })
        direction_votes.append("down")
    if leak_frames:
        issues.append({
            "code": "LEAK", "frames": leak_frames,
            "message": f"{len(leak_frames)}/{n} 格的透明區含有明顯非背景色 → 去背吃進主體，容差可能太大",
        })
        direction_votes.append("down")
    if fringe_median > FRINGE_WARN:
        issues.append({
            "code": "FRINGE", "value": _r(fringe_median),
            "message": f"主體邊緣有 {fringe_median:.0%} 是背景色 → 邊緣殘留光暈，容差可能太小",
        })
        direction_votes.append("up")
    if attached_residual > RESIDUAL_WARN:
        issues.append({
            "code": "RESIDUAL", "value": _r(attached_residual),
            "message": f"與背景相連的區域仍有 {attached_residual:.1%} 是背景色沒去掉 → 容差可能太小",
        })
        direction_votes.append("up")
    notes = []
    if enclosed_median > RESIDUAL_WARN:
        notes.append({
            "code": "ENCLOSED", "value": _r(enclosed_median),
            "message": f"有 {enclosed_median:.1%} 的背景色區塊與已去背區域不相連（被主體包住，或被裁在畫面邊緣），"
                       f"洪水填充只從四個角落開始，調容差無法解決",
        })
    if outliers:
        issues.append({
            "code": "OUTLIER_FRAMES", "frames": outliers,
            "message": f"{len(outliers)} 格的透明比例與其他格差異過大（中位數 {tr_median:.0%}），請目視確認",
        })

    ups, downs = direction_votes.count("up"), direction_votes.count("down")
    if not issues:
        verdict = "ok"
    elif ups and downs:
        verdict = "mixed"
    elif ups:
        verdict = "under_removed"
    elif downs:
        verdict = "over_removed"
    else:
        verdict = "review"

    suggestion = None
    if tolerance is not None:
        tol = int(tolerance)
        if verdict == "under_removed":
            suggestion = {"direction": "up", "tolerance": min(50, tol + max(2, round(tol * 0.5)))}
        elif verdict == "over_removed":
            suggestion = {"direction": "down", "tolerance": max(0, tol - max(2, round(tol * 0.4)))}
        elif verdict == "mixed":
            suggestion = {"direction": "unclear", "tolerance": tol,
                          "note": "同時有吃主體與殘留背景的跡象，建議用 bg-sweep 比較後再決定"}

    return {
        "verdict": verdict,
        "tolerance": tolerance,
        "bg_color": "#%02X%02X%02X" % bg_color,
        "frame_count": n,
        "summary": {
            "transparent_ratio_median": _r(tr_median),
            "transparent_ratio_min": _r(tr.min()),
            "transparent_ratio_max": _r(tr.max()),
            "leak_ratio_max": _r(max(f["leak_ratio"] for f in per_frame)),
            "fringe_ratio_median": _r(fringe_median),
            "residual_ratio_median": _r(residual_median),
            "enclosed_residual_ratio_median": _r(enclosed_median),
        },
        "issues": issues,
        "notes": notes,
        "suggestion": suggestion,
        "frames": per_frame,
    }


def pick_sample_frames(report, max_samples=8):
    """挑出要放進對照圖的影格：平均分布 + 問題最嚴重的幾格"""
    frames = report.get("frames", [])
    if not frames:
        return []
    indices = [f["index"] for f in frames]
    picks = []

    def add(idx):
        if idx not in picks:
            picks.append(idx)

    worst = []
    flagged = set()
    for issue in report.get("issues", []):
        flagged.update(issue.get("frames", []))
    by_leak = sorted(frames, key=lambda f: f["leak_ratio"], reverse=True)
    by_fringe = sorted(frames, key=lambda f: f["fringe_ratio"], reverse=True)
    for f in by_leak[:2] + by_fringe[:1]:
        if f["index"] in flagged or f["leak_ratio"] > LEAK_FRAME_RATIO:
            worst.append(f["index"])
    worst.extend(sorted(flagged)[:2])

    even_count = max(1, max_samples - min(len(set(worst)), max_samples // 2))
    for pos in np.linspace(0, len(indices) - 1, min(even_count, len(indices))).astype(int):
        add(indices[pos])
    for idx in worst:
        if len(picks) >= max_samples:
            break
        add(idx)
    return sorted(picks)


def _fit(image, max_side):
    w, h = image.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        image = image.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return image


def render_contact_sheet(frames, report, output_path, picks=None, tile_max=220, columns=4):
    """
    產生對照圖：每格上半是「貼在對比色底上的去背結果」，下半是 Alpha 遮罩（白=保留）

    Args:
        frames: [(index, name, PIL.Image), ...]
        report: analyze_frames 的結果
        output_path: 輸出 PNG 路徑
        picks: 要畫的影格 index（預設自動挑選）
    """
    lookup = {index: img for index, _name, img in frames}
    metrics = {f["index"]: f for f in report.get("frames", [])}
    picks = picks if picks is not None else pick_sample_frames(report)
    picks = [p for p in picks if p in lookup]
    if not picks:
        return None

    bg_hex = report.get("bg_color", "#000000").lstrip("#")
    bg_color = tuple(int(bg_hex[i:i + 2], 16) for i in (0, 2, 4))
    contrast = _pick_contrast_color(bg_color)

    tiles = []
    for idx in picks:
        img = _fit(lookup[idx].convert("RGBA"), tile_max)
        comp = Image.new("RGBA", img.size, contrast + (255,))
        comp.alpha_composite(img)
        mask = img.split()[3].convert("RGB")
        tile = Image.new("RGB", (img.width, img.height * 2 + 18), (40, 40, 40))
        tile.paste(comp.convert("RGB"), (0, 0))
        tile.paste(mask, (0, img.height))
        m = metrics.get(idx, {})
        label = f"#{idx} T{m.get('transparent_ratio', 0):.0%} L{m.get('leak_ratio', 0):.1%} F{m.get('fringe_ratio', 0):.0%}"
        ImageDraw.Draw(tile).text((3, img.height * 2 + 3), label, fill=(255, 255, 255))
        tiles.append(tile)

    columns = min(columns, len(tiles))
    rows = (len(tiles) + columns - 1) // columns
    cell_w = max(t.width for t in tiles) + 6
    cell_h = max(t.height for t in tiles) + 6
    header_h = 22
    sheet = Image.new("RGB", (cell_w * columns, cell_h * rows + header_h), (25, 25, 25))
    draw = ImageDraw.Draw(sheet)
    draw.text((4, 4), f"verdict={report.get('verdict')} tol={report.get('tolerance')} "
                      f"bg={report.get('bg_color')} backdrop=#%02X%02X%02X" % contrast, fill=(255, 255, 255))
    for i, tile in enumerate(tiles):
        r, c = divmod(i, columns)
        sheet.paste(tile, (c * cell_w + 3, header_h + r * cell_h + 3))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sheet.save(output_path, "PNG")
    return output_path


def render_sweep_sheet(rows, output_path, tile_max=160):
    """
    產生容差比較圖：每列一個容差，每欄一個取樣影格

    Args:
        rows: [(tolerance, report, [(index, name, PIL.Image), ...]), ...]
    """
    if not rows:
        return None
    bg_hex = rows[0][1].get("bg_color", "#000000").lstrip("#")
    contrast = _pick_contrast_color(tuple(int(bg_hex[i:i + 2], 16) for i in (0, 2, 4)))

    label_w = 150
    grid = []
    for tol, report, frames in rows:
        line = []
        for _idx, _name, img in frames:
            img = _fit(img.convert("RGBA"), tile_max)
            comp = Image.new("RGBA", img.size, contrast + (255,))
            comp.alpha_composite(img)
            line.append(comp.convert("RGB"))
        grid.append((tol, report, line))

    cell_w = max(t.width for _, _, line in grid for t in line) + 4
    cell_h = max(t.height for _, _, line in grid for t in line) + 4
    cols = max(len(line) for _, _, line in grid)
    sheet = Image.new("RGB", (label_w + cell_w * cols, cell_h * len(grid)), (25, 25, 25))
    draw = ImageDraw.Draw(sheet)
    for r, (tol, report, line) in enumerate(grid):
        s = report.get("summary", {})
        draw.text((4, r * cell_h + 4), f"tol={tol}", fill=(255, 255, 255))
        draw.text((4, r * cell_h + 20), f"{report.get('verdict')}", fill=(255, 255, 0))
        draw.text((4, r * cell_h + 36), f"T {s.get('transparent_ratio_median', 0):.0%}", fill=(200, 200, 200))
        draw.text((4, r * cell_h + 52), f"Lmax {s.get('leak_ratio_max', 0):.1%}", fill=(200, 200, 200))
        draw.text((4, r * cell_h + 68), f"F {s.get('fringe_ratio_median', 0):.0%}", fill=(200, 200, 200))
        for c, tile in enumerate(line):
            sheet.paste(tile, (label_w + c * cell_w + 2, r * cell_h + 2))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sheet.save(output_path, "PNG")
    return output_path


def strip_frame_details(report, keep_flagged=True):
    """縮小報告：只保留有問題的影格明細（給 CLI 輸出用）"""
    slim = dict(report)
    frames = report.get("frames", [])
    flagged = set()
    issues = []
    for issue in report.get("issues", []):
        issue = dict(issue)
        if "frames" in issue:
            flagged.update(issue["frames"])
            issue["frame_total"] = len(issue["frames"])
            issue["frames"] = issue["frames"][:15]
        issues.append(issue)
    slim["issues"] = issues
    if keep_flagged:
        worst = sorted((f for f in frames if f["index"] in flagged),
                       key=lambda f: (f["leak_ratio"], abs(f["transparent_ratio"]
                                      - report["summary"]["transparent_ratio_median"])),
                       reverse=True)
        slim["frames"] = worst[:8]
    else:
        slim["frames"] = []
    return slim
