# 本機公開準備清單

2026-09-11：依使用者授權建立私人 repository 並推送 main；原創程式MIT與概念示意圖範圍已確認；repository公開可見性尚未變更。

## 預定入口

- 帳號／repository：kuotunyu/care-space-3d（已建立，私人）。
- 初次公開候選：原始程式、必要設定與測試、版本鎖定檔、可重現命令、方法與限制文件。
- 作品介紹使用 [portfolio-summary.md](portfolio-summary.md) 的文案。
- 公開前需確認專案原創程式的授權選擇；已依使用者授權採MIT；第三方範圍見THIRD_PARTY_NOTICES.md。

## 檔案範圍

| 內容 | 目前處置 |
|---|---|
| src、viewer、scripts、tests、configs、鎖定相依 | 本機Git追蹤，可作程式碼審閱候選 |
| 方法／來源／驗收文件、彙總指標 | 已整理；公開前核對內容與來源標示 |
| data、models、third_party、artifacts | Git忽略；不納入原始碼發布 |
| Colab帳號畫面與使用者截圖 | 僅保存在artifacts/colab-evidence，不用於公開封面 |
| 家具渲染圖、點雲、網格與完整研究資料 | 不加入公開展示素材，等待來源授權範圍釐清 |
| .venv、node_modules、快取 | 不納入發布 |

.gitignore 不是保密或授權審查的替代品；目前的git追蹤檔案與歷史應在實際發布前再核對。
已推送私人 repository；沒有公開、部署或向資料提供者發送訊息。

## 展示素材的選擇

目前以文字、比較表與程式架構解說為作品主體。現有Colab截圖包含帳號介面，
且場景使用ReplicaCAD衍生素材，不直接作公開封面。之後若需要圖片，可另製
不含第三方家具的解析幾何案例截圖；必須標為解析幾何示意，不冒充DA3家具實驗。

## 發布前尚待決定

1. 私人repository已建立；改為公開需要另行確認。
2. 原創程式MIT授權已確認；第三方模型／資料仍適用各自條款。
3. 確认公開圖片及派生資料範圍；來源記錄見 sources.md。
4. 執行一次具體發布範圍檢查，再決定是否push。公開部署另行處理。

第一版開發已完成；本清單不是要求繼續追加模型、平台或發布系統。

原創概念圖已加入 docs/media/passage-states.svg，沒有使用第三方家具，
並明列非實驗截圖。公開repository仍待後續確認。

## 最後發布檢查

GitHub已辨識根目錄LICENSE為MIT。預定公開內容為目前main的原創程式、
測試、文件、鎖定相依、下載腳本與原創SVG示意。資料／權重／實驗輸出／
使用者Colab截圖未進入Git；下載腳本仍須遵守各來源條款，MIT不改變它們。
ReplicaCAD官網與固定版本授權差異保持揭露；不以概念示意冒充實验結果。
下一個外部動作僅為private改public，不建立Pages或其他公開部署。
