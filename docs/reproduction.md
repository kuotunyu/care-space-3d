# 安裝與操作指南

[回到專案首頁](../README.md) · [三分鐘展示](demo-guide.md)

## 現有工作目錄直接執行

PowerShell，工作目錄 `D:\AI-Portfolio\CC_github部隊\care-space-3d`：

```powershell
.venv/Scripts/python -m pytest -q
node --test tests/browser-*.test.mjs
./scripts/serve.ps1
```

`serve.ps1` 只綁定 127.0.0.1，若 port 被占用就停止，不會殺其他程序。可改
`./scripts/serve.ps1 -Port 8841`。本次執行的 PID/port 記錄在 `artifacts/server.json`。
要關閉自己啟動的 server：確認該檔 PID 與命令後 `Stop-Process -Id <該PID>`。

操作：選擇正常／沙發移至通道／觀測不足案例，切換 RGB-D 或 DA3、全部或取樣觀測。
預設瀏覽模式可直接捲動頁面，點圖不改端點；按「操作 3D」才拖曳旋轉／捲輪縮放。
按「設定起點 S／設定終點 G」再點地面，或直接輸入座標；選點後回到瀏覽，Esc 可退出。
調整圓柱半徑可重新分析。端點圓環標示圓柱半徑。
設定 S/G 時，畫布未完整可見會自動帶入畫面並聚焦，方向鍵可直接微調。
介面文字至少 16 px；圖層說明可展開，包含方法差異停用原因或目前配對。
切換方法會保留目前端點；「還原實驗端點與半徑」回到預設查詢。比較表保留原始實驗結果。
查詢摘要顯示案例、方法、來源與半徑；「實驗預設／自訂查詢／待完成輸入」反映實際條件，
還原後顯示成功訊息。窄版影格可切換 RGB／深度，寬版仍並排。
「回到全景／俯視分析」切換視角；實線是自由通路，虛線是尚待觀測的候選路線。
參考幾何需明確切換，僅疊加顯示。藍灰點雲來自觀測深度，橘色低柱只是障礙投影。
紫色狹窄帶以距已知障礙的半徑淨空 0.30–0.60 m 顯示，沒有醫療或法規意義。
觀測影格的「預覽張數」只改縮圖和相機標記；選擇重建方法才切換其觀測子集。
展示在操作與資料變更時重繪，閒置時不持續渲染。

「檢視 DA3 分歧」會切換至俯視差異圖：標出自由／障礙不一致、已觀測變未知、
未知變已觀測的位置。DA3 必須配對相同影格的 RGB-D；基線不是完整真值。
診斷會指出端點膨脹狀態、基线路徑受限中心；不把單條路徑受阻當作沒有替代路徑。
重新產生診斷報告：`node scripts/build_diagnostics.mjs`。
結果在 [方法差異診斷](diagnostics.md) 與 `artifacts/diagnostics.json`，含完整矩陣、
資料與程式 SHA256；介面直接用同一套程式計算當前查詢，不載入過期診斷快取。

## 首次安裝與執行

以下只供第一次建立新工作目錄；已有本專案的人使用上方「現有工作目錄直接執行」，不需重新下載或重跑研究。
需 Git、curl、uv、Node/npm；uv 會取得 Python 3.11.15。使用 **CPU**，不需 GPU 或 Colab。
所有相依只裝在本專案 venv。

先在 PowerShell 切換到你選定的上層資料夾，確認其下沒有同名 `care-space-3d` 資料夾，再執行：

```powershell
git clone https://github.com/kuotunyu/care-space-3d.git
Set-Location care-space-3d
```

後續命令都在這個 repo 根目錄執行。以下逐行執行，任一步出現錯誤便停止；不要跳過錯誤繼續。

```powershell
uv venv --python 3.11.15 .venv
uv pip install --python .venv/Scripts/python.exe --index-strategy unsafe-best-match -r requirements-cpu.lock
uv pip install --python .venv/Scripts/python.exe --no-deps -e .
npm ci
.venv/Scripts/python scripts/fetch_assets.py
.venv/Scripts/python scripts/fetch_model.py
.venv/Scripts/python scripts/run_study.py
.venv/Scripts/python scripts/run_learning.py
.venv/Scripts/python scripts/build_report.py
.venv/Scripts/python scripts/build_depth_audit.py
node scripts/build_diagnostics.mjs
.venv/Scripts/python -m pytest -q
node --test tests/browser-*.test.mjs
./scripts/serve.ps1
```

Linux 將 `.venv/Scripts/python` 換成 `.venv/bin/python`，啟動 viewer 用
`.venv/bin/python -m http.server 8840 --bind 127.0.0.1`。未修改 Ubuntu-bench。
安裝學習式依賴前也可先只安裝 `-e . pytest==8.3.5 embreex==2.17.7.post6` 跑 CPU 基線。

資料逐檔下載共 **8.67 MB**；只下載一個 **1.34 GB** 模型權重。模型/程式固定 revision
且驗 SHA256；完整安裝版本在 requirements-cpu.lock。上述命令不會建立或推送 GitHub repo，
也不會部署網站或使用付費 API。來源 repository 已公開，研究資產須另外下載。

首次安裝與下載可預留 10～30 分鐘，另留 10～30 分鐘執行研究與診斷；這是操作時間估算，
不是硬體效能保證。既有本機 CPU 學習流程曾記錄約 218 秒，但不能套用到其他電腦或完整安裝。
只開啟已有結果的 Viewer 不需再次執行下載、重建或模型腳本。

`run_study.py` 重新生成基線並歸檔舊 study；`run_learning.py` 逐影格快取可恢復。
場景幾何、RGB/K/姿態、配置與重建版本不一致會拒用舊結果。
原始觀測 NPZ 在 `artifacts/observations/`，學習式 NPZ 在 `artifacts/predictions/`，
主介面資料為 `artifacts/study.json`，完整配置在 `configs/study.json`。

## 結果與研究邊界

見 [自動生成結果報告](results.md)、[精簡設計](design.md)、
[原始碼與資料授權](sources.md)、[DA3 尺度核對](da3-audit.md)、
[失敗紀錄](failure-log.md)。

[深度來源追溯](depth-audit.md) 核對官方尺度／座標工具，並從快取深度追溯障礙格的
影格與像素來源。執行上述 `build_depth_audit.py` 後，可從工作台開啟含 RGB、參考／預測
深度和誤差圖的報告。這是使用合成真值的事後診斷，沒有把真值遮罩送入重建或規劃。
報告也按支援影格數對照全部 DA3 障礙格與 oracle；單影格支援仍包含參考障礙，
不能直接刪除。格子重疊比例不等於路徑錯誤放行率。

[障礙降為未知實驗](abstention.md) 使用固定單影格規則，保留自由格集合，
檢查降低阻斷確定性的代價。執行 `.venv/Scripts/python scripts/run_abstention.py`，
本機開啟 `/artifacts/abstention/index.html`。這是重用既有評估案例的探索性實驗，
不會修改主要工作台的研究結果；未知增加不等於重建成功。

- 全部 RGB-D 的三案例得到可通行／阻斷／未知。DA3 保留開放通道誤判阻斷的負例。
- 每個方法僅 3 個固定 evaluation 查詢，變體共享房間/家具，沒有獨立家庭泛化證據。
- 0.10 m 體素、已觀測射線累積、free/occupied/unknown；unknown 不自動視為 free。
  深度、遮擋與離散化誤差仍然存在。忽略 y<0.10 m 的地面接觸層。
- 模型是半徑 0.30 m、高 1.20 m 直立圓柱，圓形截面不區分轉向；非完整輪椅模型。
  淨空指路徑中心的半徑空間，不是門寬，也不是安全餘裕承諾。
- 學習式方案只拿 RGB＋K 推論；融合使用已知合成相機姿態。未知姿態模式明確未支援；
  沒有假裝定位成功或用 GT 對齊冒充部署能力。所有深度 GT 只在推論後評估。
- 覆蓋選樣讀取所有候選 RGB-D，節省的是融合用量；不宣稱節省拍攝成本。
- false-release 同時報告 oracle 阻斷與預測放行分母；未知比例與決策覆蓋率一起呈現。
- RTX 4090 原本正在忙，本次全部 CPU float32 2 threads；峰值 VRAM 為 null（不適用）。

ReplicaCAD 網站寫 CC BY 4.0，但固定版本 LICENSE.txt 寫 **CC BY-NC 4.0**，尚待官方
釐清；目前採較嚴格的本機非商業研究條件。原始資料、模型權重與派生資料沒有被提交。

## Colab

第一次操作請依 [Colab 明確路徑與停止點](colab-start-here.md)。

[CareSpace3D_CPU_Reproduction_v1_1.ipynb](../notebooks/CareSpace3D_CPU_Reproduction_v1_1.ipynb) 僅安裝/啟動相同核心，不重寫模型與幾何。
執行 `scripts/make_colab_bundle.py` 取得 `artifacts/care-space-3d-source.zip`，放入
自己的 Drive `CareSpace3D/` 後執行 notebook。下載/模型/結果持久保存，可中斷恢復。
Colab CPU 已完成安裝、29 項測試、研究流程及三案例展示；證據見 [驗收紀錄](verification.md)。
這是使用者提供的輸出與截圖驗收，並非 GPU 測試。GPU adapter 尚未驗證。

來源 ZIP 包含 Python／前端測試；Colab 安裝後先跑 CPU 測試，取得 Node 相依後再跑
前端測試。工作台的「保存的研究報告」可開啟深度診斷與降為未知實驗，兩份報告均
使用保存的原始查詢，並在開啟時核對 study 指紋。
