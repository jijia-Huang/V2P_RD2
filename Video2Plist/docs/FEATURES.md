# V2P 工具功能說明文檔

**版本**: 1.1.0  
**最後更新**: 2025-10-09

---

## 目錄

1. [視頻處理流程](#1-視頻處理流程)
2. [Frame 尺寸縮放功能](#2-frame-尺寸縮放功能) 🎉 **NEW**
3. [UI 組件架構](#3-ui-組件架構)
4. [配置管理系統](#4-配置管理系統)
5. [Lua 加載器使用](#5-lua-加載器使用)
6. [錯誤處理機制](#6-錯誤處理機制)
7. [日誌系統](#7-日誌系統)
8. [擴展與自訂](#8-擴展與自訂)

---

## 1. 視頻處理流程

### 1.1 整體流程

V2P 工具的視頻轉換流程分為以下階段：

```
輸入 → 驗證 → 影格提取 → 材質打包 → 壓縮 → 元數據保存 → 清理
```

### 1.2 詳細步驟

#### 步驟 1: 輸入驗證

**位置**: `core/video.py` 的 `process_video()` 函數開頭

**驗證項目**:
```python
# 檢查 MP4 檔案
if not mp4_file:
    raise FileError("請選擇 MP4 檔案")

# 檢查輸出名稱
if not output_name:
    raise ConfigError("請輸入輸出名稱")

# 驗證工具路徑
if not ffmpeg_path or not os.path.exists(ffmpeg_path):
    raise ConfigError("FFmpeg 路徑無效")
```

**自動處理**:
- 輸出名稱自動加上 `v2p_` 前綴
- 建立輸出目錄（如果不存在）
- 建立臨時目錄

#### 步驟 2: 影格提取

**位置**: `core/video.py` 的 `extract_frames()` 函數

**FFmpeg 命令構建**:
```python
cmd = [
    ffmpeg_path,
    "-i", video_path,           # 輸入檔案
    "-vf", f"fps={fps}",        # 設定 FPS
    "-frame_pts", "1",          # 使用影格時間戳作為檔名
    "-q:v", str(quality),       # 設定品質（1-31）
    "-y",                       # 覆蓋已存在的檔案
    output_path                 # 輸出路徑模式
]
```

**輸出格式**:
- PNG: 支援透明度，檔案較大
- JPG: 不支援透明度，檔案較小

**品質參數**:
- 1-5: 高品質（推薦）
- 6-10: 中品質
- 11-31: 低品質

**範例**:
```bash
# 從 video.mp4 提取 24fps 的影格，品質為 5，輸出為 PNG
ffmpeg -i video.mp4 -vf fps=24 -frame_pts 1 -q:v 5 -y output_%d.png
```

#### 步驟 3: 材質打包

**位置**: `core/video.py` 的 `process_video()` 函數（TexturePacker 調用）

**TexturePacker 參數**:
```python
tp_cmd = [
    texture_packer_path,
    "--data", "{output_name}_{n}.plist",     # 輸出 plist 檔名模式
    "--format", "cocos2d",                    # 輸出格式
    "--texture-format", output_format,        # PNG 或 JPG
    "--sheet", "{output_name}_{n}.png",      # 輸出材質集檔名模式
    "--max-width", str(max_width),           # 最大寬度
    "--max-height", str(max_height),         # 最大高度
    "--size-constraints", "POT",             # 大小約束（Power of Two）
    "--multipack",                           # 多材質集支援
    "--algorithm", "MaxRects",               # 打包演算法
    "--maxrects-heuristics", "Best",         # 最佳啟發式
    "--trim-mode", "None",                   # 不裁切透明邊緣
    "--opt", "RGBA8888",                     # 優化模式
    "--extrude", "0",                        # 不擴展像素
    "--disable-auto-alias",                  # 停用自動別名
    "--shape-padding", "0",                  # 形狀填充為 0
    "--border-padding", "0",                 # 邊界填充為 0
    "--disable-clean-transparency",          # 停用透明清理
    "--basic-sort-by", "Name",               # 按名稱排序
    frames_dir                               # 影格目錄
]
```

**打包策略**:
- **MaxRects 演算法**: 最優化的矩形打包，減少浪費空間
- **多材質集**: 如果影格數量超過單個材質集容量，自動分割
- **POT 約束**: 材質大小為 2 的冪次方（512, 1024, 2048...）
- **無填充**: 不添加額外的像素，節省空間

**輸出結果**:
```
v2p_animation_0.plist   # 第一個材質集描述檔
v2p_animation_0.png     # 第一個材質集圖片
v2p_animation_1.plist   # 第二個材質集描述檔（如果有）
v2p_animation_1.png     # 第二個材質集圖片（如果有）
```

#### 步驟 4: TinyPNG 壓縮（可選）

**位置**: `core/video.py` 的 `compress_png_with_tinypng()` 函數

**啟用條件**:
- 使用者勾選「使用 TinyPNG 壓縮」
- 已設定 TinyPNG API 金鑰

**壓縮流程**:
```python
# 設定 API 金鑰
tinify.key = api_key

# 壓縮檔案
source = tinify.from_file(image_path)
source.to_file(image_path)  # 覆蓋原檔案

# 計算壓縮率
compressed_size = os.path.getsize(image_path)
saved_percent = (original_size - compressed_size) / original_size * 100
```

**壓縮效果**:
- PNG: 通常壓縮 60-80%，視覺品質幾乎無損
- JPG: 通常壓縮 40-60%

**錯誤處理**:
- API 金鑰無效: 記錄錯誤，跳過壓縮
- 網路連接失敗: 記錄警告，使用原檔案
- 達到配額限制: 提示使用者

#### 步驟 5: 元數據保存

**位置**: `core/video.py` 的 `save_metadata()` 函數

**元數據內容**:
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
    "quality": 5,
    "use_tinypng": true,
    "compressed_count": 2
}
```

**用途**:
- AnimationLoader 自動讀取 FPS
- 記錄轉換參數供後續參考
- 版本相容性檢查
- 問題排查

#### 步驟 6: 臨時檔案清理

**位置**: `process_video()` 的 `finally` 區塊

**清理內容**:
```python
if temp_folder and os.path.exists(temp_folder):
    shutil.rmtree(temp_folder, ignore_errors=True)
    logging.info(f"清理臨時目錄：{temp_folder}")
```

**清理策略**:
- 無論轉換成功或失敗，都清理臨時檔案
- 使用 `ignore_errors=True` 避免清理失敗影響主流程
- 記錄清理操作到日誌

### 1.3 效能優化

**記憶體優化**:
- 使用串流處理，不一次載入整個視頻
- 及時清理臨時檔案
- FFmpeg 直接輸出到檔案，不經過記憶體

**速度優化**:
- FFmpeg 使用硬體加速（如果可用）
- TexturePacker 使用最快的打包演算法
- TinyPNG 壓縮使用異步處理（未來改進）

**錯誤恢復**:
- 每個步驟都有完整的錯誤處理
- 中間失敗不影響其他轉換任務
- 保留詳細日誌便於問題排查

---

## 2. Frame 尺寸縮放功能

### 2.1 功能概述

**版本**: v1.1.0 新增

Frame 尺寸縮放功能允許您在影格擷取時調整影片尺寸，減少處理時間和檔案大小。此功能特別適合：

- 🎮 **遊戲開發**: 將高解析度視頻縮小到遊戲所需的解析度
- 📱 **移動端優化**: 針對不同螢幕尺寸調整動畫
- 💾 **檔案壓縮**: 減少材質尺寸以節省空間
- 🎨 **特效處理**: 調整尺寸以適配特定畫面比例

### 2.2 功能參數

| 參數 | 類型 | 範圍 | 說明 |
|------|------|------|------|
| 啟用縮放 | Boolean | - | 是否啟用 Frame 尺寸縮放功能 |
| 鎖定長寬比 | Boolean | - | 鎖定後調整一個值會自動計算另一個 |
| 比例寬度 | Integer | 1-999 | 長寬比的寬度部分 |
| 比例高度 | Integer | 1-999 | 長寬比的高度部分 |
| Frame 寬度 | Integer | 1-8192 | 目標 Frame 寬度（像素） |
| Frame 高度 | Integer | 1-8192 | 目標 Frame 高度（像素） |
| 縮放模式 | Enum | 4 種 | 縮放模式（詳見下方） |

### 2.3 四種縮放模式

#### 模式 1: 拉伸變形

**FFmpeg 濾鏡**: `scale={width}:{height}`

**說明**: 直接將影片縮放到目標尺寸，不保持原始比例

**適用場景**:
- 已經匹配目標比例的影片
- 不在意變形的情況

**範例**:
```
原始: 1920x1080 (16:9)
目標: 512x512 (1:1)
結果: 影片會被壓扁（16:9 → 1:1）
```

**FFmpeg 命令**:
```bash
ffmpeg -i input.mp4 -vf "fps=24,scale=512:512" output_%d.png
```

#### 模式 2: 裁切中心

**FFmpeg 濾鏡**: `scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}`

**說明**: 保持原始比例，放大到至少填滿目標尺寸，然後裁切多餘部分

**適用場景**:
- 需要保持畫面比例
- 可接受部分內容被裁切

**範例**:
```
原始: 1920x1080 (16:9)
目標: 512x512 (1:1)
過程: 縮放到 910x512 → 裁切左右各 199px → 512x512
結果: 中央部分保留，左右被裁切
```

**視覺示意**:
```
[===========]  原始 16:9
  [======]    裁切後 1:1（保留中央）
```

#### 模式 3: 填充黑邊

**FFmpeg 濾鏡**: `scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black`

**說明**: 保持原始比例，縮小到適合目標尺寸，填充黑色邊框

**適用場景**:
- 需要保持完整畫面
- 可接受黑邊

**範例**:
```
原始: 1920x1080 (16:9)
目標: 512x512 (1:1)
過程: 縮放到 512x288 → 填充上下各 112px 黑邊 → 512x512
結果: 完整內容，上下有黑邊
```

**視覺示意**:
```
████████████  黑邊
[==========]  原始內容
████████████  黑邊
```

#### 模式 4: 填充透明邊

**FFmpeg 濾鏡**: `scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black@0`

**說明**: 與黑邊模式相同，但填充透明色（僅 PNG 支援）

**適用場景**:
- 需要透明背景
- 使用 PNG 格式輸出

**限制**:
- ⚠️ **僅支援 PNG 格式**
- 如果選擇 JPG 格式，會自動降級為黑邊模式並記錄警告

**範例**:
```python
# 在日誌中會看到：
logging.warning("JPG 格式不支援透明邊，自動降級為黑邊模式")
```

### 2.4 長寬比鎖定

當啟用「鎖定長寬比」時：

1. **調整寬度** → 自動計算高度
   ```python
   new_height = int(width * aspect_h / aspect_w)
   # 範例: width=1920, 比例=16:9
   # new_height = 1920 * 9 / 16 = 1080
   ```

2. **調整高度** → 自動計算寬度
   ```python
   new_width = int(height * aspect_w / aspect_h)
   # 範例: height=1080, 比例=16:9
   # new_width = 1080 * 16 / 9 = 1920
   ```

3. **修改比例** → 重新計算高度
   - 比例改變時，以當前寬度為基準重新計算高度

### 2.5 快速比例選擇

工具提供 5 個快速比例按鈕：

| 按鈕 | 比例 | 適用場景 |
|------|------|---------|
| 1:1 | 1:1 | 正方形動畫（頭像、圖標等） |
| 16:9 | 16:9 | 標準寬屏（現代影片、遊戲） |
| 9:16 | 9:16 | 直式影片（手機、直播） |
| 4:3 | 4:3 | 傳統螢幕比例 |
| 原始 | 動態 | 使用影片原始比例 |

**「原始」按鈕行為**:
1. 讀取影片實際尺寸（使用 `get_video_dimensions()`）
2. 計算最簡比例（使用 GCD）
3. 設定比例和尺寸

**範例**:
```python
# 影片: 1920x1080
原始尺寸 = 1920x1080
GCD = 120
簡化比例 = (1920/120) : (1080/120) = 16:9
```

### 2.6 UI 操作流程

#### 基本操作

1. **上傳影片**
   - 系統自動讀取原始尺寸
   - 顯示提示：`ⓘ 原始尺寸：1920x1080`

2. **啟用縮放**
   - 勾選「啟用 Frame 尺寸縮放」
   - 所有子選項變為可用

3. **設定尺寸**
   - 方式 A: 使用快速按鈕選擇比例
   - 方式 B: 手動調整比例數值
   - 方式 C: 直接拖動寬度/高度 Slider

4. **選擇模式**
   - 根據需求選擇 4 種縮放模式之一

5. **開始轉換**
   - 點擊「開始轉換」
   - 系統保存偏好設定

#### 實際範例

**場景 1: 將 1080p 影片縮小到 512x288**

```
1. 上傳影片 → 顯示「原始尺寸：1920x1080」
2. 勾選「啟用 Frame 尺寸縮放」
3. 點擊「16:9」快速按鈕 → 設定比例 16:9
4. 拖動寬度 Slider 到 512 → 高度自動變為 288
5. 選擇「拉伸變形」模式
6. 轉換
```

**場景 2: 將橫向影片轉為正方形（裁切）**

```
1. 上傳 1920x1080 影片
2. 啟用縮放
3. 點擊「1:1」→ 比例設為 1:1
4. 設定寬度 1080 → 高度自動 1080
5. 選擇「裁切中心」模式
6. 轉換 → 左右各被裁切 420px
```

**場景 3: 保持完整畫面，添加透明邊**

```
1. 上傳 1920x1080 影片
2. 啟用縮放
3. 點擊「1:1」→ 1080x1080
4. 選擇「填充透明邊」模式
5. 確保輸出格式為 PNG
6. 轉換 → 上下添加透明邊
```

### 2.7 技術實現

#### 核心函數

**1. `get_video_dimensions()`** - 獲取影片尺寸

```python
def get_video_dimensions(video_path, ffmpeg_path):
    """獲取影片原始尺寸"""
    # 優先使用 ffprobe
    cmd = [ffprobe_path, "-v", "error", 
           "-select_streams", "v:0",
           "-show_entries", "stream=width,height",
           "-of", "csv=s=x:p=0", video_path]
    
    # 解析輸出: "1920x1080"
    return (width, height)
```

**2. `extract_frames()` - 擴展參數**

新增參數:
```python
def extract_frames(..., 
                  enable_resize=False, 
                  target_width=None, 
                  target_height=None, 
                  resize_mode="stretch"):
```

濾鏡組合邏輯:
```python
filters = [f"fps={fps}"]

if enable_resize:
    if resize_mode == "stretch":
        filters.append(f"scale={target_width}:{target_height}")
    elif resize_mode == "crop":
        filters.append(f"scale=...:force_original_aspect_ratio=increase")
        filters.append(f"crop={target_width}:{target_height}")
    # ... 其他模式
    
filter_str = ",".join(filters)
```

**3. Metadata 擴展**

新增欄位:
```json
{
  "original_size": "1920x1080",
  "frame_resize_enabled": true,
  "frame_size": "512x288",
  "resize_mode": "stretch"
}
```

### 2.8 性能考量

#### 處理時間

| 原始尺寸 | 目標尺寸 | 相對處理時間 |
|---------|---------|-----------|
| 1920x1080 | 1920x1080 | 1.0x (基準) |
| 1920x1080 | 1280x720 | 0.8x |
| 1920x1080 | 512x288 | 0.4x |
| 3840x2160 | 1920x1080 | 1.2x |

**結論**: 縮小尺寸可顯著減少處理時間

#### 檔案大小

| 尺寸 | PNG (單幀) | JPG (單幀) | 100 幀材質 |
|------|-----------|-----------|-----------|
| 1920x1080 | ~500KB | ~150KB | ~15MB |
| 1280x720 | ~300KB | ~90KB | ~9MB |
| 512x288 | ~80KB | ~25KB | ~2.5MB |

**注意事項**:
- 尺寸超過 4096 會顯著增加處理時間
- 系統會在日誌中發出警告：
  ```python
  logging.warning(f"目標尺寸 {width}x{height} 較大，處理時間可能較長")
  ```

### 2.9 常見問題 (FAQ)

#### Q1: 為什麼選擇透明邊模式後還是黑邊？

**A**: 檢查輸出格式是否為 PNG。JPG 不支援透明度，會自動降級為黑邊模式。

查看日誌確認:
```
WARNING - JPG 格式不支援透明邊，自動降級為黑邊模式
```

#### Q2: 鎖定長寬比後如何同時調整？

**A**: 解除鎖定即可獨立調整寬度和高度。

#### Q3: 快速按鈕「原始」無反應？

**A**: 請先上傳影片。「原始」按鈕需要讀取影片尺寸才能計算比例。

#### Q4: 縮放後畫質變差？

**A**: 嘗試調整「輸出品質」參數（1-31，數值越小品質越好）。

#### Q5: 如何批次處理多個相同比例的影片？

**A**: 系統會自動保存您的縮放設定（比例、尺寸、模式），下次打開會自動載入。

### 2.10 最佳實踐

#### 建議 1: 根據用途選擇模式

| 用途 | 推薦模式 | 原因 |
|------|---------|------|
| 遊戲角色動畫 | 拉伸變形 | 通常已經正確比例 |
| 背景循環動畫 | 裁切中心 | 保持畫面豐富度 |
| UI 圖標動畫 | 填充透明邊 | 需要透明背景 |
| 全螢幕特效 | 填充黑邊 | 保持完整畫面 |

#### 建議 2: 尺寸選擇

- **2K 設備**: 縮小到 1920x1080
- **1080p 設備**: 縮小到 1280x720
- **移動端**: 縮小到 512x288 或更小
- **UI 元素**: 256x256 或 512x512

#### 建議 3: 格式選擇

- **需要透明**: 使用 PNG + 填充透明邊
- **檔案優先**: 使用 JPG + 適當品質
- **品質優先**: 使用 PNG + 低品質值（1-5）

---

## 3. UI 組件架構

### 3.1 整體架構

V2P 使用 Gradio 框架構建 Web 介面，採用模組化設計：

```
UIManager
├── Settings Tab (設定頁籤)
├── Main Tab (轉換頁籤)
├── Output Tab (輸出頁籤)
└── Manage Tab (管理頁籤)
```

### 2.2 UIManager 類別

**位置**: `ui/manager.py`

**職責**:
- 建立和管理所有 UI 元件
- 處理頁面載入事件
- 管理元件狀態更新
- 整合各個功能頁籤

**初始化流程**:
```python
class UIManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config_manager.ui_manager = self  # 雙向引用
        self.components = {}
    
    def create_ui(self):
        with gr.Blocks(css=CSS, theme=gr.themes.Soft()) as demo:
            # 建立標題
            gr.Markdown("# 🎬 V2P 工具")
            
            # 建立頁籤
            with gr.Tabs() as tabs:
                settings_components = create_settings_tab(config_manager)
                main_components = create_main_tab(config_manager)
                output_components = create_output_tab(config_manager)
                manage_components = create_manage_tab(config_manager)
            
            # 儲存元件引用
            self.components.update(settings_components)
            self.components.update(main_components)
            # ...
        
        return demo
```

**元件管理**:
```python
def get_component(self, name):
    """獲取 UI 元件"""
    return self.components.get(name)

def update_component(self, name, value):
    """更新 UI 元件值"""
    component = self.get_component(name)
    if component:
        component.update(value=value)
```

### 2.3 設定頁籤

**位置**: `ui/tabs/settings_tab.py`

**元件**:
```python
with gr.Tab("⚙️ 設定", id=0):
    # FFmpeg 路徑
    ffmpeg_path = gr.Textbox(label="FFmpeg 路徑")
    ffmpeg_browse = gr.Button("瀏覽")
    
    # TexturePacker 路徑
    tp_path = gr.Textbox(label="TexturePacker 路徑")
    tp_browse = gr.Button("瀏覽")
    
    # TinyPNG API 金鑰
    tinypng_key = gr.Textbox(label="TinyPNG API 金鑰", type="password")
    
    # 保存按鈕
    save_button = gr.Button("測試並保存設定", variant="primary")
    result = gr.Markdown()
```

**事件處理**:
```python
def on_save_click(ffmpeg, tp, tinypng_key):
    try:
        # 測試工具可用性
        config_manager.test_executable(ffmpeg, "FFmpeg")
        config_manager.test_executable(tp, "TexturePacker")
        
        # 保存配置
        return config_manager.save_config(ffmpeg, tp, tinypng_key)
    except Exception as e:
        return handle_error(e, ui_component=True)

save_button.click(
    on_save_click,
    inputs=[ffmpeg_path, tp_path, tinypng_key],
    outputs=[result]
)
```

### 2.4 轉換頁籤

**位置**: `ui/tabs/main_tab.py`

**主要區域**:

**上傳區域**:
```python
mp4_file = gr.File(
    label="上傳 MP4 檔案",
    file_types=[".mp4"],
    height=100
)
```

**參數區域**:
```python
with gr.Accordion("進階設定", open=False):
    fps_slider = gr.Slider(1, 60, value=24, label="FPS")
    format_dropdown = gr.Dropdown(["PNG", "JPG"], label="輸出格式")
    quality_slider = gr.Slider(1, 31, value=5, label="輸出品質")
    max_width_slider = gr.Slider(512, 8192, value=2048, step=512)
    max_height_slider = gr.Slider(512, 8192, value=2048, step=512)
    use_tinypng = gr.Checkbox(label="使用 TinyPNG 壓縮")
```

**預覽區域**:
```python
preview_video = gr.Video(
    label="影片預覽",
    show_download_button=False,
    include_audio=False,
    height="500px"
)
```

**輸出設定**:
```python
output_name = gr.Textbox(
    label="輸出名稱",
    placeholder="例如：walk_animation"
)
output_path_display = gr.Textbox(
    interactive=False,
    label="預訂輸出路徑"
)
```

**事件綁定**:
```python
# 上傳後更新預覽
mp4_file.change(update_preview, inputs=[mp4_file], outputs=[preview_video])

# 輸出名稱改變時更新路徑顯示
output_name.change(update_output_path, inputs=[output_name], outputs=[output_path_display])

# 點擊轉換按鈕
process_button.click(
    on_convert_click,
    inputs=[mp4_file, fps_slider, output_name, ...],
    outputs=[result_output]
)
```

### 2.5 輸出頁籤

**位置**: `ui/tabs/output_tab.py`

**功能**:
- 列出所有已轉換的動畫
- 顯示動畫元數據
- 預覽 plist 內容

### 2.6 管理頁籤

**位置**: `ui/tabs/manage_tab.py`

**功能**:
- 開啟輸出資料夾
- 清理超過指定天數的檔案
- 查看工具版本資訊

### 2.7 樣式系統

**位置**: `ui/styles.py`

**自訂 CSS**:
```python
CSS = """
/* 結果顯示區域 */
.result-display {
    padding: 10px;
    border-radius: 5px;
    background-color: #f0f0f0;
}

/* 按鈕樣式 */
.primary-button {
    background-color: #007bff;
    color: white;
}

/* ... 更多樣式 */
"""
```

---

## 4. 配置管理系統

### 3.1 ConfigManager 類別

**位置**: `core/config.py`

**配置檔案**:
- `config.yaml`: 工具路徑配置
- `preferences.json`: 使用者偏好設定

### 3.2 配置載入流程

```python
class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.preferences = {}
        self.load_config()
        self.load_preferences()
    
    def load_config(self):
        """載入 YAML 配置"""
        config_path = os.path.join(get_application_path(), "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                saved_config = yaml.safe_load(f)
                self.config.update(saved_config)
    
    def load_preferences(self):
        """載入 JSON 偏好設定"""
        prefs_file = os.path.join(get_application_path(), "preferences.json")
        if os.path.exists(prefs_file):
            with open(prefs_file, "r", encoding="utf-8") as f:
                self.preferences = json.load(f)
```

### 3.3 配置保存

```python
def save_config(self, ffmpeg_path, texture_packer_path, tinypng_api_key):
    """儲存工具配置"""
    # 驗證路徑
    if not os.path.exists(ffmpeg_path):
        raise ConfigError("FFmpeg 路徑無效")
    
    # 更新配置
    self.config.update({
        "ffmpeg_path": ffmpeg_path,
        "texture_packer_path": texture_packer_path,
        "tinypng_api_key": tinypng_api_key
    })
    
    # 保存到檔案
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(self.config, f, allow_unicode=True)

def save_preferences(self, prefs):
    """儲存使用者偏好"""
    self.preferences.update(prefs)
    with open(prefs_file, "w", encoding="utf-8") as f:
        json.dump(self.preferences, f, indent=2, ensure_ascii=False)
```

### 3.4 偏好設定項目

```python
{
    "last_version": "1.0.4",
    "theme": "light",
    "last_fps": 24,
    "last_max_width": 2048,
    "last_max_height": 2048,
    "last_format": "PNG",
    "last_quality": 5,
    "last_use_tinypng": false,
    "remember_settings": true,
    "auto_clean": true
}
```

---

## 5. Lua 加載器使用

### 4.1 AnimationLoader 架構

**位置**: `Lua/AnimationLoader.lua`

**核心功能**:
- 載入 plist 材質集
- 創建 Cocos2d-x 動畫精靈
- 管理動畫快取
- 預載和資源釋放

### 4.2 初始化

```lua
-- 在場景或管理器中初始化
self.animationManager = {
    loader = require("InannaLua/Tools/AnimationLoader"),
    activeAnimations = {},
}

-- 設定動畫資源基礎路徑
self.animationManager.loader.setBasePath("InannaResource/Inanna/videos")
```

### 4.3 創建動畫

**簡單用法**:
```lua
local sprite = self.animationManager.loader.createAnimatedSprite("walk_animation")
self:addChild(sprite)
```

**完整參數**:
```lua
local sprite = self.animationManager.loader.createAnimatedSprite(
    "walk_animation",  -- 動畫名稱（不含 v2p_ 前綴）
    30,                -- FPS（可選，從 metadata 讀取）
    200,               -- 縮放寬度（可選）
    200,               -- 縮放高度（可選）
    true,              -- 循環播放（預設 true）
    false,             -- 反覆播放（預設 false）
    nil                -- 播放間隔（可選）
)
```

### 4.4 管理動畫

**追蹤活躍動畫**:
```lua
if sprite then
    self.animationManager.activeAnimations["walk"] = sprite
    self:addChild(sprite)
end
```

**停止和移除**:
```lua
local anim = self.animationManager.activeAnimations["walk"]
if anim then
    anim:stop()
    if anim:getParent() then
        anim:removeFromParent()
    end
    self.animationManager.activeAnimations["walk"] = nil
end
```

### 4.5 資源管理

**清除快取**:
```lua
-- 清除所有快取的動畫
self.animationManager.loader.clearCache()
```

**卸載特定動畫**:
```lua
-- 卸載單個動畫資源
self.animationManager.loader.unloadAnimation("walk_animation")
```

**釋放未使用資源**:
```lua
-- 釋放不再使用的材質
self.animationManager.loader.releaseUnusedResources()
```

### 4.6 預載

**預載所有動畫**:
```lua
-- 在場景初始化時預載
self.animationManager.loader.preloadAnimations()
```

**獲取已載入列表**:
```lua
local loaded = self.animationManager.loader.getLoadedAnimations()
for _, name in ipairs(loaded) do
    print("已載入動畫: " .. name)
end
```

### 4.7 完整範例

```lua
-- 初始化
function MyScene:init()
    self.animationManager = {
        loader = require("InannaLua/Tools/AnimationLoader"),
        activeAnimations = {},
    }
    self.animationManager.loader.setBasePath("InannaResource/Inanna/videos")
    
    -- 預載動畫
    self.animationManager.loader.preloadAnimations()
    
    -- 創建角色行走動畫
    self:createWalkAnimation()
end

-- 創建動畫
function MyScene:createWalkAnimation()
    local sprite = self.animationManager.loader.createAnimatedSprite(
        "walk_animation",
        30,      -- 30 FPS
        200,     -- 寬度 200
        200,     -- 高度 200
        true     -- 循環播放
    )
    
    if sprite then
        sprite:setPosition(cc.p(display.cx, display.cy))
        self:addChild(sprite)
        self.animationManager.activeAnimations["walk"] = sprite
    end
end

-- 清理
function MyScene:onExit()
    if self.animationManager then
        -- 停止所有動畫
        for name, anim in pairs(self.animationManager.activeAnimations) do
            anim:stop()
            if anim:getParent() then
                anim:removeFromParent()
            end
        end
        
        -- 清除快取
        self.animationManager.loader.clearCache()
        
        -- 釋放引用
        self.animationManager.activeAnimations = {}
        self.animationManager.loader = nil
        self.animationManager = nil
    end
end
```

---

## 6. 錯誤處理機制

### 5.1 異常體系

**位置**: `core/exceptions/`

**異常類別**:
```python
class V2PException(Exception):
    """基礎異常類"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        self.error_type = ErrorType.GENERAL

class ConfigError(V2PException):
    """配置錯誤"""
    def __init__(self, message, details=None):
        super().__init__(message, details)
        self.error_type = ErrorType.CONFIG

class FileError(V2PException):
    """文件錯誤"""
    def __init__(self, message, details=None):
        super().__init__(message, details)
        self.error_type = ErrorType.FILE

class ConversionError(V2PException):
    """轉換錯誤"""
    def __init__(self, message, details=None):
        super().__init__(message, details)
        self.error_type = ErrorType.CONVERSION
```

### 5.2 錯誤處理模式

**在核心業務層**:
```python
def process_video(...):
    try:
        # 業務邏輯
        pass
    except (ConfigError, FileError, ConversionError):
        # 重新拋出自定義異常
        raise
    except Exception as e:
        # 包裝未預期的異常
        raise ConversionError("處理失敗", details=str(e))
```

**在 UI 層**:
```python
from core.error_handler import handle_error

def on_convert_click(...):
    try:
        return process_video(...)
    except (ConfigError, FileError, ConversionError) as e:
        return handle_error(e, ui_component=True)
    except Exception as e:
        return handle_error(e, ui_component=True)
```

### 5.3 錯誤訊息格式

**位置**: `core/error_handler.py`

```python
def handle_error(error, ui_component=False):
    """統一的錯誤處理"""
    if isinstance(error, V2PException):
        # 記錄詳細錯誤
        logging.error(f"{error.error_type.value} - {error.message}")
        if error.details:
            logging.debug(f"詳細錯誤：{error.details}")
        
        # 返回友好訊息
        if ui_component:
            return f"❌ {error.error_type.value}：{error.message}"
    else:
        # 未預期的錯誤
        logging.error(f"未預期的錯誤：{str(error)}", exc_info=True)
        if ui_component:
            return f"❌ 處理失敗：{str(error)}"
```

---

## 7. 日誌系統

### 6.1 日誌配置

**位置**: `core/logger.py`

```python
def setup_logger(log_level=logging.INFO):
    """設定日誌系統"""
    # 日誌目錄
    log_dir = os.path.join(get_application_path(), "log")
    os.makedirs(log_dir, exist_ok=True)
    
    # 日誌檔名（按日期）
    log_file = os.path.join(log_dir, f"v2p_{datetime.now():%Y%m%d}.log")
    
    # 配置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 檔案處理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

### 6.2 日誌使用範例

```python
import logging

# INFO: 一般操作
logging.info(f"開始處理影片：{video_name}")

# DEBUG: 除錯資訊
logging.debug(f"FFmpeg 命令：{' '.join(cmd)}")

# WARNING: 警告
logging.warning(f"未設定 TinyPNG API 金鑰")

# ERROR: 錯誤（含堆疊）
logging.error(f"處理失敗：{str(e)}", exc_info=True)
```

---

## 8. 擴展與自訂

### 7.1 添加新的輸出格式

1. 修改 `core/video.py` 的 `extract_frames()` 函數
2. 添加新的格式選項到 UI
3. 更新 TexturePacker 參數

### 7.2 整合其他壓縮服務

1. 在 `core/video.py` 添加新的壓縮函數
2. 在 ConfigManager 添加 API 金鑰配置
3. 更新 UI 添加壓縮選項

### 7.3 添加批量處理

1. 修改 `main_tab.py` 支援多檔案上傳
2. 在 `video.py` 添加批量處理函數
3. 更新 UI 顯示批次進度

---

**文檔維護者**: V2P 開發團隊  
**最後更新**: 2025-10-09

