# 專案狀態與發布範圍

2026-09-11：第一版完成。kuotunyu/care-space-3d目前為私人repository；沒有公開部署。

## 完成狀態

本機RGB-D／DA3 CPU研究、三態通行、互動viewer、負例診斷與來源追溯已完成。
本機Python29項／前端14項測試；Colab CPU輸出、29項測試及三案例展示已有使用者證據。
原創程式、文件與概念SVG已依使用者授權採[MIT](../LICENSE)，GitHub已辨識。

GPU、觸控、讀屏、200%縮放及完整雲端異常恢復仍未完整驗證。
未知姿態、完整輪椅與更多獨立場景屬未來研究，不是第一版待修故障。

## 檔案範圍

- Git追蹤：src、viewer、scripts、tests、configs、現行文件、鎖定相依及原創示意圖。
- docs/archive：已完成施工計畫、舊版viewer報告與審查，保留歷史，不作目前待辦。
- docs/abstention-plan.md：保留原位置；實驗腳本會讀取其雜湊，不能當一般雜項移除。
- docs/ux與docs/superpowers：保留使用者回饋及實作驗收。
- data、models、third_party、artifacts與環境：Git忽略，保留研究結果、模型與可恢復快取。
- artifacts/handoff-final與handoff-smoke：舊解壓測試副本；自動核准檢查拒絕遞迴刪除，暫留。

## 公開範圍

候選公開內容是程式、文件、測試、下載腳本與原創概念SVG；不含家具資料、權重、
研究artifacts及Colab帳號截圖。示意圖不是實驗截圖。
[第三方材料](../THIRD_PARTY_NOTICES.md)不適用本專案MIT；ReplicaCAD標示差異見[sources.md](sources.md)。
改為public仍需確認，目前沒有變更可見性或建立網站部署。

[文件索引](README.md) · [作品首頁](../README.md) · [驗收紀錄](verification.md)
