# CareSpace 3D：Colab 第一次操作指南

這次只驗證 CPU 安裝與測試，不使用 GPU、不先執行模型。

## 本機檔案（Windows）

專案資料夾：`D:/AI-Portfolio/CC_github部隊/care-space-3d/`

| 用途 | 完整路徑 |
|---|---|
| 上傳到 Drive 的來源 ZIP | `D:/AI-Portfolio/CC_github部隊/care-space-3d/artifacts/care-space-3d-source.zip` |
| 在 Colab 開啟的 notebook | `D:/AI-Portfolio/CC_github部隊/care-space-3d/notebooks/CareSpace3D_CPU_Reproduction_v1.ipynb` |

舊名 colab.ipynb 已更名，不再作為本機入口。CPU 表示使用處理器；v1 是第一版流程。

## 雲端位置（Google Drive）

使用你準備執行 Colab 的同一個 Google 帳號。
在「我的雲端硬碟」下建立 `CareSpace3D`（直接在根目錄，不是共用雲端硬碟）。
上傳 ZIP 原檔，不解壓縮，保留原名 `care-space-3d-source.zip`。

- Drive 網頁位置：`我的雲端硬碟 / CareSpace3D / care-space-3d-source.zip`
- 程式掛載後讀取：`/content/drive/MyDrive/CareSpace3D/care-space-3d-source.zip`
- 程式自動建立的工作目錄：`我的雲端硬碟 / CareSpace3D / work-v01/`
- 未來結果位置：`我的雲端硬碟 / CareSpace3D / work-v01 / artifacts/`

不要自行建立 work-v01 或搬動其內檔案。若來源 ZIP 已存在，更新同一檔案，
避免出現名稱帶 (1) 的副本；不需要刪除既有 work-v01 結果。

## 操作順序與停止點

1. 完成上述 Drive ZIP 上傳，確認檔名和所在資料夾。
2. 開啟 https://colab.research.google.com/ ，從本機上傳上述完整名稱的 notebook。
   不要誤選 ZIP，也不要再開舊名 colab.ipynb。
3. 確認頁面標題為 CareSpace3D_CPU_Reproduction_v1.ipynb。
   若要在 Drive 保存 notebook，放在 CareSpace3D 資料夾；程式不依賴 notebook 本身的位置。
4. 使用 Python 3，硬體加速器選 CPU／無。不要連線到本機執行階段。
5. 只按第一個程式碼區塊左側的執行鈕（內容以 from google.colab import drive 開始）。
   不要選「全部執行」。由本人完成 Google Drive 授權，選擇上傳 ZIP 的同一帳號。
6. 等待安裝與測試結束。成功應出現 `29 passed`。此時停止，回報結果。
   此區塊不下載模型；後續區塊才會取得家具資料與約 1.34 GB 權重。
7. 若紅色錯誤出現，停止後续區塊，提供最後一段錯誤文字。不必自行修改程式、
   更換套件或提供登入密碼／驗證碼。

Colab 尚未實跑；本機測試通過不代表雲端相依安装一定成功。
