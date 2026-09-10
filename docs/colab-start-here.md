# CareSpace 3D：Colab 第一次操作指南

已完成驗收的人不需重跑；以下供日後建立新執行階段使用。
全程選 **CPU／無硬體加速器**。先完成安裝與測試，再分段執行研究與展示。

## 本機檔案（Windows）

專案資料夾：`D:/AI-Portfolio/CC_github部隊/care-space-3d/`

| 用途 | 完整路徑 |
|---|---|
| 上傳到 Drive 的來源 ZIP | `D:/AI-Portfolio/CC_github部隊/care-space-3d/artifacts/care-space-3d-source.zip` |
| 在 Colab 開啟的 notebook | `D:/AI-Portfolio/CC_github部隊/care-space-3d/notebooks/CareSpace3D_CPU_Reproduction_v1_1.ipynb` |

舊名 colab.ipynb 已更名，不再作為本機入口。CPU 表示使用處理器；v1 是第一版流程。

## 雲端位置（Google Drive）

使用你準備執行 Colab 的同一個 Google 帳號。
在「我的雲端硬碟」下建立 `CareSpace3D`（直接在根目錄，不是共用雲端硬碟）。
上傳 ZIP 原檔，不解壓縮，保留原名 `care-space-3d-source.zip`。

- Drive 網頁位置：`我的雲端硬碟 / CareSpace3D / care-space-3d-source.zip`
- 程式掛載後讀取：`/content/drive/MyDrive/CareSpace3D/care-space-3d-source.zip`
- 程式自動建立的工作目錄：`我的雲端硬碟 / CareSpace3D / work-v01/`
- 結果位置：`我的雲端硬碟 / CareSpace3D / work-v01 / artifacts/`

不要自行建立 work-v01 或搬動其內檔案。若來源 ZIP 已存在，更新同一檔案，
避免出現名稱帶 (1) 的副本；不需要刪除既有 work-v01 結果。

## 操作順序與停止點

1. 完成上述 Drive ZIP 上傳，確認檔名和所在資料夾。
2. 開啟 https://colab.research.google.com/ ，從本機上傳上述完整名稱的 notebook。
   不要誤選 ZIP，也不要再開舊名 colab.ipynb。
3. 確認頁面標題為 CareSpace3D_CPU_Reproduction_v1_1.ipynb。
   若要在 Drive 保存 notebook，放在 CareSpace3D 資料夾；程式不依賴 notebook 本身的位置。
4. 使用 Python 3，硬體加速器選 CPU／無。不要連線到本機執行階段。
5. 只按第一個程式碼區塊左側的執行鈕（內容以 from google.colab import drive 開始）。
   不要選「全部執行」。由本人完成 Google Drive 授權，選擇上傳 ZIP 的同一帳號。
6. 等待安裝與測試結束。成功應出現 `29 passed` 與 `INSTALL_CHECK_OK`。先停在這個檢查點，確認兩者都出現，再依下一節繼續。
   此區塊不下載模型；後續區塊才會取得家具資料與約 1.34 GB 權重。
7. 若紅色錯誤出現，停止後續區塊，提供最後一段錯誤文字。不必自行修改程式、
   更換套件或提供登入密碼／驗證碼。

v1.1 已依使用者提供的 Colab 輸出與截圖完成 CPU 重現及三案例展示驗收。
新執行階段仍須依序安裝並確認輸出；不保證未來平台環境不變。

## 安裝成功後：研究與展示

只在上方兩個成功訊息都出現後繼續，不使用「全部執行」。

1. 執行**第二個程式碼區塊**，開頭註解是 `Downloads resume; existing matching predictions are reused.`。
   它會下載資料／權重、執行基線與 DA3、生成報告。維持 CPU，不需更換執行階段。
   第一次可預留 20～60 分鐘；這是含下載與 Drive I/O 的排程估算，不是 Colab 實測效能。
   有相符快取時可重用，但不要為了追求較短時間刪除或搬動結果。
2. 等第二個區塊正常結束且沒有錯誤，再執行**第三個程式碼區塊**，開頭註解是 `Optional notebook-local viewer`。
   此步安裝前端相依、測試並開啟工作台；可預留 1～5 分鐘，取決於下載速度。
3. 使用 `RGB-D · 全部觀測`，依序查看通道開放、沙發移至通道、觀測不足；還原實驗端點與半徑後，
   預期分別為可通行、阻斷、未知。DA3 在開放通道判阻斷是保留的負結果，不是安裝失敗。

## 完成後：保存與關閉

先等執行中的區塊正常結束，再確認 Drive 中以下檔案存在且可以開啟：

| 內容 | Colab 掛載後的完整路徑 |
|---|---|
| 研究資料 | `/content/drive/MyDrive/CareSpace3D/work-v01/artifacts/study.json` |
| 可讀報告 | `/content/drive/MyDrive/CareSpace3D/work-v01/docs/results.md` |
| 模型預測快取 | `/content/drive/MyDrive/CareSpace3D/work-v01/artifacts/predictions/` |

在 Drive 網頁對應 `我的雲端硬碟 / CareSpace3D / work-v01 /` 下的同名位置。
這些檔案留在 Drive，**不會自動同步到 Windows 的本機專案路徑**。
Notebook 如有修改，先等 Colab 顯示已儲存，再使用「執行階段」中的中斷連線／刪除執行階段功能，最後關閉分頁。
只關瀏覽器分頁不代表運算已停止。這裡刪除的是臨時執行階段，不要刪除 Drive 裡的 `CareSpace3D` 資料夾。
下次連線仍須先執行第一個安裝區塊；環境在 `/content/carespace-py311-v1/`，可能隨執行階段回收。
執行階段與關閉行為依 [Colab 官方 FAQ](https://research.google.com/colaboratory/intl/en-GB/faq.html) 核對。

## v1.1：Colab Python 3.13 啟動修正

舊版直接使用 Colab 系統 Python 建立 venv，在使用者環境失敗；堆疊顯示
Python 3.13，亦超出本專案 >=3.11,<3.13 的範圍。缺少 venv 的原始輸出，
不將 ensurepip 缺失宣稱為已確認原因。
新版 uv==0.11.18 使用 managed Python 3.11.15，環境位於
`/content/carespace-py311-v1/`，不使用先前失敗的 `/content/carespace-venv/`。
每個安裝階段列出合併輸出，失敗時停止。成功多顯示 INSTALL_CHECK_OK。
CPU／None；首次安裝估計10～20分鐘，非Colab實測保證。
更新時只需上傳新版 v1_1 notebook，先前 Drive 來源 ZIP 可供此次安裝使用；
核心依賴未變。無需刪除 Drive 的 work-v01 或先前結果。
uv Python 管理來源：https://docs.astral.sh/uv/concepts/python-versions/
