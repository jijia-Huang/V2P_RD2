"""Entrypoint for the V2P editor viewer."""

from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    from pathlib import Path as _Path
    import sys as _sys

    _sys.path.append(str(_Path(__file__).resolve().parent))
    from viewer import launch_viewer  # type: ignore  # pylint: disable=import-error
else:
    from .viewer import launch_viewer


def main() -> None:
    parser = argparse.ArgumentParser(description="啟動 V2P Viewer 進行檢查與預覽")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="預先載入的 V2P 輸出資料夾路徑",
    )
    args = parser.parse_args()
    initial_path = Path(args.input).expanduser() if args.input else None
    launch_viewer(str(initial_path) if initial_path else None)


if __name__ == "__main__":
    main()

