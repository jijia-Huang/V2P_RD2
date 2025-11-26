# Python 打包器實作計劃

**版本**: v1.2.0  
**建立日期**: 2025-01-17  

---

## 📋 功能概述

實作 Python 原生打包器作為 TexturePacker 的備選方案，當使用者未設定 TexturePacker 路徑時自動使用 Python 打包器進行材質集打包。

## ✅ 需求確認

### 核心需求
- ✅ 當 TexturePacker 路徑未設定時，自動使用 Python 打包器
- ✅ 保持現有 UI 參數完全相容（max_width: 512-8192, max_height: 512-8192）
- ✅ 支援多材質集分割（當影格過多時）
- ✅ 生成完全相容 Cocos2d-x 的 plist 格式
- ✅ 保持與現有 Lua AnimationLoader 的相容性
- ✅ 處理速度儘可能快，但不強求極致優化

### 技術要求
- ✅ 使用 Python 原生庫（PIL, xml.etree.ElementTree）
- ✅ 實現 MaxRects 演算法進行矩形打包
- ✅ 支援 PNG/JPG 輸出格式
- ✅ 支援影格旋轉和座標計算
- ✅ 生成與 TexturePacker 相同格式的 plist 檔案

---

## 📝 詳細 TodoList

### 🏗️ 階段 1: 核心架構設計（1 天）

#### 1.1 建立基礎模組結構
- [ ] **ARCH-1.1.1**: 建立 `core/python_packer.py` 主模組
- [ ] **ARCH-1.1.2**: 導入 `python-maxrects-packer` 演算法模組
- [ ] **ARCH-1.1.3**: 建立 `core/plist_generator.py` plist 生成器
- [ ] **ARCH-1.1.4**: 建立 `core/image_processor.py` 圖像處理工具

#### 1.2 設計核心類別
```python
# 主要類別設計
class PythonTexturePacker:
    def __init__(self, max_width, max_height, output_format="PNG"):
        self.max_width = max_width
        self.max_height = max_height
        self.output_format = output_format
        self.packer = MaxRectsPacker(max_width, max_height)
    
    def pack_images(self, image_paths, output_dir, output_name):
        # 主要打包邏輯
        pass

class MaxRectsPacker:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.free_rects = [Rect(0, 0, width, height)]
    
    def pack_rects(self, rects):
        # MaxRects 演算法實現
        pass

class PlistGenerator:
    def generate_plist(self, packed_data, output_path):
        # 生成 Cocos2d-x 格式的 plist
        pass
```

### 🔧 階段 2: MaxRects 演算法實現（1.5 天）

#### 2.1 基礎演算法實現
- [ ] **ALGO-2.1.1**: 實現矩形類別 `Rect` 和相關方法
- [ ] **ALGO-2.1.2**: 實現 `find_best_position()` 方法
- [ ] **ALGO-2.1.3**: 實現 `split_rect()` 方法分割剩餘空間
- [ ] **ALGO-2.1.4**: 實現 `cleanup_rects()` 方法清理重疊矩形

#### 2.2 演算法優化
- [ ] **ALGO-2.2.1**: 實現按面積排序的影格選擇策略
- [ ] **ALGO-2.2.2**: 實現旋轉檢測和最佳化
- [ ] **ALGO-2.2.3**: 實現多材質集分割邏輯
- [ ] **ALGO-2.2.4**: 添加演算法效能監控

#### 2.3 演算法核心邏輯
```python
def find_best_position(self, rect, free_rects):
    """尋找最佳放置位置"""
    best_rect = None
    best_short_side = float('inf')
    best_long_side = float('inf')
    
    for free_rect in free_rects:
        # 檢查是否能放入
        if (free_rect.width >= rect.width and 
            free_rect.height >= rect.height):
            # 計算剩餘空間
            leftover_horiz = abs(free_rect.width - rect.width)
            leftover_vert = abs(free_rect.height - rect.height)
            short_side = min(leftover_horiz, leftover_vert)
            long_side = max(leftover_horiz, leftover_vert)
            
            # 選擇最佳位置
            if (short_side < best_short_side or 
                (short_side == best_short_side and long_side < best_long_side)):
                best_rect = free_rect
                best_short_side = short_side
                best_long_side = long_side
    
    return best_rect
```

### 📄 階段 3: plist 格式實現（1 天）

#### 3.1 plist 結構分析
- [ ] **PLIST-3.1.1**: 分析現有 plist 檔案結構
- [ ] **PLIST-3.1.2**: 實現 frames 字典生成
- [ ] **PLIST-3.1.3**: 實現 metadata 字典生成
- [ ] **PLIST-3.1.4**: 實現 XML 格式輸出

#### 3.2 座標系統實現
- [ ] **PLIST-3.2.1**: 實現 `textureRect` 座標計算
- [ ] **PLIST-3.2.2**: 實現 `spriteOffset` 偏移計算
- [ ] **PLIST-3.2.3**: 實現 `spriteSize` 尺寸計算
- [ ] **PLIST-3.2.4**: 實現 `textureRotated` 旋轉標記

#### 3.3 plist 生成器實現
```python
def generate_plist(self, packed_data, output_path):
    """生成 Cocos2d-x 格式的 plist"""
    root = ET.Element("plist", version="1.0")
    root.set("xmlns", "http://www.apple.com/DTDs/PropertyList-1.0.dtd")
    
    dict_elem = ET.SubElement(root, "dict")
    
    # frames 字典
    frames_key = ET.SubElement(dict_elem, "key")
    frames_key.text = "frames"
    frames_dict = ET.SubElement(dict_elem, "dict")
    
    for frame_name, frame_data in packed_data.frames.items():
        # 為每個影格生成字典
        self._add_frame_dict(frames_dict, frame_name, frame_data)
    
    # metadata 字典
    self._add_metadata_dict(dict_elem, packed_data)
    
    # 寫入檔案
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
```

### 🔗 階段 4: 系統整合（1 天）

#### 4.1 修改現有程式碼
- [ ] **INTEG-4.1.1**: 修改 `core/video.py` 的 `process_video()` 函數
- [ ] **INTEG-4.1.2**: 添加 TexturePacker 路徑檢查邏輯
- [ ] **INTEG-4.1.3**: 實現 Python 打包器調用邏輯
- [ ] **INTEG-4.1.4**: 保持向後相容性

#### 4.2 整合邏輯實現
```python
def process_video(...):
    # 檢查 TexturePacker 路徑
    if texture_packer_path and os.path.exists(texture_packer_path):
        # 使用 TexturePacker
        logging.info("使用 TexturePacker 進行打包")
        return _process_with_texturepacker(...)
    else:
        # 使用 Python 打包器
        logging.info("使用 Python 打包器進行打包")
        return _process_with_python_packer(...)

def _process_with_python_packer(...):
    """使用 Python 打包器處理"""
    from core.python_packer import PythonTexturePacker
    
    packer = PythonTexturePacker(max_width, max_height, output_format)
    result = packer.pack_images(frame_paths, output_dir, output_name)
    
    return result
```

#### 4.3 錯誤處理和日誌
- [ ] **INTEG-4.3.1**: 添加 Python 打包器錯誤處理
- [ ] **INTEG-4.3.2**: 實現詳細的日誌記錄
- [ ] **INTEG-4.3.3**: 添加效能監控和統計
- [ ] **INTEG-4.3.4**: 實現優雅降級處理

### 🧪 階段 5: 測試和驗證（0.5 天）

#### 5.1 功能測試
- [ ] **TEST-5.1.1**: 測試基本打包功能
- [ ] **TEST-5.1.2**: 測試多材質集分割
- [ ] **TEST-5.1.3**: 測試 plist 格式相容性
- [ ] **TEST-5.1.4**: 測試與 Lua AnimationLoader 相容性

#### 5.2 效能測試
- [ ] **TEST-5.2.1**: 測試不同影格數量的處理速度
- [ ] **TEST-5.2.2**: 測試記憶體使用情況
- [ ] **TEST-5.2.3**: 測試大尺寸材質集處理
- [ ] **TEST-5.2.4**: 與 TexturePacker 效能對比

#### 5.3 相容性測試
- [ ] **TEST-5.3.1**: 測試現有專案的相容性
- [ ] **TEST-5.3.2**: 測試不同輸出格式（PNG/JPG）
- [ ] **TEST-5.3.3**: 測試不同材質大小限制
- [ ] **TEST-5.3.4**: 測試錯誤情況處理

---

## 🎯 技術實現細節

### 核心演算法：MaxRects
```python
class MaxRectsPacker:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.free_rects = [Rect(0, 0, width, height)]
        self.used_rects = []
    
    def pack_rects(self, rects):
        """使用 MaxRects 演算法打包矩形"""
        # 按面積排序（大矩形優先）
        rects.sort(key=lambda r: r.width * r.height, reverse=True)
        
        packed_rects = []
        for rect in rects:
            # 嘗試旋轉
            for rotated in [False, True]:
                if rotated:
                    rect.width, rect.height = rect.height, rect.width
                
                best_rect = self.find_best_position(rect)
                if best_rect:
                    # 放置矩形
                    rect.x = best_rect.x
                    rect.y = best_rect.y
                    rect.rotated = rotated
                    packed_rects.append(rect)
                    
                    # 分割剩餘空間
                    self.split_rect(best_rect, rect)
                    break
                elif rotated:
                    # 恢復原始尺寸
                    rect.width, rect.height = rect.height, rect.width
        
        return packed_rects
```

### plist 格式生成
```python
def _add_frame_dict(self, frames_dict, frame_name, frame_data):
    """為單個影格添加字典"""
    frame_key = ET.SubElement(frames_dict, "key")
    frame_key.text = frame_name
    
    frame_dict = ET.SubElement(frames_dict, "dict")
    
    # aliases
    aliases_key = ET.SubElement(frame_dict, "key")
    aliases_key.text = "aliases"
    aliases_array = ET.SubElement(frame_dict, "array")
    
    # spriteOffset
    offset_key = ET.SubElement(frame_dict, "key")
    offset_key.text = "spriteOffset"
    offset_string = ET.SubElement(frame_dict, "string")
    offset_string.text = f"{{{frame_data.offset_x},{frame_data.offset_y}}}"
    
    # spriteSize
    size_key = ET.SubElement(frame_dict, "key")
    size_key.text = "spriteSize"
    size_string = ET.SubElement(frame_dict, "string")
    size_string.text = f"{{{frame_data.width},{frame_data.height}}}"
    
    # textureRect
    rect_key = ET.SubElement(frame_dict, "key")
    rect_key.text = "textureRect"
    rect_string = ET.SubElement(frame_dict, "string")
    rect_string.text = f"{{{{{frame_data.x},{frame_data.y}}},{{{frame_data.width},{frame_data.height}}}}}"
    
    # textureRotated
    rotated_key = ET.SubElement(frame_dict, "key")
    rotated_key.text = "textureRotated"
    rotated_bool = ET.SubElement(frame_dict, "false" if not frame_data.rotated else "true")
```

---

## 📊 預估時程

| 階段 | 工作內容 | 預估時間 | 關鍵產出 |
|------|----------|----------|----------|
| 1 | 核心架構設計 | 1 天 | 基礎類別和模組結構 |
| 2 | MaxRects 演算法 | 1.5 天 | 矩形打包演算法 |
| 3 | plist 格式實現 | 1 天 | plist 生成器 |
| 4 | 系統整合 | 1 天 | 整合到現有系統 |
| 5 | 測試和驗證 | 0.5 天 | 功能測試和效能驗證 |
| **總計** | | **5 天** | **完整可用的 Python 打包器** |

---

## 🔍 風險評估

### 技術風險
- **演算法複雜度**: MaxRects 演算法實現可能比預期複雜
- **效能問題**: Python 實現可能比 TexturePacker 慢
- **格式相容性**: plist 格式可能與 TexturePacker 有細微差異

### 緩解措施
- **分階段實現**: 先實現基本功能，再逐步優化
- **效能監控**: 添加詳細的效能監控和日誌
- **相容性測試**: 與現有專案進行全面測試

---

## 🎯 成功標準

### 功能標準
- ✅ 能夠處理 100+ 影格的動畫序列
- ✅ 生成完全相容 Cocos2d-x 的 plist 檔案
- ✅ 支援多材質集自動分割
- ✅ 與現有 Lua AnimationLoader 完全相容

### 效能標準
- ✅ 處理 150 影格動畫在 30 秒內完成
- ✅ 記憶體使用不超過 500MB
- ✅ 生成的材質集利用率 > 80%

### 相容性標準
- ✅ 與現有 V2P 工具完全整合
- ✅ 支援所有現有 UI 參數
- ✅ 向後相容，不影響現有功能

---

## 📝 後續維護

### 維護項目
- **效能優化**: 持續優化演算法效能
- **功能擴展**: 根據需求添加新功能
- **錯誤修復**: 修復發現的問題和 bug
- **文檔更新**: 更新相關文檔和說明

### 監控指標
- **處理速度**: 監控不同影格數量的處理時間
- **記憶體使用**: 監控記憶體使用情況
- **錯誤率**: 監控處理失敗的比例
- **使用者反饋**: 收集使用者使用體驗

---

**建立者**: AI Assistant  
**最後更新**: 2025-01-17  
**狀態**: 待實作
