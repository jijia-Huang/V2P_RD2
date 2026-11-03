---
name: v2p-convert
description: 用 V2P 命令列把影片轉成 Cocos2d plist 序列幀動畫（沿用上次設定），轉完自動檢查去背品質，去背不正常就只微調去背容差重跑，直到正常為止。當使用者說「影片轉 plist」「V2P 轉一下」「照上次設定再轉一次」「這支影片幫我去背轉動畫」「去背跑壞了幫我調」「v2p」時使用。
---

# V2P 轉換＋去背自動微調

## 環境

```powershell
$py   = "D:\Conda\envs\GPTAction\python.exe"
$tool = "D:\Tool\newFeature\SouthAsia-Share-Tools\V2P_RD2\Video2Plist\Tool"
& $py "$tool\v2p.py" <子命令> ...
```

- 每個子命令都在 **stdout 輸出一個 JSON**，日誌與進度走 stderr；結束碼 0=成功、1=失敗、2=參數錯誤。
- 解析時用 `| ConvertFrom-Json`。加全域參數 `--quiet` 可關掉進度輸出（全域參數要放在子命令**前面**）。
- 輸出預設在 `$tool\videos\v2p_<名稱>\`（名稱會自動加 `v2p_` 前綴），同名重跑會覆蓋舊輸出。
- 對照圖在 `$tool\bgcheck\v2p_<名稱>\contact_t<容差>.png`。

| 子命令 | 用途 |
|---|---|
| `settings` | 看「上次的設定」（GUI 或 CLI 最後一次成功轉換的參數）與工具路徑 |
| `convert [-i 影片] [-n 名稱] [--tolerance N]` | 轉換；沒給的參數全部沿用上次設定；有開去背就自動附 `check` |
| `check <輸出資料夾>` | 重新檢查已存在輸出的去背品質並產生對照圖 |
| `bg-sweep [-i 影片] --tolerances 4,6,8,...` | 只抽幾格、快速比較多個容差（不產生 plist），產生比較圖 |
| `inspect <輸出資料夾>` / `info <影片>` | 檢查輸出結構／看影片尺寸 |

## 鐵則

1. **微調時只調去背容差 `--tolerance`。** fps、材質尺寸、打包器、格式、品質一律沿用上次設定，不要自己改；縮放尺寸依下一節的規則**每支影片算一次**，之後重跑都用同一組。重跑時只帶第一次用的 `-i`、`-n`、`--resize` 加上 `--tolerance`。使用者明確要求改其他參數才改。
2. 容差意義：去背是從畫面**四個角落**做洪水填充（相鄰像素色差 ≤ 容差就連過去）。
   - 容差太小 → 背景去不乾淨、邊緣留背景色光暈。
   - 容差太大 → 沿著主體的柔邊「漏」進主體，整塊主體被挖掉（常常只發生在某幾格）。
   - 吃主體通常是「超過某個值就崩」的懸崖；殘邊則是漸進的。所以目標是**不吃主體的前提下盡量大的容差**。
   - GUI 範圍 0~50，常用 4~20。
3. 每一輪都要**同時看數據和對照圖**再下結論，不能只看 verdict。
4. 最多重跑 4 輪；超過就停下來回報。

## 縮放尺寸：依影片動態計算

**不要沿用上次的 `target_width/target_height`**（那是上一支影片算出來的）。
規則：**一張材質集（`max_width` x `max_height`，預設 512x512）要能左右並排塞進兩格**，並保持影片原比例。

```
W, H   = 影片原始寬高（用 info 取得）
MW, MH = 上次設定的 max_width, max_height（預設 512, 512）

w = floor(MW / 2)
h = round(H * w / W)
若 h > MH：h = MH；w = round(W * MH / H)      # 很瘦長的影片改以高度為準
```

- 縮放模式固定用 `stretch`：尺寸已經照原比例算，不會變形。
- 範例：1080x1970 → `256x467`（上次 v2p_169 就是這組）；1920x1080 → `256x144`；2160x3938 → `256x467`。
- 算完用 `--resize <w>x<h> --resize-mode stretch` 傳給 convert / bg-sweep。

```powershell
$info = & $py "$tool\v2p.py" info "<影片>" | ConvertFrom-Json   # 取 $info.width / $info.height
```

## 流程

### 1. 確認要跑什麼

```powershell
& $py "$tool\v2p.py" settings | ConvertFrom-Json
```

- 使用者有給影片/名稱就用他的，沒給就沿用上次的影片與名稱。
- 使用者沒給影片、而且 `last_settings.video_path` 是空的（或檔案已不存在）→ 先問使用者要轉哪支影片，不要自己猜。
- 用 `info` 取影片寬高，依上一節算出縮放尺寸。
- 用一行告訴使用者這次會用的設定（影片、名稱、fps、材質上限、算出的縮放尺寸、目前容差），然後直接跑，不用等確認。
- 上次設定沒開去背（`enable_bg_removal=false`）→ 直接轉完回報，不進微調流程（除非使用者要求去背）。

### 2. 轉換

```powershell
$r = & $py "$tool\v2p.py" --quiet convert [-i "<影片>"] [-n <名稱>] --resize <w>x<h> --resize-mode stretch | ConvertFrom-Json
```

失敗（`ok=false`）就把 `error` 回報給使用者並停止，不要亂改參數重試。

### 3. 判讀去背結果

看 `$r.check`：

- `verdict`：`ok` / `under_removed`（去不乾淨）/ `over_removed`（吃到主體）/ `mixed`（兩種都有）/ `review`（只有離群格，需要目視）
- `issues`（會影響 verdict）：
  - `LEAK`：透明區裡有明顯非背景色 → 主體被挖掉 → **調低**
  - `ALL_REMOVED`：整格幾乎全透明 → 多半是吃光主體（但片頭/片尾本來就空的格子也會中）
  - `FRINGE`：主體邊緣很多像素幾乎等於背景色 → **調高**
  - `RESIDUAL`：與已去背區相連處還有背景色色塊 → **調高**
  - `NO_REMOVAL`：某些格幾乎沒去到背景 → 角落不是背景色，或容差太小
  - `OUTLIER_FRAMES`：某些格透明比例和其他格差很多 → 去看那幾格
- `notes` 的 `ENCLOSED`：被主體包住或被裁在畫面邊緣的背景色塊，**洪水填充到不了，調容差無效**。看圖判斷那塊是「主體設計本來就有的顏色」還是「該透明卻沒去掉的背景」，回報時講清楚是哪一種。
- `suggestion.tolerance`：依 verdict 算的下一個建議值（只是起點）。
- verdict 為 `ok` 時 `issues` 是空陣列、`suggestion` 是 null、`frames` 是空陣列，這是正常的，不是解析失敗。

**一定要用 Read 打開 `check.contact_sheet`。** 每格上半是「貼在對比色底上的去背結果」，下半是 Alpha 遮罩（白=保留）。檢查：

- 主體有沒有缺塊、破洞、只剩輪廓 → 吃主體
- 主體外圍有沒有一圈背景色、或角落/邊緣有沒去掉的背景色塊 → 去不乾淨
- 標註 `#編號 T透明% L漏% F殘邊%`，問題格會被優先挑進圖裡

已知誤判（看圖確認後可以忽略）：

- 主體本身有和背景相近的顏色（例如綠幕前的綠衣服）→ 可能誤報 `RESIDUAL`/`FRINGE`；
- 動畫開頭/結尾本來就沒有主體 → `ALL_REMOVED`/`OUTLIER_FRAMES`；
- 縮放模式 `pad_black`/`pad_transparent` 的補邊會干擾角落取色 → 只能回報，不要改縮放模式。

判定為正常（verdict `ok` 且圖上看不出問題，或剩下的都是上面的誤判／`ENCLOSED`）→ 跳到第 5 步。

### 4. 微調容差再跑

記錄每一輪結果，維護兩個界線：

- `low_bad`：判定為「去不乾淨」的最大容差
- `high_bad`：判定為「吃到主體」的最小容差

依序決定下一個容差：

**A. 第一次判定不正常時：先跑一次快速比較（不算一輪）**

```powershell
$sw = & $py "$tool\v2p.py" --quiet bg-sweep [-i "<同一支影片>"] --resize <w>x<h> --resize-mode stretch --tolerances 2,4,6,8,10,12,16,20 | ConvertFrom-Json
```

- `bg-sweep` 沿用上次的 fps；縮放要帶和 convert 同一組 `--resize`。只抽 6 格、不產生 plist。
- 看 `results`（每個容差的 verdict）、`ok_tolerances`、`max_ok_tolerance`，並 Read `sweep_sheet`（每列一個容差）。
- 用 sweep 結果設定**初始**界線：`low_bad` = 判定 under 的最大容差、`high_bad` = 判定 over 的最小容差。
- 下一個完整重跑的容差 = `max_ok_tolerance`（符合「不吃主體下盡量大」）。
  `recommended_tolerance` 是較保守的值，若 `max_ok_tolerance` 完整重跑後吃到主體，就改用它。
- 沒有任何 ok → 用界線中間值（偏低）；sweep 圖也看不出來 → 用 `check.suggestion.tolerance`。
- 整個流程最多跑一次 sweep。

**B. 之後每輪完整重跑仍不正常時**

- 用完整重跑的結果更新界線（完整結果優先於 sweep：例如 sweep 說 8 ok、完整跑 8 吃主體 → `high_bad = 8`）。
- 兩個界線都已知 → 取中間值（取整數，偏向低的那邊，因為吃主體比留一點邊更糟）。
- 只知道一邊 → 用 `check.suggestion.tolerance`（不能超出已知界線）。

重跑：

```powershell
$r = & $py "$tool\v2p.py" --quiet convert [-i "<同一支影片>"] [-n <同一個名稱>] --resize <w>x<h> --resize-mode stretch --tolerance <N> | ConvertFrom-Json
```

回到第 3 步。停止條件：

- 判定正常 → 第 5 步。
- `high_bad - low_bad <= 1`（沒有任何一個容差是乾淨的）→ 選**不吃主體的最大容差**作為最終值，回報這是演算法限制。
- 第一次之後的完整 convert 已經跑了 4 次（sweep 不算）→ 選目前最好的一輪，回報。
- 若最後選定的容差不是最後一次跑的，要用那個容差**再 convert 一次**，讓輸出檔與「上次設定」一致（每次成功的 convert 都會把參數存成上次設定）。

### 5. 回報使用者

簡短列出：

- 最終容差、輸出資料夾（`result.output_dir`）、影格數、plist 數
- 每輪紀錄：容差 → 判定（一行一輪）
- 最後一張對照圖路徑（完整路徑）
- 調容差解決不了的問題（`ENCLOSED`、演算法限制、誤判說明），以及建議（例如換純色背景、避免主體貼邊）
