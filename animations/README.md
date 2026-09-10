# 未知不是自由空間：Manim 原理解說

以Manim Community 0.20.1製作的25.6秒正體中文動畫。影片使用原創2D平面格與射線，
没有ReplicaCAD資料、模型權重或研究影格；不是實验截圖或新的重建成效。

## 重現（Windows / CPU）

從專案根目錄執行，不要安裝進既有 `.venv`：

```powershell
uv venv --python 3.11.15 .venv-manim
uv pip install --python .venv-manim/Scripts/python.exe -r animations/requirements.lock
.venv-manim/Scripts/python.exe animations/render.py
```

需要PATH上的FFmpeg；使用Windows內建Microsoft JhengHei字型，不分發字型檔案。
Cairo renderer使用CPU，不啟用OpenGL，無LaTeX需求。其他OS須提供相容字型並調整FONT；
本次只在Windows驗證。Manim在獨立環境的NumPy/SciPy版本與研究環境不同，不改研究鎖定檔。

輸出 `docs/media/unknown-space.mp4`（1280×720、30fps）及
`docs/media/unknown-space.gif`（960×540、10fps）；中間檔只存artifacts/manim。

## 計算與視覺界線

- `evidence_story.py`：32×20格、格距0.2m、中央障礙；每視角720條射線，遇首個障礙停止。
  每0.15格取樣是解說用2D觀測模型，不是生產RGB-D像素／高度融合。
- `unknown_space.py`：Manim只畫格子、抽樣射線、文字與路徑，不做判定。
- 共用 `src/carespace/planning.py` 的analyze、inflated_states與bfs。
  圓形半徑0.12m，加上既有保守離散化膨脹；虛線為允許未知的候選通路，
  實線只在已知自由膨脹網格連通後出現。不驗證輪椅、真實場景或高度淨空。
- 初始／第一視角／第二視角：unknown／unknown／passable；未知格640／232／4。
  剩餘未知格位於障礙內部，不因動畫結束而強制補滿。
- 可見動畫射線是720条射線的抽樣，用於解說；格子證據使用完整射線集合。

## 來源

Manim Community 0.20.1（PyPI），程式為MIT授權；官方專案
https://github.com/ManimCommunity/manim/tree/v0.20.1 。安裝相依固定在requirements.lock。
完整渲染環境與產物SHA256見provenance.json。原創動畫程式與輸出適用本專案MIT。
Manim／依賴的上游授權不因輸出授權而改變，不複製3Blue1Brown影片或素材。

## 驗收

觀測程式執行前置斷言：射線不把障礙標為自由、既有障礙不被新視角消除、
第一視角終點仍未知、第二視角通路由既有規劃器產生。抽查開頭、遮擋、
補觀測與結尾畫面，確認正體中文字、圖例、S/G、候選虛線及實線。
這是原理解說，不改動artifacts/study.json，也不增加新模型實驗。
