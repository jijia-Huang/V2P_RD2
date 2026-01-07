# 如何查看 Gradio 的所有依賴和子模組

## 方法 1: 使用 pip show 查看依賴

```bash
pip show gradio
```

這會顯示 Gradio 的版本和直接依賴。

## 方法 2: 使用 pip list 查看已安裝的相關套件

```bash
pip list | findstr -i "gradio httpx groovy"
```

## 方法 3: 查看 PyInstaller 的警告檔案

打包完成後，查看 `build/v2p/warn-v2p.txt`，裡面會列出：
- 缺少的模組（missing）
- 無法找到的模組（not found）

## 方法 4: 使用 Python 腳本檢查

執行 `check_gradio_deps.py`：

```bash
python check_gradio_deps.py
```

這會顯示：
- 所有子模組列表
- 數據檔案列表
- 版本檔案檢查
- 建議的配置

## 方法 5: 查看 Gradio 的官方文檔

訪問 [Gradio GitHub](https://github.com/gradio-app/gradio) 查看 `requirements.txt` 或 `setup.py`

## 當前配置說明

`v2p.spec` 已經配置為自動收集以下 Gradio 相關模組：

### 核心模組
- `gradio` - Gradio 核心
- `gradio_client` - Gradio 客戶端
- `safehttpx` - HTTP 客戶端
- `groovy` - Gradio 依賴

### 相關依賴模組
- `httpx` - HTTP 客戶端庫
- `httpcore` - HTTP 核心
- `h11` - HTTP/1.1 協議
- `anyio` - 異步 I/O
- `sniffio` - 異步庫檢測
- `idna` - 國際化域名
- `certifi` - SSL 證書
- `charset_normalizer` - 字符編碼檢測
- `urllib3` - URL 處理
- `websockets` - WebSocket 支援
- `orjson` - JSON 處理
- `pydantic` - 數據驗證
- `typing_extensions` - 類型擴展

### 自動收集功能

配置使用 `collect_submodules()` 和 `collect_data_files()` 自動遞迴收集：
- 所有子模組（包括嵌套的子模組）
- 所有數據檔案（包括版本檔案、JSON 檔案等）

### 手動確保關鍵檔案

對於某些關鍵檔案（如 `version.txt`、`types.json`），配置會手動確保它們被包含。

## 如果還有缺少的模組

如果打包後運行時出現 `ModuleNotFoundError`，可以：

1. **查看錯誤訊息**，找出缺少的模組名稱
2. **添加到 hiddenimports**：
   ```python
   hiddenimports = [
       # ... 現有的模組 ...
       '缺少的模組名稱',
   ]
   ```
3. **如果該模組有數據檔案**，也要添加到 datas：
   ```python
   datas = [
       # ... 現有的數據檔案 ...
   ] + collect_data_files('缺少的模組名稱')
   ```

## 注意事項

- `collect_submodules()` 會遞迴收集所有子模組，可能會包含一些不需要的模組
- 如果打包檔案太大，可以在 `excludes` 中排除不需要的模組
- 某些模組可能只在特定條件下才會被導入，需要根據實際運行情況調整

