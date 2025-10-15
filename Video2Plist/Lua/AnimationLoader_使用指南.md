# AnimationLoader 使用指南

## 概述

`AnimationLoader` 是一個用於載入和管理 V2P 工具轉換的動畫資料的工具類，主要用於在 Cocos2d-x Lua 專案中播放動畫。

## 在 lua 中的使用方式

### 1. 初始化

```lua
-- 加入 animation loader
self.m_animationManager = {
    loader = requireWithClearLoaded("InannaLua/Tools/AnimationLoader"),
    activeAnimations = {},
}
self.m_animationManager.loader.setBasePath(inn.ANIMATION_BASE_PATH)
```

**說明：**
- `loader`: AnimationLoader 模組實例
- `activeAnimations`: 用於追蹤當前活躍的動畫物件
- `inn.ANIMATION_BASE_PATH`: 動畫資源的基礎路徑，定義在 `LobbyDefine.lua` 中為 `"InannaResource/Inanna/videos"`

### 2. 清理和釋放

```lua
if self.m_animationManager then
    -- 清除所有動畫
    for name, anim in pairs(self.m_animationManager.activeAnimations) do
        anim:stop()
        if anim:getParent() then
            anim:removeFromParent()
        end
    end
    self.m_animationManager.loader.clearCache()
    self.m_animationManager.activeAnimations = {}
    self.m_animationManager.loader = nil
    self.m_animationManager = nil
end
```

**清理步驟：**
1. 停止所有活躍的動畫
2. 從父節點移除動畫物件
3. 清除 AnimationLoader 快取
4. 重置 activeAnimations 表
5. 釋放 loader 和 animationManager 引用

## AnimationLoader 工具類詳細說明

### 核心功能

#### 1. 設定基礎路徑
```lua
AnimationLoader.setBasePath(path)
```
- **參數**: `path` - 動畫資源的基礎路徑
- **功能**: 設定所有動畫資源的根目錄

#### 2. 創建動畫精靈
```lua
AnimationLoader.createAnimatedSprite(name, fps, width, height, loop, pingpong, playInterval)
```
- **參數**:
  - `name`: 動畫名稱（會自動加上 `v2p_` 前綴）
  - `fps`: 幀率（可選，會從 metadata 讀取）
  - `width`, `height`: 縮放尺寸（可選）
  - `loop`: 是否循環播放（預設 true）
  - `pingpong`: 是否反覆播放（預設 false）
  - `playInterval`: 播放間隔時間（可選）

#### 3. 創建動畫物件
```lua
AnimationLoader.createAnimation(name, fps)
```
- **參數**:
  - `name`: 動畫名稱
  - `fps`: 幀率
- **返回**: cc.Animation 物件

#### 4. 獲取動畫資訊
```lua
AnimationLoader.getAnimationInfo(name)
```
- **返回**: 包含 fps、frame_count、texture_size 等資訊的表

### 快取管理

#### 清除快取
```lua
AnimationLoader.clearCache()
```

#### 卸載特定動畫
```lua
AnimationLoader.unloadAnimation(name)
```

#### 釋放未使用的資源
```lua
AnimationLoader.releaseUnusedResources()
```

### 預載功能

#### 預載所有動畫
```lua
AnimationLoader.preloadAnimations()
```

#### 獲取已載入的動畫列表
```lua
AnimationLoader.getLoadedAnimations()
```

## 動畫資源格式

### 檔案結構
```
InannaResource/Inanna/videos/
├── v2p_animation_name/
│   ├── v2p_animation_name_metadata.json
│   ├── v2p_animation_name.plist
│   ├── v2p_animation_name.png
│   └── ...
```

### Metadata 格式
```json
{
    "fps": 30,
    "frame_count": 60,
    "max_width": 512,
    "max_height": 512,
    "creation_time": "2025-01-01T00:00:00Z",
    "tool_version": "1.0.3",
    "output_format": "PNG",
    "quality": 5,
    "plist_count": 1
}
```

## 版本相容性

- **當前版本**: 1.0.3
- **最低支援版本**: 1.0.3
- 工具會自動檢查動畫資料的版本相容性

## 使用範例

### 基本使用
```lua
-- 初始化
local loader = require("InannaLua/Tools/AnimationLoader")
loader.setBasePath("InannaResource/Inanna/videos")

-- 創建動畫精靈
local sprite = loader.createAnimatedSprite("my_animation", 30, 200, 200, true)
if sprite then
    self:addChild(sprite)
end
```

### 管理動畫
```lua
-- 創建並追蹤動畫
local animSprite = self.m_animationManager.loader.createAnimatedSprite
if animSprite then
    self.m_animationManager.activeAnimations["lobby_effect"] = animSprite
    self:addChild(animSprite)
end
```

## 注意事項

1. **路徑格式**: 所有路徑會自動正規化為使用 `/` 分隔符
2. **命名規範**: 動畫名稱會自動加上 `v2p_` 前綴
3. **記憶體管理**: 使用完畢後記得清理快取和釋放資源
4. **錯誤處理**: 工具會輸出詳細的錯誤訊息到控制台
5. **版本檢查**: 載入前會檢查動畫資料的版本相容性

## 除錯資訊

工具會在以下情況輸出除錯訊息：
- 找不到資料夾或檔案
- 版本不相容
- 動畫創建失敗
- 快取操作

所有除錯訊息都會包含詳細的錯誤描述和相關路徑資訊。
