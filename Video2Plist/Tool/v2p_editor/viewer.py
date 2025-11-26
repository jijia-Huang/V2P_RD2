"""Tkinter viewer for V2P outputs."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

from PIL import Image, ImageTk

try:  # pragma: no cover - fallback when executed as script
    from .inspector import FramePreview, InspectionReport, ProjectInspector
except ImportError:  # pragma: no cover
    from inspector import FramePreview, InspectionReport, ProjectInspector  # type: ignore

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    TkBase = tk.Tk
    DND_FILES = None
else:  # pragma: no cover - optional dependency
    TkBase = TkinterDnD.Tk


class V2PViewerApp(TkBase):
    """Main application window."""

    def __init__(self, initial_path: Optional[str] = None):
        super().__init__()
        self.title("V2P Editor Viewer")
        self.geometry("1280x780")
        self.minsize(960, 640)

        self.inspector = ProjectInspector()
        self.report: Optional[InspectionReport] = None
        self.tk_frames: Dict[int, ImageTk.PhotoImage] = {}
        self.current_index = 0
        self.is_playing = False
        self.play_job: Optional[str] = None

        self.path_var = tk.StringVar(value=initial_path or "")
        self.status_var = tk.StringVar(value="請選擇或拖曳 V2P 輸出資料夾")
        self.loop_var = tk.BooleanVar(value=True)
        self.fps_var = tk.DoubleVar(value=24.0)
        self.frame_counter_var = tk.StringVar(value="0/0")
        self.frame_detail_var = tk.StringVar(value="尚未載入任何影格")

        self.info_vars = {
            "name": tk.StringVar(value="--"),
            "fps": tk.StringVar(value="--"),
            "frame_count": tk.StringVar(value="--"),
            "plist_count": tk.StringVar(value="--"),
            "max_size": tk.StringVar(value="--"),
            "frame_size": tk.StringVar(value="--"),
            "creation_time": tk.StringVar(value="--"),
            "tool_version": tk.StringVar(value="--"),
            "output_format": tk.StringVar(value="--"),
        }

        self._build_ui()
        if DND_FILES:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._handle_drop)
            except Exception:  # pragma: no cover - defensive
                pass

        if initial_path:
            self.after(100, lambda: self.load_project(initial_path))

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        control_frame = ttk.Frame(self, padding=10)
        control_frame.grid(row=0, column=0, sticky="ew")
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="輸出資料夾：").grid(row=0, column=0, padx=(0, 8))
        path_entry = ttk.Entry(control_frame, textvariable=self.path_var)
        path_entry.grid(row=0, column=1, sticky="ew")
        path_entry.bind("<Return>", lambda event: self.load_project(self.path_var.get()))

        ttk.Button(
            control_frame, text="瀏覽...", command=self._browse_folder
        ).grid(row=0, column=2, padx=8)
        ttk.Button(
            control_frame, text="載入資料夾", command=lambda: self.load_project(self.path_var.get())
        ).grid(row=0, column=3)
        ttk.Button(
            control_frame, text="複製檢查報告", command=self._copy_report
        ).grid(row=0, column=4, padx=(8, 0))

        ttk.Label(control_frame, textvariable=self.status_var, foreground="#1565c0").grid(
            row=1, column=0, columnspan=5, sticky="w", pady=(6, 0)
        )

        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew")

        left_frame = ttk.Frame(paned, padding=10)
        right_frame = ttk.Frame(paned, padding=10)
        paned.add(left_frame, weight=2)
        paned.add(right_frame, weight=3)

        self._build_info_panel(left_frame)
        self._build_preview_panel(right_frame)

    def _build_info_panel(self, parent: ttk.Frame) -> None:
        info_box = ttk.LabelFrame(parent, text="Metadata")
        info_box.pack(fill="x")
        for idx, (label, key) in enumerate(
            [
                ("名稱", "name"),
                ("FPS", "fps"),
                ("影格數", "frame_count"),
                ("Atlas 數", "plist_count"),
                ("最大尺寸", "max_size"),
                ("Frame Size", "frame_size"),
                ("建立時間", "creation_time"),
                ("工具版本", "tool_version"),
                ("輸出格式", "output_format"),
            ]
        ):
            ttk.Label(info_box, text=label + "：", width=10).grid(
                row=idx, column=0, sticky="w", padx=4, pady=2
            )
            ttk.Label(info_box, textvariable=self.info_vars[key]).grid(
                row=idx, column=1, sticky="w", padx=4, pady=2
            )

        files_box = ttk.LabelFrame(parent, text="檔案狀態")
        files_box.pack(fill="both", expand=True, pady=(10, 0))
        self.file_tree = ttk.Treeview(
            files_box,
            columns=("path", "status"),
            show="headings",
            height=6,
        )
        self.file_tree.heading("path", text="名稱")
        self.file_tree.heading("status", text="狀態")
        self.file_tree.column("path", width=180)
        self.file_tree.column("status", width=140)
        file_scroll = ttk.Scrollbar(files_box, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scroll.set)
        self.file_tree.pack(side="left", fill="both", expand=True)
        file_scroll.pack(side="right", fill="y")

        log_box = ttk.LabelFrame(parent, text="錯誤 / 警示")
        log_box.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text = tk.Text(
            log_box, height=10, wrap="word", state="disabled", background="#f5f5f5"
        )
        self.log_text.tag_config("error", foreground="#c62828")
        self.log_text.tag_config("warn", foreground="#ef6c00")
        self.log_text.pack(fill="both", expand=True)

    def _build_preview_panel(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        preview_box = ttk.LabelFrame(parent, text="播放預覽")
        preview_box.grid(row=0, column=0, sticky="nsew")
        preview_box.columnconfigure(0, weight=1)
        preview_box.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(preview_box, anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        control_frame = ttk.Frame(preview_box)
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        ttk.Button(control_frame, text="◀ 上一幀", command=self.show_previous).pack(
            side="left", padx=2
        )
        ttk.Button(control_frame, text="播放", command=self.start_playback).pack(
            side="left", padx=2
        )
        ttk.Button(control_frame, text="暫停", command=self.pause_playback).pack(
            side="left", padx=2
        )
        ttk.Button(control_frame, text="下一幀 ▶", command=self.show_next).pack(
            side="left", padx=2
        )

        ttk.Checkbutton(control_frame, text="循環播放", variable=self.loop_var).pack(
            side="left", padx=12
        )
        ttk.Label(control_frame, text="播放 FPS").pack(side="left", padx=(12, 4))
        ttk.Spinbox(
            control_frame,
            from_=1,
            to=120,
            textvariable=self.fps_var,
            width=5,
            increment=1,
        ).pack(side="left")
        ttk.Label(control_frame, textvariable=self.frame_counter_var).pack(
            side="right", padx=(0, 8)
        )

        ttk.Label(preview_box, textvariable=self.frame_detail_var).grid(
            row=2, column=0, sticky="w", padx=10, pady=(0, 6)
        )

        frames_box = ttk.LabelFrame(parent, text="影格列表")
        frames_box.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        frames_box.columnconfigure(0, weight=1)
        frames_box.rowconfigure(0, weight=1)

        self.frames_tree = ttk.Treeview(
            frames_box,
            columns=("index", "name", "sheet", "size"),
            show="headings",
        )
        self.frames_tree.heading("index", text="#")
        self.frames_tree.heading("name", text="檔名")
        self.frames_tree.heading("sheet", text="來自圖集")
        self.frames_tree.heading("size", text="尺寸")
        self.frames_tree.column("index", width=60, anchor="center")
        self.frames_tree.column("name", width=200)
        self.frames_tree.column("sheet", width=160)
        self.frames_tree.column("size", width=100, anchor="center")
        frame_scroll = ttk.Scrollbar(frames_box, orient="vertical", command=self.frames_tree.yview)
        self.frames_tree.configure(yscrollcommand=frame_scroll.set)
        self.frames_tree.bind("<<TreeviewSelect>>", self._on_frame_selected)
        self.frames_tree.grid(row=0, column=0, sticky="nsew")
        frame_scroll.grid(row=0, column=1, sticky="ns")

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _browse_folder(self) -> None:
        selection = filedialog.askdirectory(title="選擇 V2P 輸出資料夾")
        if selection:
            self.path_var.set(selection)
            self.load_project(selection)

    def _handle_drop(self, event) -> None:  # pragma: no cover - UI callback
        paths = self.tk.splitlist(event.data)
        if not paths:
            return
        path = paths[0].strip("{}")
        self.path_var.set(path)
        self.load_project(path)

    def load_project(self, path: str) -> None:
        if not path:
            self.status_var.set("請輸入資料夾路徑")
            return
        try:
            self.report = self.inspector.inspect(path)
        except Exception as exc:  # pylint: disable=broad-except
            self.report = None
            messagebox.showerror("載入失敗", str(exc))
            self.status_var.set("載入失敗，詳情請見對話框")
            self._clear_view()
            return

        self.status_var.set(f"已載入：{self.report.folder}")
        self.fps_var.set(self.report.metadata.get("fps", 24))
        self._populate_metadata()
        self._populate_files()
        self._populate_logs()
        self._populate_frames()
        self._prepare_preview_frames()

    def _clear_view(self) -> None:
        self.pause_playback()
        for var in self.info_vars.values():
            var.set("--")
        self.file_tree.delete(*self.file_tree.get_children())
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self.frames_tree.delete(*self.frames_tree.get_children())
        self.preview_label.configure(image="")
        self.frame_detail_var.set("尚未載入任何影格")
        self.frame_counter_var.set("0/0")

    def _populate_metadata(self) -> None:
        if not self.report:
            return
        meta = self.report.metadata
        self.info_vars["name"].set(meta.get("name") or self.report.name)
        self.info_vars["fps"].set(str(meta.get("fps", "--")))
        self.info_vars["frame_count"].set(str(meta.get("frame_count", "--")))
        self.info_vars["plist_count"].set(str(meta.get("plist_count", "--")))
        self.info_vars["max_size"].set(
            f"{meta.get('max_width', '-') }x{meta.get('max_height', '-')}"
        )
        self.info_vars["frame_size"].set(meta.get("frame_size", "--"))
        self.info_vars["creation_time"].set(meta.get("creation_time", "--"))
        self.info_vars["tool_version"].set(meta.get("tool_version", "--"))
        self.info_vars["output_format"].set(meta.get("output_format", "--"))

    def _populate_files(self) -> None:
        self.file_tree.delete(*self.file_tree.get_children())
        if not self.report:
            return
        for status in self.report.file_status:
            label = "✅ 正常" if status.exists else "⚠ 缺少"
            if status.extra and status.extra not in label:
                label = f"{label} - {status.extra}"
            self.file_tree.insert("", "end", values=(status.path, label))

    def _populate_logs(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        if not self.report:
            self.log_text.insert(tk.END, "尚未進行檢查。\n")
        else:
            if not self.report.errors and not self.report.warnings:
                self.log_text.insert(tk.END, "檔案結構正常，未發現問題。\n")
            for err in self.report.errors:
                self.log_text.insert(tk.END, f"[ERROR] {err}\n", "error")
            for warn in self.report.warnings:
                self.log_text.insert(tk.END, f"[WARN] {warn}\n", "warn")
        self.log_text.configure(state="disabled")

    def _populate_frames(self) -> None:
        self.frames_tree.delete(*self.frames_tree.get_children())
        if not self.report:
            return
        for idx, frame in enumerate(self.report.frames):
            self.frames_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    frame.index,
                    frame.name,
                    frame.sheet,
                    f"{frame.size[0]}x{frame.size[1]}",
                ),
            )
        if self.report.frames:
            self.frames_tree.selection_set("0")
            self.frames_tree.focus("0")
            self.show_frame(0)
        else:
            self.preview_label.configure(image="")
            self.frame_counter_var.set("0/0")
            self.frame_detail_var.set("找不到任何影格")

    def _prepare_preview_frames(self) -> None:
        self.tk_frames.clear()
        self.current_index = 0
        self.pause_playback()
        if not self.report:
            return
        for idx, frame in enumerate(self.report.frames):
            self.tk_frames[idx] = self._convert_to_tk(frame.image)
        if self.report.frames:
            self.frame_counter_var.set(f"1/{len(self.report.frames)}")
            self.frame_detail_var.set(f"{self.report.frames[0].name} @ {self.report.frames[0].sheet}")

    def _convert_to_tk(self, image) -> ImageTk.PhotoImage:
        max_w, max_h = 640, 640
        width, height = image.size
        scale = min(max_w / width, max_h / height, 1.0)
        if scale < 1.0:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            image = image.resize(new_size, Image.LANCZOS)
        return ImageTk.PhotoImage(image=image)

    def start_playback(self) -> None:
        if not self.report or not self.report.frames:
            return
        self.is_playing = True
        self._schedule_next_frame()

    def pause_playback(self) -> None:
        self.is_playing = False
        if self.play_job is not None:
            self.after_cancel(self.play_job)
            self.play_job = None

    def _schedule_next_frame(self) -> None:
        self.show_frame(self.current_index)
        delay = max(1, int(1000 / max(1, self.fps_var.get())))
        if self.is_playing:
            self.play_job = self.after(delay, self._advance_frame)

    def _advance_frame(self) -> None:
        if not self.report or not self.report.frames:
            return
        next_index = self.current_index + 1
        if next_index >= len(self.report.frames):
            if self.loop_var.get():
                next_index = 0
            else:
                self.pause_playback()
                return
        self.current_index = next_index
        self._schedule_next_frame()

    def show_frame(self, index: int) -> None:
        if not self.report or not self.report.frames:
            return
        index = max(0, min(index, len(self.report.frames) - 1))
        frame = self.report.frames[index]
        tk_image = self.tk_frames.get(index)
        if tk_image is None:
            tk_image = self._convert_to_tk(frame.image)
            self.tk_frames[index] = tk_image
        self.preview_label.configure(image=tk_image)
        self.preview_label.image = tk_image
        self.current_index = index
        self.frame_counter_var.set(f"{index + 1}/{len(self.report.frames)}")
        self.frame_detail_var.set(f"{frame.name} | {frame.sheet} | {frame.size[0]}x{frame.size[1]}")

    def show_previous(self) -> None:
        self.pause_playback()
        self.show_frame(self.current_index - 1)

    def show_next(self) -> None:
        self.pause_playback()
        self.show_frame(self.current_index + 1)

    def _on_frame_selected(self, _) -> None:
        selection = self.frames_tree.selection()
        if not selection:
            return
        try:
            idx = int(selection[0])
        except ValueError:
            return
        self.pause_playback()
        self.show_frame(idx)

    def _copy_report(self) -> None:
        if not self.report:
            messagebox.showinfo("尚未載入", "請先載入 V2P 輸出資料夾")
            return
        data = self.report.to_dict()
        text = json.dumps(data, indent=2, ensure_ascii=False)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set("已複製 JSON 報告到剪貼簿")


def launch_viewer(initial_path: Optional[str] = None) -> None:
    """Helper that launches the standalone viewer."""

    app = V2PViewerApp(initial_path=initial_path)
    app.mainloop()

