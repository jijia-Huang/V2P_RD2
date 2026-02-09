# V2P 工具產品需求文檔 (PRD)

**版本**: 1.0.4  
**最後更新**: 2025-10-09  
**產品名稱**: V2P (Video to Plist for Cocos2d-x)

---

## 一、產品概述

### 1.1 產品定位

V2P 是一款桌面工具，專為 Cocos2d-x 遊戲開發者設計，用於將視頻動畫轉換為遊戲引擎可用的 plist 格式材質集。它解決了遊戲開發中動畫資源製作的痛點，讓美術人員可以使用專業視頻編輯工具製作動畫，然後快速轉換為遊戲可用的格式。

### 1.2 目標用戶

**主要用戶**:
- Cocos2d-x 遊戲開發者
- 遊戲美術設計師
- 獨立遊戲開發團隊

**使用場景**:
- 角色動畫製作（行走、攻擊、技能等）
- UI 動畫效果
- 場景特效動畫
- 過場動畫

### 1.3 核心價值主張

1. **簡化工作流程**: 一鍵轉換視頻為遊戲資源，無需手動處理
2. **提高製作效率**: 利用專業視頻工具的強大功能製作動畫
3. **優化資源大小**: 整合材質打包和壓縮，減少遊戲包體積
4. **開箱即用**: 提供完整的 Lua 加載器，快速整合到項目中
5. **可視化操作**: 直觀的 Web 介面，無需命令列操作

### 1.4 競品分析

**傳統方案的痛點**:
- 手動使用 FFmpeg + TexturePacker：流程複雜，易出錯
- 逐幀手繪：耗時費力，難以製作流暢動畫
- Unity/Spine 等工具：學習成本高，可能不適合簡單動畫

**V2P 的優勢**:
- 整合完整工作流程
- 自動化處理，減少人工操作
- 參數可調，滿足不同需求
- 免費開源，無授權費用

---

## 二、功能需求

### 2.1 核心功能

#### 2.1.1 視頻轉換功能

**功能描述**: 將 MP4 視頻檔案轉換為 Cocos2d-x 可用的 plist 材質集。

**輸入**:
- MP4 視頻檔案
- 轉換參數（FPS、材質大小、輸出格式、品質）

**輸出**:
- Plist 材質集檔案（一個或多個）
- 對應的圖片檔案（PNG 或 JPG）
- Metadata 元數據檔案（JSON）

**處理流程**:
```
1. 使用者上傳 MP4 檔案
2. 設定轉換參數
3. 點擊「開始轉換」
4. 系統顯示處理進度
5. 轉換完成，顯示輸出路徑
```

**參數說明**:

| 參數 | 類型 | 範圍 | 預設值 | 說明 |
|------|------|------|--------|------|
| FPS | 整數 | 1-60 | 24 | 影格率，決定動畫的流暢度 |
| 材質寬度 | 整數 | 512-8192 | 2048 | 單個材質集的最大寬度（像素） |
| 材質高度 | 整數 | 512-8192 | 2048 | 單個材質集的最大高度（像素） |
| 輸出格式 | 選項 | PNG/JPG | PNG | PNG 支援透明度，JPG 檔案較小 |
| 輸出品質 | 整數 | 1-31 | 5 | 數值越小品質越好（FFmpeg q:v 參數） |
| TinyPNG 壓縮 | 布林 | true/false | false | 是否使用 TinyPNG API 進行進階壓縮 |

**業務規則**:
1. 輸出名稱自動加上 `v2p_` 前綴，避免命名衝突
2. 如果影格數量超過單個材質集容量，自動分割為多個 plist
3. 輸出檔案命名格式：`v2p_{名稱}_{序號}.plist` 和 `v2p_{名稱}_{序號}.{格式}`
4. 臨時檔案自動清理，不佔用硬碟空間
5. 轉換失敗時保留錯誤日誌，方便問題排查

**效能要求**:
- 單個 5 秒 24fps 視頻的轉換時間 < 1 分鐘（1920x1080 解析度）
- 支援最長 60 秒的視頻
- 支援最高 60 fps 的影格率

#### 2.1.2 視頻預覽功能

**功能描述**: 在轉換前預覽上傳的視頻內容。

**實現方式**:
- 使用 WebView 介面的 HTML5 Video 元件
- 上傳後自動載入預覽
- 使用 FFmpeg 驗證視頻可讀性

**顯示資訊**:
- 視頻播放器（可播放/暫停）
- 不顯示詳細資訊（為了介面簡潔）

#### 2.1.3 參數配置功能

**功能描述**: 允許使用者配置工具和轉換參數。

**配置項**:

**工具路徑配置**（設定頁籤）:
- FFmpeg 執行檔路徑
- TexturePacker 執行檔路徑
- TinyPNG API 金鑰

**轉換參數配置**（主頁籤）:
- FPS（影格率）
- 材質大小限制
- 輸出格式選擇
- 輸出品質調整
- TinyPNG 壓縮開關

**偏好設定**:
- 主題（淺色/深色）
- 記住上次設定
- 自動清理舊檔案

**配置持久化**:
- 工具路徑保存在 `config.yaml`
- 使用者偏好保存在 `preferences.json`
- 每次啟動自動載入上次設定

#### 2.1.4 輸出管理功能

**功能描述**: 管理已轉換的動畫輸出。

**查看功能**（輸出頁籤）:
- 列出所有已轉換的動畫
- 顯示動畫元數據（FPS、影格數、尺寸、建立時間）
- 預覽 plist 內容

**管理功能**（管理頁籤）:
- 開啟輸出資料夾
- 清理超過指定天數的檔案
- 查看輸出目錄路徑

**輸出目錄結構**:
```
videos/
├── v2p_animation1/
│   ├── v2p_animation1_0.plist
│   ├── v2p_animation1_0.png
│   └── v2p_animation1_metadata.json
├── v2p_animation2/
│   ├── v2p_animation2_0.plist
│   ├── v2p_animation2_0.png
│   ├── v2p_animation2_1.plist
│   ├── v2p_animation2_1.png
│   └── v2p_animation2_metadata.json
```

#### 2.1.5 TinyPNG 壓縮整合

**功能描述**: 整合 TinyPNG API 進行高效圖像壓縮。

**支援格式**: PNG, JPG

**使用流程**:
1. 在設定頁籤配置 TinyPNG API 金鑰
2. 在轉換頁籤勾選「使用 TinyPNG 壓縮」
3. 轉換完成後自動壓縮生成的圖片

**壓縮效果**:
- PNG 通常可壓縮 60-80%
- JPG 通常可壓縮 40-60%
- 視覺品質幾乎無損

**錯誤處理**:
- API 金鑰無效時顯示明確錯誤訊息
- 網路連接失敗時記錄日誌但不中斷流程
- 壓縮失敗時使用原始檔案

**API 配額管理**:
- 免費版 TinyPNG 每月 500 張圖片
- 工具會記錄壓縮數量
- 超過配額時顯示提示

### 2.2 輔助功能

#### 2.2.1 日誌系統

**功能描述**: 記錄工具運行日誌，方便問題排查。

**日誌級別**:
- DEBUG: 詳細除錯資訊
- INFO: 一般操作資訊
- WARNING: 警告訊息
- ERROR: 錯誤訊息

**日誌檔案**:
- 位置: `log/v2p_YYYYMMDD.log`
- 格式: 按日期分割
- 編碼: UTF-8
- 保留: 建議定期清理舊日誌

**命令列選項**:
```bash
v2p.exe --log-level DEBUG  # 詳細日誌
v2p.exe --log-level INFO   # 一般日誌（預設）
```

#### 2.2.2 錯誤處理

**錯誤類型**:
1. **ConfigError**: 配置錯誤
   - FFmpeg 路徑無效
   - TexturePacker 路徑無效
   - API 金鑰驗證失敗

2. **FileError**: 文件錯誤
   - 找不到輸入檔案
   - 輸出目錄無法創建
   - 檔案讀寫權限不足

3. **ConversionError**: 轉換錯誤
   - FFmpeg 執行失敗
   - TexturePacker 打包失敗
   - 影格提取失敗

**錯誤顯示**:
- UI 中顯示友好的錯誤訊息（繁體中文）
- 日誌中記錄詳細的錯誤資訊（含堆疊）
- 提供可能的解決方案提示

#### 2.2.3 命令列介面

**啟動選項**:
```bash
v2p.exe [選項]

選項:
  -h, --help            顯示說明訊息
  -v, --version         顯示版本資訊
  --log-level LEVEL     設置日誌記錄級別
  --debug               啟用 WebView 開發者工具
```

**範例**:
```bash
# 使用 DEBUG 級別日誌啟動
v2p.exe --log-level DEBUG

# 啟用開發者工具（方便除錯）
v2p.exe --debug
```

### 2.3 Lua 整合

#### 2.3.1 AnimationLoader 模組

**功能描述**: 提供完整的 Lua 腳本，用於在 Cocos2d-x 項目中載入和播放動畫。

**主要 API**:

```lua
-- 設定動畫資源基礎路徑
AnimationLoader.setBasePath(path)

-- 創建動畫精靈（完整功能）
AnimationLoader.createAnimatedSprite(
    name,          -- 動畫名稱
    fps,           -- 幀率（可選，從 metadata 讀取）
    width,         -- 縮放寬度（可選）
    height,        -- 縮放高度（可選）
    loop,          -- 是否循環（預設 true）
    pingpong,      -- 是否反覆播放（預設 false）
    playInterval   -- 播放間隔（可選）
)

-- 創建動畫物件
AnimationLoader.createAnimation(name, fps)

-- 獲取動畫資訊
AnimationLoader.getAnimationInfo(name)

-- 快取管理
AnimationLoader.clearCache()
AnimationLoader.unloadAnimation(name)
AnimationLoader.releaseUnusedResources()

-- 預載
AnimationLoader.preloadAnimations()
AnimationLoader.getLoadedAnimations()
```

**使用範例**:
```lua
-- 初始化
local loader = require("InannaLua/Tools/AnimationLoader")
loader.setBasePath("InannaResource/Inanna/videos")

-- 創建動畫
local sprite = loader.createAnimatedSprite("my_animation", 30, 200, 200, true)
if sprite then
    self:addChild(sprite)
end

-- 清理
loader.clearCache()
```

#### 2.3.2 Metadata 支援

**Metadata 格式**:
```json
{
    "name": "v2p_animation",
    "fps": 30,
    "frame_count": 60,
    "plist_count": 2,
    "max_width": 2048,
    "max_height": 2048,
    "creation_time": "2025-10-09 15:30:00",
    "tool_version": "1.0.4",
    "output_format": "PNG",
    "quality": 5
}
```

**用途**:
- AnimationLoader 自動讀取 FPS
- 記錄轉換參數供後續參考
- 版本相容性檢查

---

## 三、技術需求

### 3.1 系統架構

**分層架構**:
```
┌─────────────────────────────────────────┐
│         主程式層 (v2p.py)                │
│    啟動、初始化、命令列參數              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│            UI 管理層                      │
│    WebView 介面、事件處理                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│            核心業務層                     │
│    視頻處理、配置管理、異常處理          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│          外部工具層                       │
│    FFmpeg、TexturePacker、TinyPNG       │
└─────────────────────────────────────────┘
```

**核心模組**:
- `core/video.py`: 視頻處理邏輯
- `core/config.py`: 配置管理
- `core/file_utils.py`: 文件工具
- `core/logger.py`: 日誌系統
- `core/exceptions/`: 異常定義
- `ui/webview/`: WebView UI 管理器
- `ui/runtime.py`: UI 啟動邏輯

### 3.2 技術選型

**開發語言**: Python 3.8+

**核心依賴**:
- **pywebview 5.0.0+**: WebView 桌面 UI 框架
- **PyYAML 6.0.1**: 配置檔案解析
- **Pillow 11.1.0**: 圖像處理
- **tinify**: TinyPNG API 客戶端
- **packaging 23.2**: 版本管理

**外部工具**:
- **FFmpeg**: 視頻解碼和影格提取
  - 命令: `-i input.mp4 -vf fps=24 -frame_pts 1 -q:v 5 output_%d.png`
  - 支援多種視頻格式
  - 高效能批次處理

- **TexturePacker**: 材質集打包
  - 格式: Cocos2d-x plist
  - 演算法: MaxRects（最優矩形打包）
  - 支援多材質集分割

- **TinyPNG API**: 圖像壓縮
  - 支援 PNG 和 JPG
  - 智能有損壓縮
  - 視覺品質保持

### 3.3 資料流程

**轉換流程**:
```
1. 使用者上傳 MP4
   ↓
2. UI 收集參數
   ↓
3. ConfigManager 提供工具路徑
   ↓
4. process_video() 協調處理
   ↓
5. extract_frames() - FFmpeg 提取影格到 temp/
   ↓
6. TexturePacker 打包到 videos/v2p_{name}/
   ↓
7. [可選] TinyPNG 壓縮圖片
   ↓
8. save_metadata() 保存元數據
   ↓
9. 清理 temp/ 臨時檔案
   ↓
10. UI 顯示完成訊息
```

**配置流程**:
```
啟動時:
  config.yaml → ConfigManager → 記憶體

使用者修改:
  UI 輸入 → 驗證 → ConfigManager → config.yaml

偏好設定:
  preferences.json ↔ ConfigManager ↔ UI
```

### 3.4 檔案結構

```
V2P/
├── Tool/
│   ├── v2p.py                      # 主程式入口
│   ├── version.py                  # 版本資訊
│   ├── config.yaml                 # 工具配置
│   ├── preferences.json            # 使用者偏好
│   ├── requirements.txt            # Python 依賴
│   ├── v2p.spec                    # PyInstaller 配置
│   │
│   ├── core/                       # 核心模組
│   │   ├── __init__.py
│   │   ├── config.py               # 配置管理
│   │   ├── video.py                # 視頻處理
│   │   ├── file_utils.py           # 文件工具
│   │   ├── logger.py               # 日誌系統
│   │   ├── error_handler.py        # 錯誤處理
│   │   └── exceptions/             # 異常定義
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── conversion.py
│   │       └── file.py
│   │
│   ├── ui/                         # UI 模組
│   │   ├── __init__.py
│   │   ├── manager.py              # UI 管理器
│   │   ├── styles.py               # 樣式定義
│   │   ├── components/             # UI 元件
│   │   │   ├── __init__.py
│   │   │   └── tk_file_picker.py
│   │   └── tabs/                   # 功能頁籤
│   │       ├── __init__.py
│   │       ├── main_tab.py         # 轉換頁籤
│   │       ├── settings_tab.py     # 設定頁籤
│   │       ├── output_tab.py       # 輸出頁籤
│   │       └── manage_tab.py       # 管理頁籤
│   │
│   ├── ffmpeg/                     # FFmpeg 執行檔
│   │   └── ffmpeg.exe
│   ├── log/                        # 日誌檔案
│   │   └── v2p_YYYYMMDD.log
│   ├── temp/                       # 臨時檔案（自動清理）
│   └── videos/                     # 輸出目錄
│       └── v2p_{name}/
│           ├── v2p_{name}_0.plist
│           ├── v2p_{name}_0.png
│           └── v2p_{name}_metadata.json
│
├── Lua/                            # Lua 模組
│   ├── AnimationLoader.lua         # 動畫加載器
│   ├── AnimationLoader_使用指南.md
│   ├── DefineExample.lua
│   └── FunctionExample.lua
│
├── docs/                           # 文檔
│   ├── PRD.md                      # 產品需求文檔
│   └── FEATURES.md                 # 功能說明文檔
│
└── .cursor/                        # Cursor Rules
    └── rules/
        ├── v2p-overview.mdc
        ├── v2p-architecture.mdc
        └── v2p-coding-standards.mdc
```

### 3.5 效能要求

**轉換效能**:
- 5 秒 24fps 1920x1080 視頻 < 1 分鐘
- 10 秒 30fps 1280x720 視頻 < 1.5 分鐘
- 支援最長 60 秒視頻

**UI 回應**:
- 介面啟動時間 < 5 秒
- 參數調整即時回應 < 100ms
- 預覽載入 < 2 秒

**資源佔用**:
- 記憶體峰值 < 500MB（不含外部工具）
- 臨時檔案自動清理
- 日誌檔案輪替（按日期分割）

### 3.6 相容性要求

**作業系統**:
- Windows 10/11（主要支援）
- 理論支援 macOS 和 Linux（未完整測試）

**Python 版本**:
- 最低要求: Python 3.8
- 建議版本: Python 3.10+
- 最高測試版本: Python 3.12

**外部工具版本**:
- FFmpeg 4.0+
- TexturePacker 5.0+

**瀏覽器**:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

---

## 四、使用流程

### 4.1 初次設定流程

```
1. 使用者啟動 v2p.exe
   ↓
2. 程式自動開啟瀏覽器（http://127.0.0.1:7866）
   ↓
3. 如果 config.yaml 不存在，停留在「設定」頁籤
   ↓
4. 使用者設定 FFmpeg 路徑（工具內建或自訂）
   ↓
5. 使用者設定 TexturePacker 路徑
   ↓
6. [可選] 設定 TinyPNG API 金鑰
   ↓
7. 點擊「測試並保存設定」
   ↓
8. 測試通過後，自動切換到「轉換」頁籤
```

**首次設定注意事項**:
- FFmpeg 需要先解壓縮 `ffmpeg.7z`
- TexturePacker 需要購買授權並安裝
- TinyPNG API 金鑰可從 https://tinypng.com/developers 獲取（免費版每月 500 張）

### 4.2 視頻轉換流程

```
1. 在「轉換」頁籤點擊上傳 MP4 檔案
   ↓
2. 預覽視頻內容（確認是否正確）
   ↓
3. [可選] 調整參數：
   - FPS（影格率）
   - 材質大小
   - 輸出格式（PNG/JPG）
   - 輸出品質
   - TinyPNG 壓縮開關
   ↓
4. 輸入輸出名稱（例如：walk_animation）
   ↓
5. 查看預訂輸出路徑
   ↓
6. 點擊「開始轉換」
   ↓
7. 等待處理（顯示進度）
   ↓
8. 轉換完成，顯示成功訊息
   ↓
9. 在「輸出」頁籤查看結果
```

**參數建議**:
- **角色動畫**: FPS 24-30，材質 2048x2048，PNG 格式
- **UI 特效**: FPS 30-60，材質 1024x1024，PNG 格式
- **場景動畫**: FPS 24，材質 2048x2048，JPG 格式（無需透明度）

### 4.3 Cocos2d-x 整合流程

**步驟 1: 複製檔案**
```
將 videos/v2p_{name}/ 目錄複製到 Cocos2d-x 項目的資源目錄
例如：InannaResource/Inanna/videos/v2p_walk_animation/
```

**步驟 2: 整合 AnimationLoader**
```lua
-- 將 AnimationLoader.lua 複製到項目的 Lua 目錄
-- 例如：InannaLua/Tools/AnimationLoader.lua
```

**步驟 3: 初始化**
```lua
-- 在需要使用動畫的場景中初始化
self.animationManager = {
    loader = require("InannaLua/Tools/AnimationLoader"),
    activeAnimations = {},
}
self.animationManager.loader.setBasePath("InannaResource/Inanna/videos")
```

**步驟 4: 創建動畫**
```lua
-- 創建動畫精靈
local sprite = self.animationManager.loader.createAnimatedSprite(
    "walk_animation",  -- 動畫名稱（不含 v2p_ 前綴）
    30,                -- FPS（可選，會從 metadata 讀取）
    200,               -- 縮放寬度（可選）
    200,               -- 縮放高度（可選）
    true               -- 循環播放
)

if sprite then
    self:addChild(sprite)
    self.animationManager.activeAnimations["walk"] = sprite
end
```

**步驟 5: 清理資源**
```lua
-- 在場景結束時清理
if self.animationManager then
    for name, anim in pairs(self.animationManager.activeAnimations) do
        anim:stop()
        if anim:getParent() then
            anim:removeFromParent()
        end
    end
    self.animationManager.loader.clearCache()
    self.animationManager = nil
end
```

---

## 五、非功能需求

### 5.1 可用性

- **易用性**: 非技術人員也能快速上手
- **一致性**: UI 風格統一，操作邏輯一致
- **回饋**: 每個操作都有明確的回饋訊息
- **容錯**: 參數驗證，防止錯誤操作

### 5.2 可靠性

- **錯誤處理**: 完整的異常捕獲和處理
- **日誌記錄**: 詳細的操作日誌便於問題排查
- **資料完整性**: 轉換失敗不留殘留檔案
- **版本相容**: 檢查工具版本相容性

### 5.3 可維護性

- **模組化設計**: 職責分離，易於擴展
- **文檔完整**: 程式碼註釋和使用文檔
- **日誌系統**: 便於追蹤和除錯
- **版本管理**: 語義化版本號

### 5.4 安全性

- **輸入驗證**: 驗證所有使用者輸入
- **路徑檢查**: 防止路徑遍歷攻擊
- **API 金鑰**: 安全儲存在本地配置
- **臨時檔案**: 自動清理，不洩露資訊

### 5.5 效能

- **回應時間**: UI 操作即時回應
- **處理效率**: 充分利用 CPU 和記憶體
- **資源清理**: 及時釋放不再使用的資源
- **批次最佳化**: 未來支援批量處理

---

## 六、未來規劃

### 6.1 短期計劃（v1.1.x）

**批量處理**:
- 支援一次上傳多個 MP4 檔案
- 批量套用相同參數轉換
- 顯示批次處理進度

**預覽增強**:
- 顯示視頻詳細資訊（解析度、時長、FPS）
- 影格預覽（顯示關鍵影格）
- 轉換前估算輸出大小

**參數預設集**:
- 保存常用參數組合
- 快速套用預設集
- 分享預設集給團隊

### 6.2 中期計劃（v1.2.x）

**更多輸出格式**:
- Spine JSON 格式
- DragonBones JSON 格式
- GIF 動圖格式

**視頻編輯**:
- 裁切視頻片段
- 調整播放速度
- 添加濾鏡效果

**雲端整合**:
- 支援從雲端儲存載入視頻
- 輸出直接上傳到雲端
- 團隊協作功能

### 6.3 長期計劃（v2.0.x）

**跨平台支援**:
- macOS 原生應用
- Linux 支援
- Web 版本（無需安裝）

**AI 輔助**:
- 自動推薦最佳參數
- 智能裁切和對齊
- 自動生成動畫變體

**插件系統**:
- 支援第三方插件
- 自訂處理流程
- 社群插件市場

---

## 七、成功指標

### 7.1 產品指標

- **使用者數量**: 獲得 100+ 活躍使用者
- **轉換成功率**: > 95%
- **使用者滿意度**: 平均評分 > 4.5/5
- **問題解決率**: 已知問題 < 5 個

### 7.2 效能指標

- **轉換速度**: 平均 1 秒視頻轉換時間 < 15 秒
- **崩潰率**: < 0.1%
- **記憶體洩漏**: 無
- **CPU 使用率**: 峰值 < 80%

### 7.3 業務指標

- **文檔完整度**: 100% 功能有文檔
- **程式碼覆蓋率**: > 70%（未來目標）
- **發布頻率**: 每月至少一個修復版本
- **回應時間**: 問題回報 24 小時內回應

---

## 八、風險與挑戰

### 8.1 技術風險

| 風險 | 影響 | 機率 | 應對策略 |
|------|------|------|----------|
| FFmpeg 版本不相容 | 高 | 中 | 內建特定版本，提供相容性檢查 |
| TexturePacker 授權問題 | 高 | 低 | 明確說明需要購買授權 |
| TinyPNG API 配額限制 | 中 | 高 | 提供開關選項，顯示使用量提示 |
| 大檔案處理失敗 | 中 | 中 | 限制檔案大小，優化記憶體使用 |

### 8.2 使用者體驗風險

| 風險 | 影響 | 機率 | 應對策略 |
|------|------|------|----------|
| 初次設定複雜 | 中 | 高 | 提供詳細的設定引導和預設值 |
| 參數選擇困難 | 中 | 中 | 提供推薦值和詳細說明 |
| 錯誤訊息不清楚 | 低 | 中 | 使用繁體中文和友好的錯誤提示 |
| 效能不符預期 | 高 | 低 | 明確說明效能要求和限制 |

### 8.3 維護風險

| 風險 | 影響 | 機率 | 應對策略 |
|------|------|------|----------|
| 依賴套件更新破壞相容性 | 高 | 中 | 鎖定套件版本，充分測試後才更新 |
| 缺乏測試覆蓋 | 中 | 高 | 逐步增加單元測試和整合測試 |
| 文檔過時 | 低 | 中 | 每次發布前更新文檔 |
| 社群支援不足 | 中 | 中 | 建立 FAQ 和使用案例庫 |

---

## 九、附錄

### 9.1 術語表

- **Plist**: Property List，Apple 的配置檔案格式，Cocos2d-x 用於描述材質集
- **材質集 (Texture Atlas)**: 將多個小圖合併成一張大圖，提高渲染效能
- **影格 (Frame)**: 視頻的單個畫面
- **FPS (Frames Per Second)**: 每秒影格數，決定動畫流暢度
- **TexturePacker**: 專業的材質集打包工具
- **FFmpeg**: 開源的視頻處理工具
- **TinyPNG**: 圖像壓縮服務

### 9.2 參考資料

- Cocos2d-x 官方文檔: https://docs.cocos2d-x.org/
- FFmpeg 文檔: https://ffmpeg.org/documentation.html
- TexturePacker 文檔: https://www.codeandweb.com/texturepacker/documentation
- TinyPNG API: https://tinypng.com/developers
- pywebview 文檔: https://pywebview.flowrl.com/

### 9.3 變更歷史

| 版本 | 日期 | 變更內容 |
|------|------|----------|
| 1.0.4 | 2025-03-26 | TinyPNG 壓縮功能、布林值儲存修正 |
| 1.0.3 | 2025-03-20 | 輸出格式選擇、品質調整、偏好設定 |
| 1.0.2 | 2025-03-03 | 修正 plist 影格名稱、調整介面 |
| 1.0.1 | 2025-02-20 | 架構重構、日誌系統完善 |
| 1.0.0 | 2025-02-19 | 首次發布 |

---

**文檔維護者**: V2P 開發團隊  
**最後審核**: 2025-10-09  
**下次審核**: 2025-11-09

