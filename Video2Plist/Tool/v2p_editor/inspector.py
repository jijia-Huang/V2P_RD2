"""Core logic for inspecting V2P output folders."""

from __future__ import annotations

import json
import plistlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image


@dataclass
class FramePreview:
    """Represents a single frame extracted from the spritesheet."""

    name: str
    index: int
    sheet: str
    size: Tuple[int, int]
    rotated: bool
    image: Image.Image


@dataclass
class FileStatus:
    """Tracks the existence and basic info of an output artifact."""

    label: str
    path: str
    exists: bool
    extra: str = ""


@dataclass
class InspectionReport:
    """Aggregate inspection results."""

    name: str
    folder: Path
    metadata: Dict[str, Any]
    frames: List[FramePreview]
    file_status: List[FileStatus] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize a light-weight snapshot for copying or logging."""
        return {
            "name": self.name,
            "folder": str(self.folder),
            "metadata": self.metadata,
            "frames_detected": len(self.frames),
            "errors": self.errors,
            "warnings": self.warnings,
            "files": [
                {
                    "label": status.label,
                    "path": status.path,
                    "exists": status.exists,
                    "extra": status.extra,
                }
                for status in self.file_status
            ],
        }


class ProjectInspector:
    """Loads metadata/plists/pngs from a V2P output folder."""

    _RECT_RE = re.compile(r"-?\d+")
    _INDEX_RE = re.compile(r"(\d+)(?=\.png$)")

    def inspect(self, target: Path | str) -> InspectionReport:
        folder = Path(target).expanduser().resolve()
        if not folder.exists():
            raise FileNotFoundError(f"找不到輸出資料夾: {folder}")
        if not folder.is_dir():
            raise NotADirectoryError(f"路徑不是資料夾: {folder}")

        metadata_path = self._locate_metadata(folder)
        metadata: Dict[str, Any] = {}
        file_status: List[FileStatus] = []
        errors: List[str] = []
        warnings: List[str] = []

        if metadata_path:
            metadata = self._load_metadata(metadata_path) or {}
            file_status.append(
                FileStatus("metadata", str(metadata_path.name), True, "OK")
            )
        else:
            errors.append("找不到 *_metadata.json，請確認資料夾是否正確。")

        project_name = metadata.get("name") or folder.name
        plist_files = self._collect_plists(folder, project_name)
        texture_map = self._derive_texture_map(folder, plist_files, metadata)

        for plist_path in plist_files:
            exists = plist_path.exists()
            file_status.append(
                FileStatus(
                    "plist",
                    plist_path.name,
                    exists,
                    "OK" if exists else "缺少 plist",
                )
            )
            if not exists:
                errors.append(f"缺少 plist: {plist_path.name}")

        for texture_name, texture_path in texture_map.items():
            exists = texture_path.exists()
            file_status.append(
                FileStatus(
                    "texture",
                    texture_path.name,
                    exists,
                    "OK" if exists else "缺少對應 png",
                )
            )
            if not exists:
                errors.append(f"缺少 spritesheet: {texture_path.name}")

        frames: List[FramePreview] = []
        if not errors:
            frames = self._extract_frames(folder, plist_files, texture_map)

        if metadata:
            expected_plists = metadata.get("plist_count")
            if expected_plists is not None and expected_plists != len(plist_files):
                warnings.append(
                    f"metadata 宣告 plist_count={expected_plists} "
                    f"但實際找到 {len(plist_files)} 個 plist"
                )
            expected_frames = metadata.get("frame_count")
            if expected_frames is not None and expected_frames != len(frames):
                warnings.append(
                    f"metadata 宣告 frame_count={expected_frames} "
                    f"但實際解析 {len(frames)} 幅"
                )

        return InspectionReport(
            name=project_name,
            folder=folder,
            metadata=metadata,
            frames=frames,
            file_status=file_status,
            errors=errors,
            warnings=warnings,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _locate_metadata(self, folder: Path) -> Optional[Path]:
        expected = folder / f"{folder.name}_metadata.json"
        if expected.exists():
            return expected
        candidates = list(folder.glob("*_metadata.json"))
        if len(candidates) == 1:
            return candidates[0]
        return None

    def _load_metadata(self, metadata_path: Path) -> Optional[Dict[str, Any]]:
        try:
            with metadata_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:  # pylint: disable=broad-except
            raise ValueError(f"無法解析 metadata: {metadata_path}") from exc

    def _collect_plists(self, folder: Path, base_name: str) -> List[Path]:
        pattern = f"{base_name}_*.plist"
        candidates = sorted(
            folder.glob(pattern),
            key=lambda path: self._extract_suffix_index(path.stem),
        )
        if candidates:
            return candidates
        fallback = folder / f"{base_name}.plist"
        return [fallback] if fallback.exists() else []

    def _derive_texture_map(
        self,
        folder: Path,
        plist_files: Sequence[Path],
        metadata: Dict[str, Any],
    ) -> Dict[str, Path]:
        texture_map: Dict[str, Path] = {}
        output_format = (metadata.get("output_format") or "png").lower()
        for plist_path in plist_files:
            if not plist_path.exists():
                continue
            texture_name = plist_path.with_suffix(f".{output_format}").name
            texture_map.setdefault(texture_name, folder / texture_name)
        return texture_map

    def _extract_frames(
        self,
        folder: Path,
        plist_files: Sequence[Path],
        texture_map: Dict[str, Path],
    ) -> List[FramePreview]:
        frames: List[FramePreview] = []
        sheet_cache: Dict[str, Image.Image] = {}
        file_errors: List[str] = []

        try:
            for plist_path in plist_files:
                if not plist_path.exists():
                    continue
                with plist_path.open("rb") as fh:
                    plist_data = plistlib.load(fh)
                plist_frames: Dict[str, Any] = plist_data.get("frames", {})
                texture_name = (
                    plist_data.get("metadata", {}).get("textureFileName")
                    or plist_path.with_suffix(".png").name
                )
                sheet_path = texture_map.get(texture_name) or (folder / texture_name)
                sheet_image = self._load_sheet(sheet_cache, sheet_path)
                if sheet_image is None:
                    file_errors.append(f"無法載入 spritesheet: {sheet_path.name}")
                    continue
                for frame_name, frame_data in plist_frames.items():
                    rect = self._parse_rect(frame_data.get("textureRect", ""))
                    if rect is None:
                        continue
                    x, y, w, h = rect
                    cropped = sheet_image.crop((x, y, x + w, y + h)).copy()
                    rotated_flag = bool(frame_data.get("textureRotated"))
                    target_size = self._parse_size(
                        frame_data.get("spriteSize")
                        or frame_data.get("spriteSourceSize", "")
                    )
                    if target_size:
                        cropped = self._normalize_orientation(
                            cropped, rotated_flag, target_size
                        )
                    frame_index = self._extract_frame_index(frame_name)
                    frames.append(
                        FramePreview(
                            name=frame_name,
                            index=frame_index,
                            sheet=texture_name,
                            size=cropped.size,
                            rotated=rotated_flag,
                            image=cropped,
                        )
                    )
        finally:
            for sheet in sheet_cache.values():
                sheet.close()
        if file_errors:
            raise ValueError("\n".join(file_errors))

        frames.sort(key=lambda item: item.index)
        return frames

    def _load_sheet(
        self, cache: Dict[str, Image.Image], sheet_path: Path
    ) -> Optional[Image.Image]:
        if sheet_path.name in cache:
            return cache[sheet_path.name]
        if not sheet_path.exists():
            return None
        image = Image.open(sheet_path).convert("RGBA")
        cache[sheet_path.name] = image
        return image

    def _parse_rect(self, rect: str) -> Optional[Tuple[int, int, int, int]]:
        numbers = self._RECT_RE.findall(rect)
        if len(numbers) >= 4:
            x, y, w, h = map(int, numbers[:4])
            return x, y, w, h
        return None

    def _parse_size(self, size_str: str) -> Optional[Tuple[int, int]]:
        numbers = self._RECT_RE.findall(size_str)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        return None

    def _normalize_orientation(
        self,
        image: Image.Image,
        rotated_flag: bool,
        target_size: Optional[Tuple[int, int]] = None,
    ) -> Image.Image:
        if not rotated_flag:
            return image

        candidates = [
            image.rotate(90, expand=True),
            image.rotate(-90, expand=True),
        ]

        if target_size:
            for candidate in candidates:
                if candidate.size == target_size:
                    return candidate

        return candidates[0]

    def _extract_frame_index(self, frame_name: str) -> int:
        match = self._INDEX_RE.search(frame_name)
        if match:
            return int(match.group(1))
        return len(frame_name)

    def _extract_suffix_index(self, stem: str) -> int:
        match = self._RECT_RE.findall(stem)
        return int(match[-1]) if match else 0

