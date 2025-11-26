## Why
Lua 端已有 `AnimationLoader` 可即時載入 V2P 產物並檢查 fps、frame count、spritesheet 命名等細節，但 Python 工具本身缺乏可視化的快速驗證／預覽介面。當使用者只想確認輸出資料夾是否健康時，必須手動開啟 plist、靜態圖或切到 Lua 環境，非常耗時且無法立即查看播放結果。

## What Changes
- 在 `Tool/v2p_editor/` 下建立一個 Python 版 V2P Viewer 介面（Tkinter/Gradio），以 Lua `AnimationLoader` 的邏輯為基準，載入 metadata、plist、png 並即時顯示檢查結果與錯誤訊息。
- 介面需提供檔案瀏覽/拖拉輸入、顯示 `v2p_<name>_*.plist/.png`、`metadata.json` 的狀態、fps/frame_count/max_size 等欄位，以及播放控制（播放/暫停/loop）以快速預覽 spritesheet。
- 提供結構化的訊息區塊（例如 JSON 檢查報告或表格）讓使用者能將結果複製到 issue/CI log，即使沒有 CLI 也能取得完整資訊。
- 視需要提供封裝 API 或按鈕，讓主程式或未來 UI tab 可直接呼叫並顯示相同資料。

## Impact
- Affected specs: `v2p-test-tool`
- Affected code: `Tool/v2p_editor/` Viewer 介面、`docs/` 使用指南、可能擴充 `ui/` 元件供主程式帶出 Viewer。

