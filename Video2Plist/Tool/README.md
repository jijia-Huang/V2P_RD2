# V2P (Video to Plist for Cocos2d-x)

一個將視頻轉換給 Cocos2d-x 可用的 .plist 文件的工具。

## 功能特點

- 支持將視頻文件轉換為 Cocos2d-x 可用的動畫格式
- 提供簡單的 Web 界面進行轉換
- 自動生成 Cocos2d-x 可用的 .plist 文件
- 支持調整輸出參數（如幀數、大小等）
- 詳細的系統日誌記錄
- 支援淺色/深色主題切換

## 需求

- Python 3.8 或更高版本
- ffmpeg.exe 路徑。現在工具內有內置的 ffmpeg.exe，如果需要使用其他版本，請在設定中選擇其他版本
- 在本地端必須先安裝 TexturePacker，執行工具後會要求設定 TexturePacker.exe 路徑。

## 安裝

### 方法 1：使用 python 環境執行

1. 環境要求 Python 3.8 以上
2. 克隆或下載此倉庫到本地
3. 在命令提示符（CMD）中進入項目目錄：
   `cd path\to\V2P`
4. 安裝依賴：
   `pip install -r requirements.txt`
5. 運行程序：
   `python v2p.py [選項]`
6. python版本超過3.11，須升級gradio_client
   `pip install --upgrade gradio gradio_client`

### 方法 2：編譯成可執行檔

1. 環境要求：
   - Windows 10/11
   - Python 3.8+ (建議使用 3.12)
   - pip (Python 包管理器)

2. 克隆或下載此倉庫到本地

3. 在命令提示符（CMD）中進入項目目錄：
   `cd path\to\V2P`

4. 安裝依賴：
   `pip install -r requirements.txt`

依賴包括：

- gradio 5.16.2
- PyYAML 6.0.1
- Pillow 11.1.0
- packaging 23.2

5. 編譯程序：
   `pyinstaller v2p.spec --clean`

編譯後的程序將在 `dist` 目錄中，並且會生成 `v2p.exe` 可執行檔，將 `v2p.exe` 複製到本地端，即可運行。

## 使用方法

### 命令列選項

``` powershell
v2p.exe [選項]

選項：
  -h, --help            顯示說明訊息
  -v, --version         顯示版本資訊
  --port PORT          指定服務埠號（預設：7866）
  --no-browser         啟動後不自動開啟瀏覽器
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        設置日誌記錄級別（預設：INFO）
```

### 基本使用步驟

1. 運行 `v2p.exe` 或 `python v2p.py`
2. 程序會自動打開瀏覽器，顯示轉換界面（如果沒有自動打開，請訪問 <http://127.0.0.1:7866）>
3. 上傳 .mp4 視頻文件
4. 設置轉換參數
5. 點擊轉換按鈕
6. 轉換完成的 .plist 文件會自動保存在 videos 子目錄下

### 在 Cocos2d-x 中使用

1. 從 videos 目錄中找到已轉換完成的 .plist 文件
2. 將 .plist 文件複製到你的 Cocos2d-x 項目的 resources 目錄下
3. 在你的項目中使用這些 .plist 文件

## 項目文件說明

- `animation_loader.lua`: 內置的 animation_loader.lua 腳本，用於加載 .plist 文件
- `ffmpeg.7z`: 內置的 ffmpeg 可執行檔，要使用前請解壓縮到同目錄下
- `ffprobe.7z`: 內置的 ffprobe 可執行檔，用於預覽影片，要使用前請解壓縮到同目錄下
- `requirements.txt`: Python 依賴列表
- `v2p.py`: python main entry
- `v2p.spec`: PyInstaller 配置文件
- `videos/`: 轉換後的 .plist 文件存放目錄
- `log/`: 系統日誌存放目錄，格式為 v2p_YYYYMMDD.log

## 日誌系統

程式會自動記錄運行日誌，存放在 `log` 目錄下：

- 檔案名格式：`v2p_YYYYMMDD.log`
- 預設級別：INFO
- 可通過 `--log-level` 參數調整記錄詳細程度
- 建議在遇到問題時使用 `--log-level DEBUG` 收集更詳細的資訊

## 注意事項

- 建議使用較短的視頻進行轉換
- 確保輸出的圖片大小適合你的項目需求
- 確保有足夠的磁盤空間用於臨時文件
- 如果遇到防火牆提示，請允許程序訪問網絡（僅用於本地 Web 界面）
- 如果遇到 ffmpeg 報錯，請檢查 ffmpeg.exe 是否正確
- 如果遇到 TexturePacker 報錯，請檢查 TexturePacker.exe 是否正確
- 如果遇到其他問題，請：
  1. 使用 `--log-level DEBUG` 收集詳細日誌
  2. 將日誌檔案和問題描述一併回報

## 版本歷史

### v1.1.0 (2025-10-09)

- 🎉 **新功能：Frame 尺寸縮放**
  - 支援在影格擷取時調整尺寸（1-8192 像素）
  - 四種縮放模式：拉伸變形、裁切中心、填充黑邊、填充透明邊
  - 長寬比鎖定功能，自動計算對應尺寸
  - 快速比例選擇按鈕（1:1, 16:9, 9:16, 4:3, 原始）
- 🔧 **改進**
  - 偏好設定自動儲存縮放參數
  - Metadata 完整記錄縮放資訊（原始尺寸、縮放後尺寸、縮放模式）
  - 增強的 FFmpeg 命令日誌記錄
  - 新增 `get_video_dimensions()` 函數獲取影片原始尺寸

### v1.0.4 (2025-03-26)

- TinyPNG 壓縮功能加入，支援 PNG/JPG 格式的進階壓縮
- 修正偏好設定中布林值（如 TinyPNG 壓縮選項）的儲存與讀取問題
- 改進錯誤處理機制，提供更清晰的錯誤訊息
- 修正中文檔名處理問題，提升系統穩定性

### v1.0.3 (2025-03-20)

- 新增輸出格式選擇功能（PNG/JPG）
- 移除無用的「輸出子資料夾」，合併由輸出名稱決定，並加入`v2p_`前綴避免重複
- 新增輸出品質調整功能（1-31，建議值：5）
- 優化材質打包設定，提升輸出效率
- 改進錯誤處理和日誌記錄
- 修正 FFmpeg 影格提取參數
- 優化使用者介面配置
- 新增偏好設定儲存功能（FPS、材質大小、輸出格式、品質）

### v1.0.2 (2025-03-03)

- 修正輸出 plist 影格名稱錯誤
- animation_loader.lua 修正讀入 plist 錯誤
- 調整介面配置
- 調整 TexturePacker 輸出格式，讓其可以塞入更多資料 (但會更耗時)

### v1.0.1 (2025-02-20)

- 架構重構
- 完善日誌系統
- 改進相容性檢查
- 優化使用者介面
- 添加命令列參數支援

### v1.0.0 (2025-02-19)

- 首次發布
- 基本功能完整實現
