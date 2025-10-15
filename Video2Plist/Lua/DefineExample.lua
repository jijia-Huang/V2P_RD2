-- 設定 V2P 工具動畫資料夾路徑
inn.ANIMATION_BASE_PATH = "InannaResource/Inanna/videos"

-- 設定動態 Banner
-- ANIMATION V2P動畫檔案
----  LOOP 動畫循環模式 (normal/ pingpong)
----  GAME_NAME 廳館靜態 banner 檔名(不填不顯示)
----  ZORDER video banner 預設 zOrder 為 99
----  PLAY_INTERVAL 動畫播放間隔 (預設無間隔)
----  ENABLE 是否使用動態 banner
local DYNAMIC_BANNER_DEFINE = {
	[inn.SceneIds.TRIPLE_FORTUNE_BAOZHU] = {  -- 招財爆竹
		ANIMATION = "v2p_tripleBaoZhu",
		LOOP = "normal",
		GAME_NAME  = "TRIPLE_FORTUNE_BAOZHU.png",
		IS_CLIPPING= true,
	},
}

inn.DYNAMIC_BANNER_DEFINE = DYNAMIC_BANNER_DEFINE