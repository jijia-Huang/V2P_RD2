# PyInstaller 打包指南

## 前置需求

1. **Python 環境**：Python 3.8-3.12
2. **Conda 環境**（推薦）：
   ```bash
   # 激活 conda 環境
   conda activate <your_env>
   
   # 確認環境
   which python  # 或 Windows: where python
   python --version
   ```
3. **PyInstaller**：**必須在與專案相同的環境中安裝**
   ```bash
   # 在 conda 環境中安裝
   conda install pyinstaller
   # 或
   pip install pyinstaller
   
   # 確認 PyInstaller 在正確環境中
   which pyinstaller  # 或 Windows: where pyinstaller
   ```
4. **依賴套件**：確保所有依賴已安裝在**同一個環境中**
   ```bash
   # 在 conda 環境中安裝
   pip install -r requirements.txt
   
   # 檢查環境（可選）
   python check_environment.py
   ```
5. **FFmpeg**：確保 `ffmpeg/ffmpeg.exe` 存在（主專案需要）

## 重要：環境一致性

**確保 PyInstaller 和所有依賴都在同一個 Python 環境中！**

常見問題：
- PyInstaller 在系統 Python 中，但依賴在 conda 環境中 → **會找不到模組**
- 使用 `python -m PyInstaller` 而不是直接使用 `pyinstaller` 命令可以確保使用正確的 Python 環境

**推薦做法**：
```bash
# 1. 激活 conda 環境
conda activate <your_env>

# 2. 確認環境
python check_environment.py

# 3. 確認 pyinstaller 命令在正確環境中
where pyinstaller  # Windows，應該顯示 conda 環境中的路徑

# 4. 如果 pyinstaller 不在環境中，安裝它
conda install pyinstaller
# 或
pip install pyinstaller

# 5. 使用 pyinstaller 命令（確保在正確環境中）
pyinstaller v2p.spec
pyinstaller v2p_editor.spec

# 或者使用 python -m PyInstaller.__main__（如果 pyinstaller 命令不可用）
python -m PyInstaller.__main__ v2p.spec
python -m PyInstaller.__main__ v2p_editor.spec
```

## 打包指令

### 步驟 1：確認環境

```bash
# 激活 conda 環境
conda activate <your_env>

# 檢查環境（可選）
python check_environment.py
```

### 步驟 2：確認 PyInstaller 在環境中

```bash
# 檢查 pyinstaller 是否在當前環境中
where pyinstaller  # Windows
# 應該顯示類似：D:\Conda\envs\GPTAction\Scripts\pyinstaller.exe

# 如果找不到，安裝它
conda install pyinstaller
# 或
pip install pyinstaller
```

### 步驟 3：主專案打包

在 `Tool/` 目錄下執行（**推薦使用 build_v2p.py**，會自動將 `ffmpeg` 複製到 dist）：

```bash
# 方法 1：一鍵打包並複製 ffmpeg 到 dist（推薦）
python build_v2p.py

# 方法 2：僅 PyInstaller，之後需手動複製 ffmpeg
pyinstaller v2p.spec
xcopy /E /I ffmpeg dist\ffmpeg
```

打包完成後，可執行檔位於 `dist/v2p.exe`，預設會使用同目錄的 `dist/ffmpeg/ffmpeg.exe`（無需在設定中指定路徑）。

### 步驟 4：Editor 打包

在 `Tool/` 目錄下執行：

```bash
# 方法 1：直接使用 pyinstaller 命令（推薦）
pyinstaller v2p_editor.spec

# 方法 2：如果 pyinstaller 命令不可用，使用 python -m
python -m PyInstaller.__main__ v2p_editor.spec
```

打包完成後，可執行檔位於 `dist/v2p_editor.exe`

### 重新打包（如果修改了代碼）

如果修改了 Python 代碼，需要重新打包：

```bash
# 清理之前的打包結果（可選）
rmdir /s /q build dist

# 重新打包主專案（含複製 ffmpeg 到 dist）
python build_v2p.py

# 或僅 Editor
pyinstaller v2p_editor.spec
```

## 打包輸出

打包完成後，會在 `Tool/` 目錄下產生：
- `build/`：臨時建置檔案（可刪除）
- `dist/`：打包後的執行檔和相關檔案

### 主專案輸出結構

```
dist/
├── v2p.exe                    # 主執行檔
├── ffmpeg/                    # FFmpeg 執行檔目錄
│   └── ffmpeg.exe
└── [其他依賴檔案]
```

### Editor 輸出結構

```
dist/
├── v2p_editor.exe             # Editor 執行檔
└── [其他依賴檔案]
```

## 測試打包結果

### 主專案測試

1. 執行 `dist/v2p.exe`
2. 確認 WebView UI 正常啟動
3. 測試轉換功能是否正常
4. 確認 FFmpeg 可以正常調用

### Editor 測試

1. 執行 `dist/v2p_editor.exe`
2. 確認 WebView UI 正常啟動
3. 測試資料夾檢查功能
4. 測試播放預覽功能

## 注意事項

1. **WebView2 Runtime**：打包後的 exe 仍需要系統安裝 WebView2 Runtime
2. **TexturePacker**：需要用戶自行提供 TexturePacker 執行檔
3. **檔案大小**：打包後的 exe 可能較大（包含所有依賴）
4. **啟動時間**：首次啟動可能需要解壓縮資源，啟動時間較長
5. **路徑問題**：如果遇到路徑問題，檢查 `sys._MEIPASS` 是否正確設置

## 疑難排解

### 問題：雙擊 exe 沒有任何反應

**解決方案**：
1. **啟用控制台視窗**：spec 文件已設置 `console=True`，重新打包後會顯示控制台視窗，可以看到錯誤訊息
2. **從命令行執行**：在命令行執行 exe，可以看到錯誤輸出
   ```bash
   cd dist
   v2p.exe
   ```
3. **檢查錯誤訊息**：查看控制台輸出的錯誤訊息，常見問題包括：
   - WebView2 Runtime 未安裝
   - 靜態資源路徑錯誤
   - 模組導入失敗

### 問題：找不到靜態資源（HTML/CSS/JS）

**解決方案**：
- 確認 spec 文件中的 `datas` 配置正確
- 確認路徑解析邏輯使用 `sys._MEIPASS`
- 檢查控制台輸出的路徑資訊，確認資源是否正確打包

### 問題：找不到模組（如 webview）

**原因**：PyInstaller 使用了不同的 Python 環境

**解決方案**：
1. **確認環境一致性**：
   ```bash
   # 檢查當前 Python 環境
   where python  # Windows
   
   # 檢查 PyInstaller 使用的環境
   where pyinstaller  # Windows
   
   # 兩個路徑應該在同一個 conda 環境中
   # 例如：
   # Python: D:\Conda\envs\GPTAction\python.exe
   # PyInstaller: D:\Conda\envs\GPTAction\Scripts\pyinstaller.exe
   ```

2. **如果 pyinstaller 不在環境中，安裝它**：
   ```bash
   conda activate <your_env>
   conda install pyinstaller
   # 或
   pip install pyinstaller
   ```

3. **如果 pyinstaller 命令不可用，使用 python -m**：
   ```bash
   python -m PyInstaller.__main__ v2p.spec
   ```

2. **在 conda 環境中安裝 PyInstaller**：
   ```bash
   conda activate <your_env>
   conda install pyinstaller
   # 或
   pip install pyinstaller
   ```

3. **確認模組在正確環境中**：
   ```bash
   python check_environment.py
   ```

4. **確認 `hiddenimports` 中包含所有必要的模組**
5. **檢查是否有動態導入的模組未包含**
6. **查看控制台輸出的導入錯誤訊息**

### 問題：FFmpeg 無法執行

**解決方案**：
- 確認 `ffmpeg/ffmpeg.exe` 已正確包含在 `datas` 中
- 確認路徑解析正確
- 檢查 `dist/ffmpeg/` 目錄是否存在 `ffmpeg.exe`

## 進階配置

### 單檔案模式（--onefile）

如果需要打包為單一 exe 檔案，可以在 spec 文件中修改：

```python
exe = EXE(
    # ... 其他參數 ...
    onefile=True,  # 啟用單檔案模式
)
```

**注意**：單檔案模式會增加啟動時間，因為需要解壓縮資源。

### 圖示設定

可以在 spec 文件中添加圖示：

```python
exe = EXE(
    # ... 其他參數 ...
    icon='path/to/icon.ico',  # 圖示路徑
)
```

### 除錯模式

如果需要除錯，可以啟用控制台視窗：

```python
exe = EXE(
    # ... 其他參數 ...
    console=True,  # 顯示控制台視窗
    debug=True,    # 啟用除錯模式
)
```

