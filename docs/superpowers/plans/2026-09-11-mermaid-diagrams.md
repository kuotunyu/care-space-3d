# Mermaid 技術圖解

使用者已批准三張圖：README 架構、技術文件三態流程、Viewer 互動時序。
圖解現有實作，不新增模型、部署或執行時依賴；沿用正體中文與精簡首頁。

- [x] 對照 pipeline／run_learning／fusion／planning 與 Viewer 程式，確認資訊與執行邊界。
- [x] 在 artifacts/diagrams 暫存來源並以固定 CLI 渲染，檢查字體、分支、箭頭與版面。
- [x] 把已驗證 Mermaid 區塊放入 README、docs/design.md、docs/viewer-contract.md；Markdown 為唯一公開圖源。
- [x] 核對連結、重現包與 GitHub 實際顯示；記錄驗收後同步。

架構圖保留合成觀測與 oracle 分流：完整幾何不能進入 DA3 推論。
三態圖從已融合高度的平面格出發，先膨脹再做兩次四鄰接連通搜尋。
時序圖以靜態產物載入與瀏覽器本地查詢為主，避免暗示每次互動都呼叫 Python／模型。
README 用圖取代部分既有條列；不增加首頁文字連結。
