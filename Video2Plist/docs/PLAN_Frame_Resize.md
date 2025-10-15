# Frame 尺寸縮放功能實作計劃

**版本**: v1.1.0  
**建立日期**: 2025-10-09  
**預估工作時間**: 6-9 小時

---

## 📋 功能概述

新增 Frame 尺寸縮放功能，讓使用者可以在影片轉換時調整影格尺寸，減少處理時間和檔案大小。

## ✅ 需求確認

### 核心需求
- ✅ 可自由設定目標寬度和高度（1-8192 像素）
- ✅ 支援鎖定長寬比，調整一個值時另一個自動計算
- ✅ 提供快速比例選擇按鈕（1:1, 16:9, 9:16, 4:3, 原始）
- ✅ 四種縮放模式：拉伸變形、裁切中心、填充黑邊、填充透明邊
- ✅ 預設不啟用（使用原始尺寸）
- ✅ 記住使用者的設定偏好

### UI 設計（方案 B）
```
☑ 啟用 Frame 尺寸縮放
  ☑ 鎖定長寬比
  ├─ 比例設定：寬 [16] : 高 [9]
  └─ 快速選擇：[1:1] [16:9] [9:16] [4:3] [原始]
  
  寬度  [========●] 1920 px  (1-8192)
  高度  [========●] 1080 px  (1-8192)
  
  縮放模式：
  (•) 拉伸變形 - 填滿目標尺寸
  ( ) 裁切中心 - 保持比例，裁切超出
  ( ) 填充黑邊 - 保持比例，填充黑色
  ( ) 填充透明邊 - 保持比例，填充透明 (PNG)
  
  ⓘ 原始：1920x1080 (16:9) → 縮放後：512x288 (16:9)
```

---

## 📝 詳細 TodoList

### 🎨 階段 1: UI 元件實作（優先級：高）

#### 1.1 建立基礎 UI 元件

- [ ] **UI-1.1.1**: 新增「啟用 Frame 尺寸縮放」Checkbox
  - **檔案**: `Tool/ui/tabs/main_tab.py`
  - **位置**: 進階設定區域，影格設定之後
  - **參數**: 
    - `label="啟用 Frame 尺寸縮放"`
    - `value=False`（預設不啟用）
    - `info="啟用後會在擷取影格時調整尺寸"`
  - **變數名**: `enable_frame_resize`
  
- [ ] **UI-1.1.2**: 新增「鎖定長寬比」Checkbox
  - **預設狀態**: `interactive=False`（未啟用縮放時不可用）
  - `label="鎖定長寬比"`
  - `value=True`（預設鎖定）
  - **變數名**: `lock_aspect_ratio`
  
- [ ] **UI-1.1.3**: 新增比例輸入框（寬、高）
  - **元件**: `gr.Number`
  - **參數**:
    - `minimum=1`, `maximum=999`
    - 預設值：`aspect_width=16`, `aspect_height=9`
    - `precision=0`（整數）
    - `interactive=False`（預設不可用）
  - **布局**: 使用 Row，文字「比例設定：寬 [___] : 高 [___]」

#### 1.2 快速比例選擇按鈕

- [ ] **UI-1.2.1**: 新增 5 個快速按鈕
  - **按鈕列表**:
    - `btn_ratio_1_1`: "1:1"
    - `btn_ratio_16_9`: "16:9"
    - `btn_ratio_9_16`: "9:16"
    - `btn_ratio_4_3`: "4:3"
    - `btn_ratio_original`: "原始"
  - **參數**: `size="sm"`, `variant="secondary"`
  - **布局**: 水平排列在 `gr.Row` 中，label="快速選擇："

#### 1.3 尺寸控制 Sliders

- [ ] **UI-1.3.1**: 新增寬度 Slider
  - **變數名**: `frame_width_slider`
  - **參數**:
    - `minimum=1`, `maximum=8192`
    - `value=1920`（預設值，會從 preferences 或影片讀取）
    - `step=1`
    - `label="寬度 (Width)"`
    - `info="Frame 寬度（像素）"`
    - `interactive=False`（預設不可用）
  
- [ ] **UI-1.3.2**: 新增高度 Slider
  - **變數名**: `frame_height_slider`
  - **參數**:
    - `minimum=1`, `maximum=8192`
    - `value=1080`
    - `step=1`
    - `label="高度 (Height)"`
    - `info="Frame 高度（像素）"`
    - `interactive=False`

#### 1.4 縮放模式選擇

- [ ] **UI-1.4.1**: 新增縮放模式 Radio
  - **變數名**: `resize_mode`
  - **選項**:
    ```python
    choices=[
        ("拉伸變形 - 填滿目標尺寸", "stretch"),
        ("裁切中心 - 保持比例，裁切超出", "crop"),
        ("填充黑邊 - 保持比例，填充黑色", "pad_black"),
        ("填充透明邊 - 保持比例，填充透明 (PNG)", "pad_transparent")
    ]
    ```
  - `value="stretch"`（預設）
  - `label="縮放模式"`
  - `interactive=False`

#### 1.5 提示資訊

- [ ] **UI-1.5.1**: 新增尺寸資訊 Markdown 元件
  - **變數名**: `frame_size_info`
  - **預設內容**: `"ⓘ 提示：請先上傳影片"`
  - **動態更新**: 顯示原始尺寸 → 縮放後尺寸

---

### ⚙️ 階段 2: UI 事件處理（優先級：高）
**依賴**: 階段 1 完成

#### 2.1 啟用/停用控制

- [ ] **UI-2.1.1**: 實作 `on_enable_resize_change()` 函數
  - **輸入**: `enable` (bool)
  - **輸出**: 多個 `gr.update()` 物件
  - **邏輯**:
    ```python
    if enable:
        # 啟用所有子元件
        return [
            gr.update(interactive=True),  # lock_aspect_ratio
            gr.update(interactive=True),  # aspect_width
            gr.update(interactive=True),  # aspect_height
            gr.update(interactive=True),  # frame_width_slider
            gr.update(interactive=True),  # frame_height_slider
            gr.update(interactive=True),  # resize_mode
            # 所有快速按鈕也啟用
        ]
    else:
        # 停用所有子元件
        return [gr.update(interactive=False), ...]
    ```

#### 2.2 長寬比鎖定邏輯

- [ ] **UI-2.2.1**: 實作 `on_lock_aspect_change()` 函數
  - **輸入**: `lock` (bool), `width`, `height`, `aspect_w`, `aspect_h`
  - **輸出**: 更新後的高度或提示
  - **邏輯**: 鎖定時根據當前比例重新計算高度

- [ ] **UI-2.2.2**: 實作 `on_width_change()` 函數
  - **輸入**: `width`, `lock`, `aspect_w`, `aspect_h`, `original_w`, `original_h`
  - **輸出**: `gr.update(value=new_height)`, 更新後的提示文字
  - **計算**: `new_height = int(width * aspect_h / aspect_w)`
  - **條件**: 只有在 `lock=True` 時才計算

- [ ] **UI-2.2.3**: 實作 `on_height_change()` 函數
  - **輸入**: `height`, `lock`, `aspect_w`, `aspect_h`, `original_w`, `original_h`
  - **輸出**: `gr.update(value=new_width)`, 更新後的提示文字
  - **計算**: `new_width = int(height * aspect_w / aspect_h)`
  - **條件**: 只有在 `lock=True` 時才計算

#### 2.3 比例設定

- [ ] **UI-2.3.1**: 實作 `on_aspect_ratio_change()` 函數
  - **輸入**: `aspect_w`, `aspect_h`, `width`, `lock`
  - **輸出**: 更新後的高度
  - **驗證**: 比例必須 > 0
  - **邏輯**: 比例改變時，如果鎖定則重新計算高度

- [ ] **UI-2.3.2**: 實作快速按鈕事件處理
  - **1:1 按鈕**:
    ```python
    def on_ratio_1_1_click():
        return [
            True,  # lock_aspect_ratio
            1,     # aspect_width
            1,     # aspect_height
            gr.update(value=計算後的高度)
        ]
    ```
  - **16:9, 9:16, 4:3 按鈕**: 類似邏輯

- [ ] **UI-2.3.3**: 實作「原始」按鈕特殊邏輯
  - **輸入**: `video_file`（當前上傳的影片）
  - **處理**:
    1. 使用 FFmpeg/FFprobe 讀取影片尺寸
    2. 計算最簡比例（GCD）
    3. 返回比例寬、高
  - **範例**: 1920x1080 → GCD=120 → 16:9

#### 2.4 提示文字更新

- [ ] **UI-2.4.1**: 實作 `update_frame_size_info()` 函數
  - **輸入**: `original_w`, `original_h`, `target_w`, `target_h`, `resize_mode`
  - **輸出**: Markdown 格式的提示文字
  - **格式**:
    ```
    ⓘ 原始尺寸：1920x1080 (16:9)
    → 縮放後：512x288 (16:9)
    模式：拉伸變形
    ```
  - **計算比例**: 使用 GCD 計算最簡分數

#### 2.5 事件綁定

- [ ] **UI-2.5.1**: 綁定所有事件到元件
  ```python
  # 啟用縮放
  enable_frame_resize.change(
      on_enable_resize_change,
      inputs=[enable_frame_resize],
      outputs=[lock_aspect_ratio, aspect_width, ..., resize_mode]
  )
  
  # 鎖定長寬比
  lock_aspect_ratio.change(
      on_lock_aspect_change,
      inputs=[lock_aspect_ratio, frame_width_slider, ...],
      outputs=[frame_height_slider, frame_size_info]
  )
  
  # 寬度改變
  frame_width_slider.change(
      on_width_change,
      inputs=[frame_width_slider, lock_aspect_ratio, ...],
      outputs=[frame_height_slider, frame_size_info]
  )
  
  # 高度改變（類似）
  # 比例改變（類似）
  # 快速按鈕點擊
  btn_ratio_1_1.click(on_ratio_1_1_click, ...)
  # 其他按鈕...
  
  # 上傳影片時讀取原始尺寸並更新
  mp4_file.change(
      on_video_upload,
      inputs=[mp4_file],
      outputs=[frame_width_slider, frame_height_slider, frame_size_info]
  )
  ```

---

### 🔧 階段 3: 核心功能實作（優先級：高）
**依賴**: 無（可與階段 1-2 並行）

#### 3.1 FFmpeg 縮放命令

- [ ] **CORE-3.1.1**: 實作「拉伸變形」模式
  - **檔案**: `Tool/core/video.py`
  - **函數**: 在 `extract_frames()` 中
  - **濾鏡**: `scale={width}:{height}`
  - **測試**: 確認輸出尺寸精確匹配

- [ ] **CORE-3.1.2**: 實作「裁切中心」模式
  - **濾鏡**: 
    ```python
    f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
    ```
  - **說明**: 
    - `force_original_aspect_ratio=increase`: 放大到至少填滿目標
    - `crop`: 裁切到精確尺寸，保持中央
  - **測試**: 確認裁切位置在中央

- [ ] **CORE-3.1.3**: 實作「填充黑邊」模式
  - **濾鏡**:
    ```python
    f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    ```
  - **說明**:
    - `force_original_aspect_ratio=decrease`: 縮小到適合目標
    - `pad`: 填充黑色，居中對齊
    - `(ow-iw)/2`: 水平居中
    - `(oh-ih)/2`: 垂直居中
  - **測試**: 確認黑邊大小和位置

- [ ] **CORE-3.1.4**: 實作「填充透明邊」模式
  - **濾鏡**:
    ```python
    f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black@0"
    ```
  - **說明**: `color=black@0` 表示透明色
  - **限制**: 僅 PNG 格式支援
  - **處理**: 如果是 JPG，自動降級為黑邊模式並警告

#### 3.2 修改 extract_frames() 函數

- [ ] **CORE-3.2.1**: 更新函數簽名
  ```python
  def extract_frames(
      video_path, 
      output_folder, 
      fps, 
      ffmpeg_path, 
      output_name, 
      output_format="PNG", 
      quality=5,
      enable_resize=False,       # 新增
      target_width=None,         # 新增
      target_height=None,        # 新增
      resize_mode="stretch"      # 新增
  ):
  ```

- [ ] **CORE-3.2.2**: 實作濾鏡組合邏輯
  ```python
  # 建立濾鏡列表
  filters = [f"fps={fps}"]
  
  # 如果啟用縮放
  if enable_resize and target_width and target_height:
      if resize_mode == "stretch":
          filters.append(f"scale={target_width}:{target_height}")
      elif resize_mode == "crop":
          filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase")
          filters.append(f"crop={target_width}:{target_height}")
      elif resize_mode == "pad_black":
          filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease")
          filters.append(f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black")
      elif resize_mode == "pad_transparent":
          # 檢查格式
          if output_format.upper() == "JPG":
              logging.warning("JPG 格式不支援透明邊，自動降級為黑邊模式")
              filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease")
              filters.append(f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black")
          else:
              filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease")
              filters.append(f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black@0")
  
  # 組合濾鏡
  filter_str = ",".join(filters)
  
  # 構建命令
  cmd = [ffmpeg_path, "-i", video_path, "-vf", filter_str, ...]
  ```

- [ ] **CORE-3.2.3**: 增強日誌記錄
  ```python
  if enable_resize:
      logging.info(f"啟用 Frame 縮放：{target_width}x{target_height}")
      logging.info(f"縮放模式：{resize_mode}")
  else:
      logging.info("使用原始尺寸（未啟用縮放）")
  
  logging.debug(f"FFmpeg 完整命令：{' '.join(cmd)}")
  ```

#### 3.3 修改 process_video() 函數

- [ ] **CORE-3.3.1**: 更新函數簽名
  ```python
  def process_video(
      mp4_file,
      fps,
      output_name,
      max_width,
      max_height,
      ffmpeg_path,
      texture_packer_path,
      output_format="PNG",
      quality=5,
      use_tinypng=False,
      tinypng_api_key=None,
      enable_resize=False,       # 新增
      target_width=None,         # 新增
      target_height=None,        # 新增
      resize_mode="stretch",     # 新增
      ui_manager=None,
      progress=gr.Progress()
  ):
  ```

- [ ] **CORE-3.3.2**: 參數驗證
  ```python
  # 驗證縮放參數
  if enable_resize:
      if not target_width or not target_height:
          raise ConfigError("啟用縮放時必須提供目標寬度和高度")
      if target_width < 1 or target_height < 1:
          raise ConfigError("目標尺寸必須大於 0")
      if target_width > 8192 or target_height > 8192:
          logging.warning(f"目標尺寸 {target_width}x{target_height} 較大，處理時間可能較長")
  ```

- [ ] **CORE-3.3.3**: 傳遞參數到 extract_frames()
  ```python
  frame_count = extract_frames(
      mp4_file.name, 
      frames_dir, 
      fps, 
      ffmpeg_path, 
      output_name, 
      output_format, 
      quality,
      enable_resize=enable_resize,
      target_width=target_width,
      target_height=target_height,
      resize_mode=resize_mode
  )
  ```

- [ ] **CORE-3.3.4**: 讀取原始影片尺寸
  ```python
  # 使用 FFprobe 讀取原始尺寸
  def get_video_dimensions(video_path, ffmpeg_path):
      """獲取影片原始尺寸"""
      # 使用 ffprobe 或 ffmpeg -i 讀取
      # 返回 (width, height)
      pass
  
  original_width, original_height = get_video_dimensions(mp4_file.name, ffmpeg_path)
  logging.info(f"原始影片尺寸：{original_width}x{original_height}")
  ```

---

### 💾 階段 4: 配置與 Metadata（優先級：中）
**依賴**: 階段 3 完成

#### 4.1 偏好設定

- [ ] **CONFIG-4.1.1**: 新增偏好設定欄位
  - **檔案**: `Tool/core/config.py`
  - **位置**: `load_preferences()` 和 `save_preferences()`
  - **新增欄位**:
    ```python
    preferences = {
        # ... 現有設定 ...
        "last_enable_resize": False,
        "last_lock_aspect": True,
        "last_aspect_width": 16,
        "last_aspect_height": 9,
        "last_frame_width": 1920,
        "last_frame_height": 1080,
        "last_resize_mode": "stretch"
    }
    ```

- [ ] **CONFIG-4.1.2**: 更新 UIManager 的 `_on_page_load()`
  - **檔案**: `Tool/ui/manager.py`
  - **修改**: 在返回值中加入縮放相關設定
    ```python
    def _on_page_load(self):
        prefs = self.config_manager.preferences
        return [
            # ... 現有返回值 ...
            prefs.get("last_enable_resize", False),
            prefs.get("last_lock_aspect", True),
            prefs.get("last_aspect_width", 16),
            prefs.get("last_aspect_height", 9),
            prefs.get("last_frame_width", 1920),
            prefs.get("last_frame_height", 1080),
            prefs.get("last_resize_mode", "stretch")
        ]
    ```

- [ ] **CONFIG-4.1.3**: 更新轉換時儲存邏輯
  - **檔案**: `Tool/ui/tabs/main_tab.py`
  - **位置**: `on_convert_click()` 函數中
  - **新增**:
    ```python
    config_manager.save_preferences({
        # ... 現有設定 ...
        "last_enable_resize": enable_resize,
        "last_lock_aspect": lock_aspect,
        "last_aspect_width": aspect_w,
        "last_aspect_height": aspect_h,
        "last_frame_width": frame_w,
        "last_frame_height": frame_h,
        "last_resize_mode": resize_mode
    })
    ```

#### 4.2 Metadata 更新

- [ ] **META-4.2.1**: 修改 `save_metadata()` 函數
  - **檔案**: `Tool/core/video.py`
  - **新增欄位**:
    ```python
    metadata = {
        "name": output_name,
        "fps": settings.get("fps", 0),
        "max_width": settings.get("max_width", 0),
        "max_height": settings.get("max_height", 0),
        "creation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "frame_count": settings.get("frame_count", 0),
        "plist_count": settings.get("plist_count", 0),
        "tool_version": get_version(),
        "output_format": settings.get("output_format", "PNG"),
        "quality": settings.get("quality", 5),
        # 新增欄位
        "original_size": settings.get("original_size", ""),      # 例如 "1920x1080"
        "frame_resize_enabled": settings.get("frame_resize_enabled", False),
        "frame_size": settings.get("frame_size", ""),            # 例如 "512x288"
        "resize_mode": settings.get("resize_mode", "")           # 例如 "stretch"
    }
    ```

- [ ] **META-4.2.2**: 在 process_video() 中準備 metadata
  ```python
  settings = {
      "fps": fps,
      "max_width": max_width,
      "max_height": max_height,
      "frame_count": frame_count,
      "plist_count": plist_count,
      "output_format": output_format,
      "quality": quality,
      "use_tinypng": use_tinypng,
      # 新增
      "original_size": f"{original_width}x{original_height}",
      "frame_resize_enabled": enable_resize,
      "frame_size": f"{target_width}x{target_height}" if enable_resize else f"{original_width}x{original_height}",
      "resize_mode": resize_mode if enable_resize else ""
  }
  ```

---

### 🧪 階段 5: 測試與驗證（優先級：高）
**依賴**: 階段 1-4 完成

#### 5.1 UI 功能測試

- [ ] **TEST-5.1.1**: 測試啟用/停用縮放
  - 預設應該是停用狀態
  - 勾選後所有子元件應該可用
  - 取消後所有子元件應該不可用

- [ ] **TEST-5.1.2**: 測試長寬比鎖定/解鎖
  - 預設應該是鎖定狀態
  - 鎖定時調整寬度，高度應該自動計算
  - 解鎖後寬高應該可以獨立調整

- [ ] **TEST-5.1.3**: 測試寬度調整時高度聯動
  - 鎖定 16:9，寬度改為 512，高度應該變為 288
  - 鎖定 1:1，寬度改為 512，高度應該變為 512

- [ ] **TEST-5.1.4**: 測試高度調整時寬度聯動
  - 鎖定 16:9，高度改為 1080，寬度應該變為 1920

- [ ] **TEST-5.1.5**: 測試所有快速按鈕
  - [1:1]: 比例應設為 1:1，鎖定，重新計算高度
  - [16:9]: 比例應設為 16:9
  - [9:16]: 比例應設為 9:16
  - [4:3]: 比例應設為 4:3
  - [原始]: 應讀取影片比例（需要上傳影片）

- [ ] **TEST-5.1.6**: 測試提示文字更新
  - 上傳影片後應顯示原始尺寸
  - 調整寬高後應顯示縮放後尺寸
  - 應正確計算和顯示比例（如 16:9）

#### 5.2 縮放模式測試

- [ ] **TEST-5.2.1**: 測試拉伸模式
  - 1920x1080 → 512x512：應該變形（16:9 變成 1:1）
  - 1920x1080 → 512x288：應該保持比例
  - 檢查輸出檔案尺寸精確匹配

- [ ] **TEST-5.2.2**: 測試裁切模式
  - 1920x1080 → 512x512：應該裁切左右（保留中央）
  - 1080x1920 → 512x512：應該裁切上下
  - 檢查裁切位置是否在中央

- [ ] **TEST-5.2.3**: 測試黑邊模式
  - 1920x1080 → 512x512：上下應該有黑邊
  - 檢查黑邊大小：(512-288)/2 = 112px 上下各
  - 檢查內容是否居中

- [ ] **TEST-5.2.4**: 測試透明邊模式（PNG）
  - 1920x1080 → 512x512：上下應該有透明邊
  - 使用圖片查看器確認透明度
  - 疊加到其他背景上測試

- [ ] **TEST-5.2.5**: 測試 JPG + 透明邊的降級
  - 選擇 JPG 格式 + 透明邊模式
  - 應該自動降級為黑邊
  - 日誌應該有警告訊息

#### 5.3 整合測試

- [ ] **TEST-5.3.1**: 完整轉換流程
  1. 上傳 MP4 影片
  2. 啟用縮放，設定 512x512，拉伸模式
  3. 轉換
  4. 檢查輸出：
     - Frame 尺寸是否正確
     - Plist 檔案是否正常
     - Metadata 是否記錄正確

- [ ] **TEST-5.3.2**: 偏好設定儲存與載入
  1. 設定縮放參數並轉換
  2. 重新啟動程式
  3. 檢查設定是否恢復

- [ ] **TEST-5.3.3**: Metadata 驗證
  - 檢查 `original_size` 正確
  - 檢查 `frame_resize_enabled` 正確
  - 檢查 `frame_size` 正確
  - 檢查 `resize_mode` 正確

#### 5.4 邊界測試

- [ ] **TEST-5.4.1**: 最小尺寸 1x1
  - 設定 1x1，應該能正常處理
  - 輸出應該是 1x1 的 frame

- [ ] **TEST-5.4.2**: 最大尺寸 8192x8192
  - 設定 8192x8192
  - 應該有警告提示（處理時間較長）
  - 應該能成功處理

- [ ] **TEST-5.4.3**: 極端比例測試
  - 1:100 比例（寬 10，高 1000）
  - 100:1 比例（寬 1000，高 10）
  - 應該能正常處理，不崩潰

- [ ] **TEST-5.4.4**: 無效輸入處理
  - 寬度或高度為 0：應該拒絕或限制為 1
  - 負數：應該拒絕
  - 超出範圍：應該限制在 1-8192

---

### 📚 階段 6: 文檔更新（優先級：中）
**依賴**: 階段 5 完成

- [ ] **DOC-6.1**: 更新 `docs/PRD.md`
  - **章節**: 功能需求 → 2.1 核心功能
  - **新增**: Frame 尺寸縮放功能詳細說明
  - **內容**:
    - 功能描述
    - 參數說明表格
    - 四種縮放模式說明
    - 使用情境範例
  - **章節**: 版本歷史
  - **新增**: v1.1.0 條目

- [ ] **DOC-6.2**: 更新 `docs/FEATURES.md`
  - **新增章節**: Frame 尺寸縮放功能
  - **內容**:
    - 功能介紹
    - UI 操作說明
    - 四種縮放模式詳解（含視覺範例）
    - FFmpeg 命令解析
    - 使用範例和最佳實踐
    - 常見問題 FAQ

- [ ] **DOC-6.3**: 更新 `Tool/README.md`
  - **版本號**: 更新為 v1.1.0
  - **版本歷史**: 新增 v1.1.0 條目
    ```markdown
    ### v1.1.0 (2025-10-XX)
    - 新增 Frame 尺寸縮放功能
    - 支援四種縮放模式（拉伸、裁切、黑邊、透明邊）
    - 支援長寬比鎖定和快速比例選擇
    - 偏好設定自動儲存縮放參數
    - Metadata 記錄完整縮放資訊
    ```

- [ ] **DOC-6.4**: 更新 `.cursor/rules/` （可選）
  - **檔案**: `v2p-architecture.mdc`
  - **更新**: UI 元件和參數傳遞（如有重大改動）
  - **檔案**: `v2p-coding-standards.mdc`
  - **更新**: 新增的函數命名規範（如需要）

---

### 🚀 階段 7: 發布準備（優先級：低）
**依賴**: 階段 6 完成

- [ ] **RELEASE-7.1**: 更新版本號
  - **檔案**: `Tool/version.py`
  - **修改**:
    ```python
    VERSION = {
        'major': 1,
        'minor': 1,  # 從 0 改為 1
        'patch': 0
    }
    ```
  - **更新**: `BUILD_INFO['date']`

- [ ] **RELEASE-7.2**: 最終回歸測試
  - [ ] 測試所有現有功能是否正常
  - [ ] 測試新功能是否正常
  - [ ] 測試不同場景組合
  - [ ] 檢查沒有引入新的 bug

- [ ] **RELEASE-7.3**: 準備 Release Notes
  - **內容**:
    ```markdown
    # V2P v1.1.0 Release Notes
    
    ## 🎉 新功能
    
    ### Frame 尺寸縮放
    - 支援在影格擷取時調整尺寸
    - 四種縮放模式：拉伸變形、裁切中心、填充黑邊、填充透明邊
    - 長寬比鎖定功能
    - 快速比例選擇（1:1, 16:9, 9:16, 4:3, 原始）
    
    ## 🔧 改進
    - 偏好設定自動儲存縮放參數
    - Metadata 完整記錄縮放資訊
    - 增強的 FFmpeg 命令日誌
    
    ## 📝 文檔
    - 更新 PRD 和 FEATURES 文檔
    - 新增詳細的使用指南
    
    ## 🐛 Bug 修復
    - （如有）
    ```

---

## 📊 進度追蹤

### 統計

- **UI 層**: 15 個任務
- **核心層**: 10 個任務
- **配置/Metadata**: 5 個任務
- **測試**: 14 個任務
- **文檔**: 4 個任務
- **發布**: 3 個任務

**總計**: **51 個詳細任務**

### 檢查清單

#### 階段 1: UI 元件 (15 任務)
- [ ] 1.1 基礎元件 (3)
- [ ] 1.2 快速按鈕 (1)
- [ ] 1.3 尺寸 Sliders (2)
- [ ] 1.4 縮放模式 (1)
- [ ] 1.5 提示資訊 (1)

#### 階段 2: UI 事件 (7 任務)
- [ ] 2.1 啟用控制 (1)
- [ ] 2.2 鎖定邏輯 (3)
- [ ] 2.3 比例設定 (3)
- [ ] 2.4 提示更新 (1)
- [ ] 2.5 事件綁定 (1)

#### 階段 3: 核心功能 (10 任務)
- [ ] 3.1 FFmpeg 命令 (4)
- [ ] 3.2 extract_frames (3)
- [ ] 3.3 process_video (4)

#### 階段 4: 配置/Metadata (5 任務)
- [ ] 4.1 偏好設定 (3)
- [ ] 4.2 Metadata (2)

#### 階段 5: 測試 (14 任務)
- [ ] 5.1 UI 測試 (6)
- [ ] 5.2 縮放模式 (5)
- [ ] 5.3 整合測試 (3)
- [ ] 5.4 邊界測試 (4)

#### 階段 6: 文檔 (4 任務)
- [ ] 6.1-6.4 文檔更新

#### 階段 7: 發布 (3 任務)
- [ ] 7.1-7.3 發布準備

---

## ⚠️ 注意事項

1. **FFmpeg 相容性**: 
   - 確保 `scale` 和 `pad` 濾鏡在 FFmpeg 4.0+ 版本正常工作
   - 測試 `force_original_aspect_ratio` 參數

2. **效能考量**:
   - 放大到超大尺寸（>4096）會顯著增加處理時間
   - 需要在 UI 中提示使用者

3. **錯誤處理**:
   - FFmpeg 命令失敗時提供清楚的錯誤訊息
   - 參數驗證（寬高 > 0，< 8192）

4. **UI 回應**:
   - 拖動 Slider 時即時更新提示文字
   - 使用 debounce 避免過度計算

5. **PNG vs JPG**:
   - 透明邊模式僅支援 PNG
   - JPG 自動降級為黑邊並記錄警告

6. **日誌記錄**:
   - 記錄完整的 FFmpeg 命令
   - 記錄所有縮放參數
   - 使用 DEBUG 級別記錄詳細資訊

7. **向後相容**:
   - 沒有縮放參數時使用原始尺寸
   - 舊的 metadata 檔案仍然可讀

---

## 🎯 驗收標準

### 必須達成
- [x] 所有 51 個 TODO 任務完成
- [ ] UI 功能完整且直觀
- [ ] 四種縮放模式正確實現
- [ ] 長寬比鎖定功能正常
- [ ] 偏好設定正確儲存/載入
- [ ] Metadata 完整記錄
- [ ] 所有測試通過
- [ ] 文檔完整更新

### 品質標準
- [ ] 無崩潰和嚴重 bug
- [ ] FFmpeg 命令正確無誤
- [ ] 日誌記錄完整
- [ ] 錯誤訊息清晰友好
- [ ] 效能可接受（處理時間合理）

### 文檔標準
- [ ] PRD 更新完整
- [ ] FEATURES 包含詳細使用指南
- [ ] README 版本歷史更新
- [ ] Release Notes 準備完成

---

**計劃建立**: 2025-10-09  
**預計完成**: 2025-10-10（1-2 天）  
**責任人**: V2P 開發團隊

