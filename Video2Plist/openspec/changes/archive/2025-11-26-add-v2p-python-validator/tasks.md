## 1. 需求蒐集與對齊
- [x] 1.1 盤點 `Lua/AnimationLoader.lua` 的載入流程（命名、fps、loop、快取邏輯）。
- [x] 1.2 定義 Python Viewer 介面的互動行為（資料夾選擇、動畫篩選、播放控制）。
- [x] 1.3 確認既有 `videos/` 範例資料與 QA 需求，列出必須檢查的錯誤型別與訊息格式。

## 2. Python Viewer 介面實作
- [x] 2.1 在 `Tool/v2p_editor/` 下建立 GUI 主程式（Tkinter/Gradio），可載入指定輸出資料夾並顯示摘要資訊。
- [x] 2.2 實作檢查邏輯：檔案存在性、plist/png/metadata 數量一致、fps/frame_count 整合，並在介面顯示警示訊息。
- [x] 2.3 參考 Lua 邏輯製作播放面板（播放/暫停、loop、fps 顯示），可即時預覽 spritesheet。
- [x] 2.4 提供資訊面板／可複製的 JSON 報表，讓使用者將檢查結果貼回 issue/CI log。
- [x] 2.5 規劃後續與主程式整合的入口（例如按鈕呼叫 Viewer 或提供 API）。

## 3. 文件與驗證
- [x] 3.1 撰寫使用說明（README/docs）示範如何啟動 Viewer、載入資料夾與解讀訊息。
- [x] 3.2 以至少一組現有 `videos/v2p_*` 輸出操作介面，截圖或錄影記錄結果。
- [x] 3.3 `openspec validate add-v2p-python-validator --strict` 並修正所有問題，提報審核。

