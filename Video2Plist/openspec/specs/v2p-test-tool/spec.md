# v2p-test-tool Specification

## Purpose
TBD - created by archiving change add-v2p-python-validator. Update Purpose after archive.
## Requirements
### Requirement: Python V2P 驗證介面
V2P 系統 SHALL 在 `Tool/v2p_editor/` 提供一個圖形化介面，可載入 V2P 輸出資料夾並依照 Lua `AnimationLoader` 的邏輯檢查檔案齊全性、metadata/plist/png 一致性與 fps/frame_count 欄位，並即時顯示摘要與錯誤。

#### Scenario: 資料夾結構完整
- **GIVEN** 使用者執行 `python Tool/v2p_editor/main.py` 並載入 `videos/v2p_123`
- **WHEN** 介面掃描到 `v2p_123_metadata.json`、對應的 `v2p_123_*.plist/.png`
- **THEN** 它 SHALL 在資訊面板展示 fps、frame_count、plist_count 摘要並顯示「狀態：正常」。

#### Scenario: 缺檔立即失敗
- **GIVEN** 使用者載入的資料夾缺少某個 plist 或 png
- **WHEN** 介面偵測命名集合不匹配
- **THEN** 它 SHALL 以醒目顏色列出遺失清單、標註錯誤狀態並允許使用者複製詳細訊息。

### Requirement: 快速播放預覽
V2P 驗證介面 SHALL 支援快速預覽（Tkinter/Pillow）播放面板，重用 Lua 動畫邏輯（fps、loop、加上 `v2p_` 前綴）讓美術不開 Lua 也能檢查 spritesheet 播放是否正常。

#### Scenario: 指定動畫預覽
- **GIVEN** 使用者載入資料夾並在 Viewer 中選擇動畫 `main_idle`
- **WHEN** 工具載入對應 plist frame 並按照 metadata fps 播放
- **THEN** 它 SHALL 在同一介面顯示播放/暫停控制、loop 狀態與 fps 指標，以便快速辨識錯誤影格。

