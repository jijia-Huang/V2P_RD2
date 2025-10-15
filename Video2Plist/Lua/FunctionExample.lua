-- 設定動畫 Banner
-- animName - 動畫資訊
-- gameName - 遊戲名稱
-- isClipping - 是否裁剪
-- sceneId - 遊戲ID
-- jiliSceneId - 吉利遊戲ID
function GameButton:SetAnimationBanner(animationInfo, sceneId, jiliSceneId)
	local animName = animationInfo.ANIMATION
	local loop = animationInfo.LOOP
	local gameName = animationInfo.GAME_NAME
	local isClipping = true		-- AI banner 一律裁切
	local zOrder = animationInfo.ZORDER
	local playInterval = animationInfo.PLAY_INTERVAL
	
	-- 檢查 animationManager 是否存在
	if not self.m_lobbyView.m_animationManager then
		print(string.format("GameButton:SetAnimationBanner: animationManager not exist, animName: %s", tostring(animName)))
		return
	end
	
	-- 檢查 loader 是否存在
	if not self.m_lobbyView.m_animationManager.loader then
		print(string.format("GameButton:SetAnimationBanner: animationManager.loader not exist, animName: %s", tostring(animName)))
		return
	end

	local isLoop, isPingpong = false, false
	if loop then
		isLoop = true
		if loop == "pingpong" then
			isPingpong = true
		end
	end

	local ani = nil
	-- 安全地調用 createAnimatedSprite，加強錯誤處理
	local success, result = pcall(function()
		return self.m_lobbyView.m_animationManager.loader.createAnimatedSprite(animName, 24, 204, 392, isLoop, isPingpong, playInterval)
	end)
	
	if success then
		ani = result
	else
		print(string.format("GameButton:SetAnimationBanner: createAnimatedSprite 發生錯誤：%s, animName: %s", tostring(result), tostring(animName)))
	end

	if not ani then
		local name = nil
		if animName:match("^v2p_") then
			name = animName
		else
			name = "v2p_" .. animName
		end
		return
	end

	local maskStencilNode = nil
	local picName = ""
	if jiliSceneId ~= nil then
		picName = inn.JiliScenePNG[SizeType.LARGE][jiliSceneId]
	else
		picName = inn.ScenePNG[SizeType.LARGE][sceneId]
	end
	if not cc.SpriteFrameCache:getInstance():getSpriteFrame(picName) then
		NotBrokenCrashReport("GameButton:SetAnimationBanner: not found, picName: " .. picName)
		picName = "img_ani_banner_L.png"
	end
	maskStencilNode = cc.Sprite:createWithSpriteFrameName(picName)

	local size = maskStencilNode:getContentSize()
	local maskClippingNode = nil
	if not isClipping then
		maskClippingNode = cc.Node:create()
	else
		maskClippingNode = cc.ClippingNode:create()
		maskClippingNode:setStencil(maskStencilNode)
		maskClippingNode:setAlphaThreshold(0.5)

		local bannerFrame
		if GET_PLATFORM() == inn.PLATFORM.BEST_777 then
			bannerFrame = cc.Sprite:createWithSpriteFrameName("banner_frame.png")
		else
			bannerFrame = cc.Sprite:createWithSpriteFrameName("img_ani_banner_L.png")
		end
		bannerFrame:setAnchorPoint(cc.p(0.5, 0.5))
		bannerFrame:setPosition(cc.p(size.width / 2, size.height / 2))
		self:addChild(bannerFrame, UI_ZORDER.DYNAMIC_FRAME)
	end

	maskClippingNode:setAnchorPoint(cc.p(0.5, 0.5))
	maskClippingNode:setScale(0.99)
	maskClippingNode:setPosition(cc.p(size.width / 2, size.height / 2))
	self:addChild(maskClippingNode, UI_ZORDER.DYNAMIC)

	self.animation = ani
	maskClippingNode:addChild(self.animation)
	self.maskClippingNode = maskClippingNode

	if gameName and gameName ~= "" then
		local gameNameSprite = cc.Sprite:createWithSpriteFrameName(gameName)

		-- gameNameSprite = nil
		if gameNameSprite then
			gameNameSprite:setAnchorPoint(cc.p(0.5, 0.5))
			gameNameSprite:setPosition(cc.p(0, -130))
			gameNameSprite:setScale(1.1)
			maskClippingNode:addChild(gameNameSprite)

			if inn.BANNER_LOGO_SCALE[sceneId] then
				gameNameSprite:setScale(inn.BANNER_LOGO_SCALE[sceneId])
			end
		end
	end

	if self.animation then
		-- 部分 spine banner 會超框，所以將 video banner zOrder 設為略低於 spine banner zOrder
		self:setZOrder(zOrder or 99)
	end
end
