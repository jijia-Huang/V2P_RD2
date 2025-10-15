--[[
    Copyright 2025 by International Games System Co., Ltd.
    All rights reserved.

    This software is the confidential and proprietary information of
    International Game System Co., Ltd. ('Confidential Information'). You shall
    not disclose such Confidential Information and shall use it only in
    accordance with the terms of the license agreement you entered into with
    International Game System Co., Ltd.
]]--

--------------------------------------------------------------------------------
-- 將使用 V2P 工具轉換的動畫資料載入到遊戲中
-- 使用方法：
-- 1. 將 AnimationLoader 加入到你的專案中
-- 2. 使用 AnimationLoader.setBasePath 設定動畫資料的基礎路徑
-- 3. 使用 AnimationLoader.createAnimatedSprite 創建 cc.Sprite with loop animation.
--------------------------------------------------------------------------------

local AnimationLoader = {}

-- 快取系統
AnimationLoader.cache = {}
AnimationLoader.base_path = nil

-- 版本相容性設定
AnimationLoader.VERSION = {
    CURRENT = "1.0.3",  -- 當前版本
    MINIMUM = "1.0.3"   -- 最低支援版本
}

-- 版本檢查
function AnimationLoader.checkVersion(metadata)
    if not metadata or not metadata.tool_version then
        -- 沒有版本資訊，假設是舊版本
        print("AnimationLoader:checkVersion: Warning: No version information found in metadata")
        return true
    end

    local function parseVersion(ver)
        -- 移除 'v' 前綴
        ver = ver:gsub("^v", "")
        local major, minor, patch = ver:match("(%d+)%.(%d+)%.(%d+)")
        return {
            tonumber(major) or 0,
            tonumber(minor) or 0,
            tonumber(patch) or 0
        }
    end

    local function compareVersion(v1, v2)
        for i = 1, 3 do
            if v1[i] ~= v2[i] then
                return v1[i] - v2[i]
            end
        end
        return 0
    end

    local dataVersion = parseVersion(metadata.tool_version)
    local minVersion = parseVersion(AnimationLoader.VERSION.MINIMUM)

    -- if compareVersion(dataVersion, minVersion) < 0 then
    --     print(string.format(
    --         "AnimationLoader:checkVersion: Error: Animation data version %s is not supported. Minimum version required: %s",
    --         metadata.tool_version,
    --         AnimationLoader.VERSION.MINIMUM
    --     ))
    --     return false
    -- end

    return true
end

-- 路徑處理
function AnimationLoader.normalizePath(path)
    return path:gsub("\\", "/")
end

-- 設定基礎路徑
function AnimationLoader.setBasePath(path)
    assert(type(path) == "string", "AnimationLoader:setBasePath: 路徑必須是字符串")
    local normal_path = AnimationLoader.normalizePath(path)
    if cc.FileUtils:getInstance():isDirectoryExist(normal_path) then
        AnimationLoader.base_path = normal_path
    else
        print("AnimationLoader:setBasePath: 警告：找不到資料夾：" .. normal_path)
    end
end

-- 讀取動畫設定
function AnimationLoader.loadMetadata(name)
    assert(AnimationLoader.base_path, "AnimationLoader:loadMetadata: 請先使用 setBasePath 設定基礎路徑")
    -- 確保名稱有 v2p_ 前綴
    if not name:match("^v2p_") then
        name = "v2p_" .. name
    end
    local folder_path = AnimationLoader.base_path .. "/" .. name
    local metadata_path = folder_path .. "/" .. name .. "_metadata.json"

    local fileUtils = cc.FileUtils:getInstance()
    if not fileUtils:isFileExist(metadata_path) then
        print("AnimationLoader:loadMetadata: 警告：找不到 metadata 文件：" .. metadata_path)
        return nil
    end

    local str = fileUtils:getStringFromFile(metadata_path)
    local json = require("cjson")
    local metadata = json.decode(str)
    if not metadata then
        print("AnimationLoader:loadMetadata: 警告：無法解析 metadata 文件：" .. metadata_path)
        return nil
    end  
    return metadata
end

-- 獲取動畫詳細資訊
function AnimationLoader.getAnimationInfo(name)
    -- 確保名稱有 v2p_ 前綴
    if not name:match("^v2p_") then
        name = "v2p_" .. name
    end
    local metadata = AnimationLoader.loadMetadata(name)
    if metadata then
        return {
            fps = metadata.fps,
            frame_count = metadata.frame_count,
            texture_size = {
                width = metadata.max_width,
                height = metadata.max_height
            },
            creation_time = metadata.creation_time,
            version = metadata.tool_version,
            output_format = metadata.output_format or "PNG",
            quality = metadata.quality or 5
        }
    end
    return nil
end

-- 從 TexturePacker 生成的 plist 和圖片創建動畫
function AnimationLoader.createAnimation(name, fps)
    if not AnimationLoader.base_path then
        print("AnimationLoader:createAnimation: 請先使用 setBasePath 設定基礎路徑")
        return nil
    end
    
    assert(type(name) == "string", "AnimationLoader:createAnimation: 名稱必須是字符串")
    
    -- 確保名稱有 v2p_ 前綴
    if not name:match("^v2p_") then
        name = "v2p_" .. name
    end
    
    -- 檢查快取
    if AnimationLoader.cache[name] then
        return AnimationLoader.cache[name]
    end
    
    -- 檢查資料夾
    local folder_path = AnimationLoader.base_path .. "/" .. name
    if not cc.FileUtils:getInstance():isDirectoryExist(folder_path) then
        print(string.format("AnimationLoader:createAnimation: 找不到資料夾：%s", folder_path))
        return nil
    end
    
    -- 讀取 metadata
    local metadata = AnimationLoader.loadMetadata(name)
    if metadata then
        fps = fps or metadata.fps
        print(string.format("AnimationLoader:createAnimation: 使用 FPS: %d (來自 metadata)", fps))
    else
        assert(fps, "AnimationLoader:createAnimation: 未找到 metadata，必須指定 FPS")
    end
    
    local frames = {}
    
    -- 載入所有的 plist 和圖片
    local max_plist_index = (metadata and metadata.plist_count and (metadata.plist_count - 1)) or 999
    local loaded_any = false
    local output_format = (metadata and metadata.output_format or "PNG"):lower()
    
    for i = 0, max_plist_index do
        local plistPath = folder_path .. "/" .. name .. "_" .. i .. ".plist"
        local imagePath = folder_path .. "/" .. name .. "_" .. i .. "." .. output_format
        
        if not cc.FileUtils:getInstance():isFileExist(plistPath) then
            if not loaded_any then
                plistPath = folder_path .. "/" .. name .. ".plist"
                imagePath = folder_path .. "/" .. name .. "." .. output_format
                if not cc.FileUtils:getInstance():isFileExist(plistPath) then
                    break
                end
            else
                break
            end
        end
        
        cc.SpriteFrameCache:getInstance():addSpriteFrames(plistPath, imagePath)
        loaded_any = true
    end
    
    if not loaded_any then
        print("AnimationLoader:createAnimation: 找不到任何 plist 文件")
        return nil
    end
    
    -- 收集所有幀
    local frame_count = metadata and metadata.frame_count or 9999
    local cache = cc.SpriteFrameCache:getInstance()
    
    for i = 0, frame_count - 1 do
        local frameName = string.format("%s_%d.%s", name, i, output_format)
        local frame = cache:getSpriteFrame(frameName)
        if frame then
            table.insert(frames, frame)
        end
    end
    
    if #frames == 0 then
        print("AnimationLoader:createAnimation: 在 plist 中找不到任何幀")
        return nil
    end
    
    -- 創建動畫
    local animation = cc.Animation:create()
    if not animation then
        print(string.format("AnimationLoader:createAnimation: cc.Animation:create() 失敗，動畫名稱：%s", name))
        return nil
    end
    
    animation:setDelayPerUnit(1.0 / fps)
    
    -- 添加所有幀到動畫中
    for _, frame in ipairs(frames) do
        animation:addSpriteFrame(frame)
    end
    
    AnimationLoader.cache[name] = animation
    return animation
end

-- 創建動畫精靈
function AnimationLoader.createAnimatedSprite(name, fps, width, height, loop, pingpong, playInterval)
    if not AnimationLoader.base_path then
        print("AnimationLoader:createAnimatedSprite: 請先使用 setBasePath 設定基礎路徑")
        return nil
    end
    
    -- 確保名稱有 v2p_ 前綴
    if not name:match("^v2p_") then
        name = "v2p_" .. name
    end
    
    -- 讀取 metadata
    local metadata = AnimationLoader.loadMetadata(name)
    if metadata then
        fps = fps or metadata.fps
    end

    -- Check data version
    if not AnimationLoader.checkVersion(metadata) then
        print("AnimationLoader:createAnimatedSprite: 警告：動畫資料版本不相容，將無法正常運行")
        return nil
    end
    
    loop = loop ~= false  -- 如果未指定，默認為 true
    pingpong = pingpong or false  -- 是否使用反覆播放模式
    
    -- 創建動畫
    local animation = AnimationLoader.createAnimation(name, fps)
    if not animation then
        return nil
    end
    
    -- 創建第一幀的精靈
    local output_format = (metadata and metadata.output_format or "PNG"):lower()
    local firstFrameName = string.format("%s_%d.%s", name, 0, output_format)
    local sprite = cc.Sprite:createWithSpriteFrameName(firstFrameName)
    
    if not sprite then
        print("AnimationLoader:createAnimatedSprite: 無法創建精靈")
        return nil
    end
    
    -- 添加縮放功能：如果指定了寬度和高度，則進行縮放
    if width and height then
        local contentSize = sprite:getContentSize()
        local scaleX = width / contentSize.width
        local scaleY = height / contentSize.height
        sprite:setScale(scaleX, scaleY)
    end
    
    -- 再次確認動畫物件有效，避免 Animate:create 失敗
    if not animation or tolua.isnull(animation) then
        print(string.format("AnimationLoader:createAnimatedSprite: 動畫物件無效 %s", name))
        return nil
    end
    
    -- 創建動畫動作
    local animate = cc.Animate:create(animation)
    local action
    
    if loop then
        if pingpong then
            -- 創建反覆播放動作
            local reverse = animate:reverse()
            local sequence
            if playInterval and playInterval > 0 then
                local pause = cc.DelayTime:create(playInterval)
                sequence = cc.Sequence:create(animate, reverse, pause)
            else
                sequence = cc.Sequence:create(animate, reverse)
            end
            action = cc.RepeatForever:create(sequence)
        else
            -- 一般循環播放
            local sequence
            if playInterval and playInterval > 0 then
                local pause = cc.DelayTime:create(playInterval)
                sequence = cc.Sequence:create(animate, pause)
            else
                sequence = cc.Sequence:create(animate)
            end
            action = cc.RepeatForever:create(sequence)
        end
    else
        -- 單次播放
        action = animate
    end
    
    -- 運行動畫
    sprite:runAction(action)
    
    return sprite
end

-- 預載指定資料夾中的所有動畫
function AnimationLoader.preloadAnimations()
    assert(AnimationLoader.base_path, "AnimationLoader:preloadAnimations: 請先使用 setBasePath 設定基礎路徑")
    
    -- 使用 cc.FileUtils 獲取目錄下的所有檔案
    local fileUtils = cc.FileUtils:getInstance()
    local files = fileUtils:listFiles(AnimationLoader.base_path)
    
    for _, file in ipairs(files) do
        if file:match("_metadata.json$") then
            local name = file:gsub("_metadata.json$", "")
            local metadata = AnimationLoader.loadMetadata(name)
            if metadata and metadata.fps then
                AnimationLoader.createAnimation(name, metadata.fps)
            end
        end
    end
end

-- 獲取已載入的動畫列表
function AnimationLoader.getLoadedAnimations()
    local animations = {}
    for key, _ in pairs(AnimationLoader.cache) do
        table.insert(animations, key)
    end
    return animations
end

-- 卸載指定動畫
function AnimationLoader.unloadAnimation(name)
    AnimationLoader.cache[name] = nil
end

-- 清理快取
function AnimationLoader.clearCache()
    AnimationLoader.cache = {}
end

-- 釋放資源
function AnimationLoader.releaseUnusedResources()
    cc.SpriteFrameCache:getInstance():removeUnusedSpriteFrames()
    AnimationLoader.clearCache()
end

return AnimationLoader
