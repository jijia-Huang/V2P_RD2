# Project Context

## Purpose
V2P（Video to Plist）旨在將影片快速轉換為 Cocos2d-x／2d 遊戲可使用的 spritesheet 與 `.plist` 動畫定義。工具提供圖形化介面整合 ffmpeg 影格擷取、影像過濾與 TexturePacker 打包流程，協助美術與技術美術以最少步驟產出可直接放入專案的動畫資產，減少手動切圖與命令列操作成本。

## Tech Stack
- Python 3.8–3.12（核心邏輯、UI 控制）
- Gradio 5.x（瀏覽器操作介面）與 Tkinter（原生設定對話視窗）
- FFmpeg / FFprobe（影格擷取與影片分析）
- TexturePacker CLI（spritesheet 打包）
- Pillow、numpy、python-maxrects-packer（影像處理與矩形排版）
- PyInstaller（Windows 可執行檔打包）

## Project Conventions

### Code Style
- 盡量遵循 PEP 8，慣用 `snake_case` 函式與變數名稱、`CamelCase` 類別名稱。
- 設定、常數集中在 `core/config.py` 與 YAML/JSON 檔案中，避免魔術數字。
- 日誌統一透過 `core/logger.py`，根據執行參數控制等級。

### Architecture Patterns
- `core/`：影片處理、過濾、材質打包、檔案輸出等純邏輯模組，盡量保持無狀態方便測試。
- `ui/`：Gradio 介面與 Tkinter 工具列，以 Tab 組件拆分（主流程、背景去除、管理、設定等）。
- 外部工具（ffmpeg、TexturePacker）透過執行檔呼叫並封裝在 helper 中，確保錯誤可被攔截並記錄。
- 偏好設定／過濾條件使用 JSON 儲存，讓 UI 啟動時可還原。

### Testing Strategy
- 針對幾何排版演算法採用 `python-maxrects-packer/tests` 單元測試；主要流程以手動端對端驗證為主。
- 提交前需至少跑一次樣板影片轉換，檢查輸出 `.plist`、`metadata.json` 與 spritesheet 是否符合預期。
- 關鍵錯誤邏輯（例如參數解析、檔案存在檢查）採用輕量自動測試或腳本確認。

### Git Workflow
- 採用 `main` 穩定分支 + 功能分支（`feature/*`, `fix/*`）流程，完成後透過 PR 合併。
- Commit 訊息以動詞開頭（e.g. `feat: add frame resize presets`），必要時附上問題追蹤編號。
- 與 OpenSpec 整合：變更一律先建立 `openspec/changes/<change-id>/` 並取得核可後再實作。

## Domain Context
- 目標使用者為 2D 遊戲美術／技術美術，重視批次轉檔效率與輸出與 Cocos2d-x 引擎相容性。
- Spritesheet 與 `.plist` 必須符合 TexturePacker/Cocos2d-x 的欄位命名；`metadata.json` 紀錄影格縮放、濾鏡、時間軸等資訊供遊戲載入。
- 設計上需兼顧影片/影像尺寸限制（單邊最大 8192 px）與記憶體占用。

## Important Constraints
- 主要鎖定 Windows 10/11 平台；外部執行檔路徑必須可在系統上被存取。
- 使用者需自行提供 TexturePacker 授權；我們僅驅動 CLI，不可內建授權檔。
- 大型影片處理需保證足夠磁碟空間於 `videos/` 與 `temp/preview_frames/`。
- 若要釋出可執行檔必須使用 PyInstaller 並確保 ffmpeg、ffprobe 附帶於 `Tool/ffmpeg/` 目錄。

## External Dependencies
- `ffmpeg.exe`、`ffprobe.exe`：影格擷取、影片資訊解析。
- `TexturePacker.exe`：spritesheet 打包成 `.plist`。
- Gradio（本地 Web UI）、Tkinter（桌面控件）。
- TinyPNG API（選用，提供 PNG/JPG 壓縮）。
- GitHub（程式碼託管）、OpenSpec CLI（規格管理）。
