# CareSpace 3D 首次使用改善 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. 若執行環境沒有此技能，依本文件核取方塊逐項實作與驗收。**2026-09-10 第二輪更新：先讀本節「第二輪待辦」。原 Task 1–5 已有改版實作，後段保留為歷史規格，不可從頭重做。此次只更新文件，未實作第二輪待辦。**

## 第二輪複測結論與施工入口（最新）

來源：[第二輪使用體驗](../../ux/2026-09-10-first-visit-report.md)。本輪在約 462×514 的內建瀏覽器以 Computer Use 重測，三基準案例仍依序為「可通行／阻斷／未知」。

已實際確認：核心條件上移、還原成功訊息、查詢摘要與預設／自訂標記、browse 捲頁與 camera 縮放、Esc 退出、窄版 RGB／深度切換及關閉後焦點返回。端點編輯明確啟用後也能更新並退出。這些功能應保留。

其他任務的 [既有施工驗收](../../ux/viewer-improvement-acceptance.md) 記載更廣的測試與後續至少 16px 字級調整；那是另一份驗收的證據，不代表本輪重新完成所有測試。**舊 Task 4 的 12px／14px 建議已被 16px 方向取代，不可拿縮小字體當作縮短頁面的方法。**

### 第二輪範圍與保護條件

- 本次修改僅限以下 R2-01～03 及必要驗收；不重排整個工作台、不重做已通過的互動模式。
- 保留所有文字至少 16px、主要操作區至少 44px 高；靠去除重複資訊與按需展開節省空間。
- 保留目前模型、影格、資料與判定契約；不重跑模型、不重裝依賴、不改寫 artifacts。
- 不把三案例預期值寫入 UI 的判定邏輯；基準不符時回報案例名稱、方法、畫面判定。
- 優先 R2-01，再 R2-02；R2-03 是局部說明補強。沒有本輪證據支持的全面重設計不在範圍。

### R2-01：把端點設定與模型連起來（P1）

**問題證據：** 點「設定終點 G」後仍停在端點欄位，畫布不在可視範圍；本輪需向上捲兩次才看到可點地面。模式啟用及放置都正常，故修的是操作銜接，不是端點計算。

**Files:** `viewer/app.js` 的 `bind()`、`setInteractionMode()`；必要時 `viewer/style.css` 的 viewport 焦點樣式。

- [ ] 增加只由設定 S/G 按鈕呼叫的 `beginEndpointEdit(kind)`，參數限 `start | goal`。同一按鈕再次點擊仍退出 browse，不捲頁。不要在一般 `setInteractionMode()` 裡加入無條件 scroll，避免還原、切案例或 Esc 跳頁。
- [ ] 進入時若畫布不完整可見，將其帶到畫面；若已可見，不移動頁面。將鍵盤焦點移至既有 `ui.viewport`，用 `preventScroll` 防止第二次跳動。不得移動相機、重設半徑或改端點。
- [ ] 整合骨架如下，取代現有兩個設定按鈕事件，不新增重複 listener：

```js
function beginEndpointEdit(kind) {
  if (pick === kind) { setInteractionMode('browse'); return; }
  setInteractionMode(kind);
  const rect = ui.viewport.getBoundingClientRect();
  if (rect.top < 0 || rect.bottom > window.innerHeight) {
    ui.viewport.scrollIntoView({ block: 'center', behavior: 'auto' });
  }
  ui.viewport.focus({ preventScroll: true });
}
ui.pickStart.addEventListener('click', () => beginEndpointEdit('start'));
ui.pickGoal.addEventListener('click', () => beginEndpointEdit('goal'));
```

- [ ] 保留模式提示的 role=status 與 viewport 的 aria-describedby；確認提示能辨識目前設定 S 或 G。不要另外重複播報同一訊息。
- [ ] 在 462×514 從下方欄位點 G：無須手動捲頁即可點地面；只有 G 更新，回 browse。重測 S；在模型已完整可見的寬版，進入編輯不改頁面位置。
- [ ] 焦點進 viewport 後按方向鍵只微調選定端點；Esc 後再按方向鍵不改端點。還原與切案例不因本改動強制跳至模型。短於畫布的極短視窗不要求整個畫布同屏，但必須能看見可點地面並退出。

**完成條件：** 明確選端點後不再需要找模型；計算、數值輸入與瀏覽防誤點維持原狀。這是 UI 銜接，主要以真實瀏覽器操作驗收，不用寫比對函式原始碼的測試。

### R2-02：精簡重複說明，保留大字與證據意義（P1）

**問題證據：** 模型下方同時顯示 `pointsHint`、`interactionHint`、圖例與 `.view-help` 的重複相機操作敘述。約 462×514 下，這些區域與工具列占掉相當多可視高度。

**Files:** `viewer/index.html` 的工具 footer、`pointsHint`、`.view-help`；`viewer/app.js` 的 `setInteractionMode()`；`viewer/style.css`。

- [ ] `.view-help` 只保留「實線：自由通路 · 虛線：待觀測候選路線」，移除其第二行「操作 3D 模式…」。相機操作說明只由 `interactionHint` 提供。
- [ ] 採用以下單一模式提示，保留必要動作與退出方式：browse「瀏覽模式：可直接捲頁；旋轉模型請選『操作 3D』。」；camera「操作 3D：拖曳旋轉、捲輪縮放；完成操作或 Esc 退出。」；start/goal「設定起點 S／終點 G：點地面放置，或用方向鍵微調；Esc 退出。」對兩種端點分別顯示，不直接顯示斜線合併文案。
- [ ] 點雲的長說明放入一個原生 details「圖層說明」，保留 `pointsHint` 唯一 ID 與對應 aria-describedby。不要折疊三態結果、未知警示、目前模式或實虛線說明；圖例仍直接可見。
- [ ] 保留字級，不再為研究條件／結果增加大塊固定導覽。若微調 margin，只調相關 footer 規則，避免全頁密度再次改變。
- [ ] 同位置截圖比較 462×514：工具、模式提示與圖例可讀；模式訊息不重複；字級不低於16px；可點工具不小於44px。開啟圖層說明、切點雲、切 camera／browse／S／G 都正常。

**完成條件：** 新手仍知道怎麼操作、線條代表什麼；熟悉後不用反覆讀同一段相機操作。不要以「首屏一定塞入所有控制和完整模型」作不合理驗收。

### R2-03：在停用的差異圖層旁解釋原因（P2）

**Files:** `viewer/app.js` 的 `updateDiagnostics()`、`viewer/index.html` 圖層說明。

- [ ] 重用現有是否有配對基線的判斷；不建立另一套方法名稱白名單。`showDifference` 停用時，於 R2-02 的圖層說明提供「此方法目前沒有可配對的基線，無法顯示方法差異。」
- [ ] 將說明 ID 加入 showDifference 的 aria-describedby；disabled checkbox 本身不能作唯一鍵盤說明入口，details summary 必須可聚焦。不要只放 title tooltip。
- [ ] 有可用基線時移除上述停用原因，保留「方法分歧不等於真值誤差」與配對資訊。切方法後原因與 enabled 狀態一致。
- [ ] 驗收 RGB-D 全部觀測停用情境及介面提供的可配對方法；確認新增說明不改查詢判定、不自動切 DA3、不自動開圖層。

### 第二輪交付與尚未驗收

- [ ] 執行既有 Node 回歸命令：`node --test tests/browser-planner.test.mjs tests/browser-rendering.test.mjs tests/browser-diagnostics.test.mjs tests/browser-interaction.test.mjs`。此命令在本輪體驗期間沒有重跑，下一次施工應自行執行。
- [ ] 三基準案例再照順序驗證。每例固定 RGB-D 全部觀測、重建證據、還原，記錄半徑與判定。
- [ ] 對 R2-01～03 記錄實際操作、結果、視窗尺寸與截圖。桌面、真實觸控、200% 縮放、完整鍵盤／讀屏，做到哪項寫哪項；不能沿用前次文件當本次通過。
- [ ] 回報只完成了哪些 R2 項目與仍未測項目，保留第一輪與第二輪時間脈絡。

**交給下一個 Codex／Claude Code 的最新起始指令：**

> 請依本文件最前方「第二輪待辦」實作 R2-01、R2-02、R2-03，保留現有已完成的 Task 1–5 與至少16px字級。先改善設定端點後找不到模型的操作銜接，再精簡重複提示及補上停用圖層說明。不要重做歷史計畫、不重跑模型、不改研究資料；按第二輪驗收條件測試並回報。

---

## 第一輪施工規格（封存參考，不是目前待辦）

以下 Goal、檔案地圖、Task 1–5 與尾端起始指令是改版前規劃。未勾選狀態保留原始檔，**不表示現有功能尚未實作**；其中舊字級數值以本文件第二輪保護條件為準。

**Goal:** 讓首次進站使用者在窄視窗也能找到條件、還原實驗、理解三態判定並探索證據。

**Architecture:** 保留原生 HTML/CSS/JavaScript 與 Three.js 工作台，重組核心控制區及結果摘要；新增小型互動狀態模組，不改重建或通行演算法。DOM 保持單一控制項來源，避免桌面／手機各一套選單造成同步問題。

**Tech Stack:** ES modules、Three.js 0.174.0、原生 dialog、Node 內建 test runner；既有 localhost 靜態伺服器。

## Global Constraints

- 需求來源：[第一次使用體驗紀錄](../../ux/2026-09-10-first-visit-report.md)，主要涵蓋 UX-01 至 UX-09。
- 本輪只改善 viewer 與必要測試／說明，不重新跑模型、不重裝、不刪除或重寫 `artifacts/`。
- 不新增框架、不升級 Three.js、不新增 CDN、不部署、不建立後端。
- 不更改 `viewer/planning.js` 的半徑膨脹、未知處理、四鄰接與邊界規則。
- 判定必須由當前方法的重建網格計算，不可由案例名稱或預期答案硬編碼。
- 保存比較表使用原始端點／預設半徑；目前查詢使用當前端點／半徑。不得混用。
- 標註參考仍是選用視覺對照，不能變成重建證據。
- 保留 `docs/viewer-contract.md` 與 `docs/DESIGN.md` 的研究邊界、中文介面、既有色彩。
- 先完成 Task 1–3，再做 Task 4–5。每項驗收通過後再進下一項。
- 若指定三案例判定不符，回報「案例名稱、方法、畫面判定」並停下相關變更；不要自行重建資料來讓畫面通過。
- 現有工作若有未提交修改，不覆寫；本規劃沒有要求 commit、push 或 merge。

## 現況與檔案地圖

| 檔案 | 已確認的責任 | 本計畫處理 |
|---|---|---|
| `viewer/index.html` | 控制區、3D、比較表、結果／量測、影格 dialog | 調整 DOM 區塊順序、摘要與提示、互動控制 |
| `viewer/style.css` | 1180px／700px 斷點；700px 以下 scene order=-2、evidence order=-1 | 重做窄版操作順序、可讀性與預覽布局 |
| `viewer/app.js` | `selectCase`、`selectMethod`、`replan`、`bind`、`endPointer`、`openFrameDialog` | 接上互動模式、查詢摘要、還原回饋；保留計算 |
| `viewer/planning.js` | BFS、端點解析、障礙狀態查詢 | 保持不變，執行既有回歸測試 |
| `viewer/rendering.js` | render scheduler／資源釋放 | 保持不變，避免新增永久動畫迴圈 |
| `viewer/diagnostics.js` | 方法差異診斷 | 保持不變，保留顯示入口 |
| `viewer/interaction.js`（新增） | 純函式：互動權限、查詢是否為預設 | Task 2–3 共用 |
| `tests/browser-interaction.test.mjs`（新增） | 新互動純函式的行為測試 | 用 Node test runner 執行 |
| `docs/viewer-contract.md` | 使用行為契約 | Task 5 更新 |

進場先讀上述檔案與當地 AGENTS.md；本次讀到的程式可能在後續施工前已變動，應以函式／元素 ID 定位，不盲套行號。`package.json` 只有 serve 指令，沒有 npm test。伺服器已在 8840 執行時直接重用。

## Task 1：核心操作與結果靠近（P0；UX-01、05）

**Files:** 修改 `viewer/index.html`、`viewer/style.css`。

**Interfaces:** 保留 `caseSelect`、`methodSelect`、`reconMode`、`oracleMode`、`resetQuery` 等 ID，各存在一次；後續 JS 不因版型切換而更換節點。

- [ ] 將研究條件第一個 section 移為 `.query-panel`，包含案例、方法、檢視來源與 `resetQuery`。原端點 section 不再擺第二顆同 ID 的還原按鈕。
- [ ] 將目前判定與原因抽成獨立 `.result-panel`，保留 `resultStatus`、`resultReason`、`statusDot` 及原有 polite live region。3D 角落的狀態仍可作為視覺副本，維持 aria-hidden，避免重複宣讀。
- [ ] 窄版的實際 DOM 閱讀／Tab 順序設為「條件 → 結果 → 3D → 進階查詢 → 方法比較 → 研究證據」。不要只用 CSS order 讓視覺與鍵盤順序相反。3D 可仍是最大視覺區，但不可排在案例入口前面。
- [ ] 方法比較從 `.scene-column` 抽為可獨立布局的區塊；先移除舊窄版 order 規則，再以 grid areas 排桌面。以下是布局骨架，需同步設定各區塊的 grid-area：

```css
.layout { display: grid; grid-template-columns: 260px minmax(0,1fr) 290px;
  grid-template-areas: "query scene result" "controls scene evidence" "controls comparison evidence"; }
.query-panel { grid-area: query; }
.result-panel { grid-area: result; }
.scene-column { grid-area: scene; }
.controls { grid-area: controls; }
.comparison-panel { grid-area: comparison; }
.evidence { grid-area: evidence; }
@media (max-width: 1180px) {
  .layout { grid-template-columns: 240px minmax(0,1fr);
    grid-template-areas: "query scene" "result scene" "controls comparison" "evidence evidence"; }
}
@media (max-width: 700px) {
  .layout { grid-template-columns: minmax(0,1fr);
    grid-template-areas: "query" "result" "scene" "controls" "comparison" "evidence"; }
  .query-panel, .result-panel, .scene-column, .controls, .comparison-panel, .evidence { min-width: 0; }
}
```

- [ ] 視窗高度約 514px 時不要硬把所有控制塞進一屏；驗收目標是案例／方法先可發現，還原與結果相鄰，不再跨越比較表與研究量測。避免大面積 sticky 擠壓 3D。
- [ ] 在 462×514、390×844、1280×800 用 UI 驗證：不靠搜尋 DOM 也能找到案例與方法；還原後可在緊鄰處看到結果；頁面無水平溢出。按 Tab 核對順序。

**完成條件：** 三個案例仍能按原名稱選取並驗證；桌面仍有足夠 3D 區域，窄版不必先讀比較表才能切案例。這是布局調整，用實際瀏覽器驗收即可，不需要為 CSS 寫字串比對測試。

## Task 2：明確分開頁面瀏覽、3D 操作、端點編輯（P0/P1；UX-02、08）

**Files:** 新增 `viewer/interaction.js`、`tests/browser-interaction.test.mjs`；修改 `viewer/app.js`、`viewer/index.html`、`viewer/style.css`。

**Interfaces:** `canPlaceEndpoint(mode)` 回傳是否允許地面點擊；`mode` 只允許 `browse | camera | start | goal`。此模式存在目前頁面，不需要存入 localStorage。

- [ ] 先寫並執行行為測試，確認新增模組尚未存在時測試失敗：

```js
// tests/browser-interaction.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { canPlaceEndpoint } from '../viewer/interaction.js';
test('瀏覽與相機操作不能改端點', () => {
  assert.equal(canPlaceEndpoint('browse'), false);
  assert.equal(canPlaceEndpoint('camera'), false);
});
test('只有明確設定端點模式可以改端點', () => {
  assert.equal(canPlaceEndpoint('start'), true);
  assert.equal(canPlaceEndpoint('goal'), true);
  assert.equal(canPlaceEndpoint('invalid'), false);
});
```

- [ ] 建立最小純函式：

```js
export function canPlaceEndpoint(mode) {
  return mode === 'start' || mode === 'goal';
}
```

- [ ] `app.js` 將預設 `pick` 改為 `browse`，增加單一 `setInteractionMode(mode)`：browse 時停用 OrbitControls 並讓 canvas `touch-action:auto`；camera 時啟用 OrbitControls 並設 `touch-action:none`；start/goal 時停用 OrbitControls，顯示明確地面選點提示。檢查這個 Three.js 版本的 wheel listener 是否仍攔截預設事件，不能只以 enabled=false 當作驗收完成。
- [ ] 新增「操作 3D／完成操作」控制；既有起終點按鈕改文案為「設定起點 S／設定終點 G」。每次模式切換更新 aria-pressed、游標與一行提示；Esc 返回 browse。退出按鈕應在 viewport 外，保證仍能操作。
- [ ] 在 `endPointer()` 現有按鈕／移動距離檢查前增加 `if (!canPlaceEndpoint(pick)) return;`。成功放置端點後返回 browse。保留現有射線、snap 與 replan，不複製計算邏輯。`keydown` 方向鍵更新也加同樣 gate；編輯模式下保留連續方向鍵微調，直到 Esc 或完成。
- [ ] `selectCase()` 與明確還原時返回 browse；`fitView`／`topView` 在任何模式都可使用且不開啟端點編輯。
- [ ] 執行 `node --test tests/browser-interaction.test.mjs`，然後實際驗證下表。純函式測試不能代替捲動測試。

| UI 操作 | 必須結果 |
|---|---|
| 初始載入後在 canvas 上捲輪 | 頁面捲動，模型不縮放 |
| 初始載入後點擊地面 | S/G 座標不變 |
| 開「操作 3D」再拖曳／捲輪 | 視角旋轉／縮放，端點不變 |
| 按「完成操作」或 Esc 再捲動 | 頁面正常捲動 |
| 設定 S → 點地面 | 只更新 S；顯示自訂查詢，回到 browse |
| 設定 G → 方向鍵 → Esc | 只微調 G；退出後方向鍵不改端點 |
| 拖曳距離超過既有 5px 門檻 | 不意外觸發端點點選 |

**完成條件：** 頁面捲動不必尋找畫布外窄邊；不進入端點設定就不會修改查詢。

## Task 3：還原回饋、目前條件與白話判定（P1；UX-03、04、05、09）

**Files:** 修改 `viewer/interaction.js`、`tests/browser-interaction.test.mjs`、`viewer/app.js`、`viewer/index.html`、`viewer/style.css`。

**Interfaces:** 新增 `isBaselineQuery(query, baseline)`；兩者均為 `{ radius: number, start: [number,number], goal: [number,number] }`。baseline 取 `study.body.radius` 與 `currentMethod.result.start/goal`，不得用畫面是否顯示「可通行」判斷是否為預設。

- [ ] 為「還原成功」新增 `queryFeedback` role=status；只在明確按還原時寫入「已還原實驗端點與半徑（0.30 m）。」半徑值依資料格式化，不硬編碼。
- [ ] 將原 resetQuery handler 抽成 `restoreExperimentQuery()`，仍只做既有半徑、兩端點與 replan，並接 Task 2 的 browse 與上述回饋。新增 `querySummary` 顯示案例／方法／來源／半徑；新增 `queryMode` 顯示「實驗預設」或「自訂查詢」。所有方法入口、案例切換、半徑與座標輸入都更新摘要。
- [ ] 加入下列測試再實作 helper：

```js
import { isBaselineQuery } from '../viewer/interaction.js';
test('自訂半徑或端點不能冒充保存條件', () => {
  const b = {radius:.3,start:[1.25,3.05],goal:[6.75,3.05]};
  assert.equal(isBaselineQuery(b,b), true);
  assert.equal(isBaselineQuery({...b,radius:.4},b), false);
  assert.equal(isBaselineQuery({...b,start:[1.35,3.05]},b), false);
  assert.equal(isBaselineQuery({...b,radius:NaN},b), false);
});
```

```js
export function isBaselineQuery(query, baseline) {
  const flatten = q => [q?.radius, ...(q?.start ?? []), ...(q?.goal ?? [])];
  const a = flatten(query), b = flatten(baseline);
  return a.length === 5 && b.length === 5 &&
    a.every((v,i) => Number.isFinite(v) && Number.isFinite(b[i]) && Math.abs(v-b[i]) < 1e-6);
}
```

- [ ] 有空白／非法座標時 `queryMode` 顯示「待完成輸入」，沿用現有暫停判定；不要把無效值轉為 0。半徑改變時不重置使用者座標。
- [ ] 保留目前切案例的行為，但在案例旁明說「切換案例會載入該案例第一個方法與實驗端點；半徑保留。要驗證保存結果，請按還原。」方法切換仍保留目前查詢。不要在此次改善偷偷改成每次切方法都還原。
- [ ] 採用以下文案，把技術細節置於可展開「判定依據」；同一狀態所有位置用相同名稱：

| 情境 | 新手主句 | 保留細節 |
|---|---|---|
| 可通行 | 在目前觀測與模型條件下，找到可連通的自由路徑。 | 已知自由空間存在四鄰接通路；原模型限制 |
| 阻斷，沒有樂觀通路 | 即使把未知區暫視為可走，仍找不到連通路徑。 | 原始 reason |
| 阻斷，端點問題 | 起點或終點位於障礙範圍或研究邊界外。 | 障礙膨脹區說明 |
| 未知 | 目前觀測不足，還不能確認這條路是否可通行。 | 端點或路徑穿越未觀測區域；虛線為候選路線 |

- [ ] 判定主句根據 replan 實際分支設定，不用中文 reason 的字串比對猜分支。`renderComparison()` 將 passable 的「可通」統一為「可通行」。比較表標題附近改為「保存實驗結果（原始端點／預設半徑）」。
- [ ] 方法旁補充「全部觀測＝此案例已保存的全部影格，不表示房間每處都已觀測。」將「即時計算」改為「目前查詢計算」，頂部補一句「檢視已保存的重建成果；調整端點與半徑只更新通行查詢。」避免聲稱完全沒有任何計算。
- [ ] 驗證自訂半徑 0.40 → 改方法 → 改案例 → 還原：每一步摘要與實際值一致；保存比較表不能跟著自訂查詢改寫。三態白話不能遮蔽不同 blocked 原因。

**完成條件：** 使用者知道正在看哪個方法、是否偏離實驗條件、還原是否成功，也知道「未知」不是「阻斷」。

## Task 4：證據可讀性與影格預覽（P1/P2；UX-06、07）

**Files:** 修改 `viewer/index.html`、`viewer/style.css`、`viewer/app.js` 的 `openFrameDialog()`／dialog bindings。

**Interfaces:** 保留 `showPoints`、`fitView`、`topView`、`dialogRgb`、`dialogDepth`、`dialogDepthMissing`；不改影格檔案來源與方法分流。

- [ ] 圖例／操作說明移入 3D 區域外的 footer row，減少工具、圖例遮住地面。窄版說明至少 12px、一般說明 14px、主要操作文字 14px；按鈕觸控區至少 44px 高。這些是本專案驗收目標，非宣稱已完成標準稽核。
- [ ] 保留預設點雲開啟，給「觀測點雲」加短說明「關閉可看清地面分區與路線」。不要自動關閉造成使用者以為重建資料消失；俯視／全景維持直接按鈕。
- [ ] 為 RGB／深度新增窄版切換控制，兩顆 button 使用 aria-pressed；寬版並排、窄版只顯示選取影像。以單一 dialog 同時支援兩種布局，不能複製圖片節點與 ID。
- [ ] dialog header 設 sticky top:0、背景色不透明；影像區允許捲動。每次開新影格預設 RGB；顯示目前方法與 F 編號。切換深度時沿用感測／預測標籤，缺圖顯示既有 missing 狀態。
- [ ] 可用下列狀態設定配合 CSS，避免改動圖片資料：

```js
function setFramePreview(kind) {
  ui.frameDialog.dataset.preview = kind;
  document.getElementById('previewRgb').setAttribute('aria-pressed', String(kind === 'rgb'));
  document.getElementById('previewDepth').setAttribute('aria-pressed', String(kind === 'depth'));
}
```

```css
.dialog-head { position: sticky; top: 0; z-index: 1; background: white; }
.preview-switch { display: none; }
@media (max-width: 700px) {
  .preview-switch { display: flex; gap: 8px; }
  #frameDialog[data-preview="rgb"] .depth-figure,
  #frameDialog[data-preview="depth"] .rgb-figure { display: none; }
}
```

- [ ] 窄版測試 F0 RGB→深度→Esc，再開 F0；預設回 RGB、方法標籤正確、關閉後焦點回原縮圖。寬版確認仍可並排；200% 縮放下標題／關閉可操作，無被截斷的必要控制。

**完成條件：** 不依賴放大整頁就能讀圖例；窄版不用長距離上下捲動才能比較 RGB 與深度。新增控制需人工鍵盤驗收；不為顏色或文字複製字串測試。

## Task 5：回歸、契約與交付（必要）

**Files:** 更新 `docs/viewer-contract.md`；新增 `docs/ux/viewer-improvement-acceptance.md` 作為實測紀錄。

- [ ] 執行既有計算與資源管理測試及新增互動測試：

```powershell
node --test tests/browser-planner.test.mjs tests/browser-rendering.test.mjs tests/browser-diagnostics.test.mjs tests/browser-interaction.test.mjs
```

- [ ] 若沒有既有伺服器，才在專案根目錄執行 `npm run serve`；不要另起與 8840 衝突的服務。這只啟動靜態檢視，不重建模型。
- [ ] 以 Computer Use 在 462×514、390×844、1280×800 驗收 Task 1–4；尺寸是測試目標，不表示本次原始體驗已測全部。可用瀏覽器可用的 viewport 功能；完成後恢復原視窗設定。
- [ ] 三案例依序選取，每次「RGB-D · 全部觀測／重建證據／還原」：通道開放可通行、沙發移至通道阻斷、觀測不足未知。逐筆記錄方法、半徑、判定及畫面證據。
- [ ] 操作自訂半徑與端點、切方法、切案例、還原、俯視、點雲、RGB／深度、Esc、Tab。核對現在查詢和保存比較表沒有混用；圖層操作不改判定。
- [ ] 檢查標註參考仍有清楚來源說明；不把 DA3 分歧叫作真值錯誤；未知候選路線仍是虛線。這是顯示契約回歸，不是模型精度驗證。
- [ ] 在驗收檔中用「通過／失敗／未測」記錄環境、操作、預期、實際、截圖位置。未取得觸控或讀屏環境時明列未測，不能推定通過。
- [ ] 更新 viewer-contract 的「瀏覽預設、3D 操作模式、端點編輯、還原回饋、窄版影格切換」段落；保留原本科學與資料邊界。
- [ ] 交付時列已完成 Task、測試輸出摘要、仍未驗收項目與前後截圖；不要只回報「UX 已優化」。

## 交給下一個 Codex／Claude Code 的起始指令

> 請先閱讀 docs/ux/2026-09-10-first-visit-report.md 與本計畫，檢查當前程式及 AGENTS.md，按 Task 1–5 順序實作 CareSpace 3D 工作台改善。先完成核心操作布局、明確互動模式與查詢摘要，再做圖例與影格預覽。保留三態判定、保存比較與重建證據邊界，不重新跑模型、不重裝、不刪除或修改 artifacts。每項完成做對應驗收；最後回報三案例判定與未測範圍。計畫中的程式片段是增量設計，整合前要核對現有程式，不可整檔覆蓋。
