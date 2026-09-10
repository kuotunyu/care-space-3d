"""Generate a compact Chinese report from persisted evidence, never hand-enter scores."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/"artifacts/study.json").read_text(encoding="utf8"))
label={"passable":"可通行","blocked":"阻斷","unknown":"未知"}
rows=["# CareSpace 3D 本機實驗報告", "", "固定模型：半徑 0.30 m、高 1.20 m 的直立圓柱；平坦已知支撐面。",
"高度分析忽略 y<0.10 m 接觸層；高度向上取整到體素邊界。不是完整輪椅模型，也不是長者安全驗證。", "",
"本報告由 artifacts/study.json 自動生成。資料為程式化房間與原尺度 ReplicaCAD 家具，重新著色；未使用原始公寓布局。",
"3 個 evaluation 配置共用房間與資產，只能視為同一受控實驗家族，不能當作 3 個獨立家庭。", "",
"| 場景 | 方法 | 判定 | 影格 | 已觀測 | 深度 MAE | 推論＋融合秒 |", "|---|---|---|---:|---:|---:|---:|"]
for c in a["cases"]:
    if c["split"]!="evaluation":continue
    for m in c["methods"]:
        x=m["metrics"];mae=x.get("depth_mae_m")
        rows.append(f"| {c['title']} | {m['label']} | {label[m['result']['status']]} | {len(m['selected_frames'])} | {x['observed_fraction']:.1%} | {f'{mae:.3f} m' if mae is not None else '—'} | {x['runtime_seconds']:.2f} |")
rows += ["", "每種方法只有 3 個固定查詢，樣本很小；MAE 以所選有效像素加權。RGB-D 使用無噪聲合成深度，故不是感測器實測誤差。",
"方法秒數為原始各影格推論時間加本次融合時間；快取重用不重新消耗相同推論時間。完整軌跡不代表完整觀測幾何。", "",
"| 方法 | N | 可通／阻斷／未知 | 決策覆蓋率 | 錯放／oracle 阻斷 | 錯放／預測可通 |", "|---|---:|---|---:|---|---|"]
for name,m in a["classification_metrics"].items():
    if not name.startswith("evaluation/"):continue
    counts=m["counts"]
    released=m["false_release_count"]
    rows.append(f"| {name.split('/')[1]} | {m['n_queries']} | {counts['passable']}/{counts['blocked']}/{counts['unknown']} | {m['decision_coverage']:.1%} | {released}/{m['oracle_blocked_count']} | {str(released)+'/'+str(m['predicted_pass_count']) if m['predicted_pass_count'] else 'N/A（沒有放行）'} |")
rows += ["", "錯誤放行：預測可通行、oracle 判阻斷。兩個分母分別為 oracle 阻斷查詢數，以及預測可通行查詢數；零分母為 N/A。",
"未知查詢仍計入 N，決策覆蓋率=(可通＋阻斷)/N；另保存完整三態 confusion matrix。",
"DA3 的正常場景誤判阻斷，是必須保留的負結果；沒有錯誤放行不代表辨識成功。", "",
"## 觀測與尺度", "",
"全部＝宣告軌跡 24 張（觀測不足案例只有 1 張）；固定間隔＝8 張；覆蓋選樣＝以各候選 RGB-D 的已知體素欄覆蓋貪婪選 8 張。",
"覆蓋選樣先讀過所有候選深度，因此只節省融合用量，沒有證明節省拍攝或感測成本；選樣耗時另存於每個 case。",
"DA3 對照使用相同全部／固定間隔影格，沒有拿 RGB-D 覆蓋選樣的深度資訊當作 RGB-only 選樣能力。",
"已知姿態實驗：DA3 只讀 RGB＋K，使用固定 focal/300 轉換；融合使用已知合成姿態，沒有真值尺度擬合。",
"未知姿態：所選單目 Metric 模型不支援，因此沒有相機定位誤差或定位失敗率數字；資料中的 null 不是 0。", "",
"## 幾何限制與失敗", "",
"以實際像素中心射線、0.05 m 步長累積 0.10 m 體素；每兩條有效射線取一條。未觸及體素保留未知；occupied 優先。",
"每個 XZ 欄的全部高度體素都有自由證據才成為自由欄。這是離散體素證據，不是對每個連續體積點的量測保證。",
"足跡膨脹增加 sqrt(2)×網格解析度；4 鄰接路徑避免穿角。淨空為路徑中心到非自由體素/邊界的最小距離扣除半格對角線，單位是半徑淨空，不是門寬。",
"淨空差是各方法路徑瓶頸與 oracle 路徑瓶頸之差；不是同一位置的配準誤差。oracle 由完整三角形獨立投影離散化，仍受解析度與投影填孔假設限制。",
"家具改動會改 scene ID、生成新觀測、基線、oracle 與模型快取；不同方法不共享可變的舊幾何。",
"細薄物件、透明/反射、坡道、門扇動態、人體動作與接觸層障礙不在第一版模型內。預訓練資料重疊未知。", "",
"## 執行記錄", "", "```json",json.dumps(a.get("learning_execution",{}),ensure_ascii=False,indent=2),"```", "",
"RTX 4090 預檢為 22135/24564 MiB、99% 使用中，因此本次採 CPU float32、2 執行緒；沒有停止其他程序或修改 Ubuntu-bench。",
"峰值顯存為 null（CPU 不適用），不是 0 MB 的 GPU 測量。模型權重載入/首次驗證開銷包含在當次 wall time，個別影格時間含前處理與 forward。",
f"Viewer JSON：{(ROOT/'artifacts/study.json').stat().st_size/1e6:.2f} MB；初始 WebGL 畫面與互動由瀏覽器實際檢視。", "",
"授權：ReplicaCAD 官方網頁 CC BY 4.0 與此 revision 的 LICENSE.txt CC BY-NC 4.0 不一致，採較嚴格的本機非商業研究條件。詳見 docs/sources.md。",
"Colab 啟動檔共用相同核心，但本次沒有執行 Colab，也未量測任何 Colab GPU 效能。"]
(ROOT/"docs/results.md").write_text("\n".join(rows)+"\n",encoding="utf8")
print("Wrote docs/results.md from actual study results")
