# 📈 Taiwan Stock GUI Tool (台股歷史資料抓取助手)

![Build Status](https://github.com/PME26Elvis/Taiwan-Stock-Grabber/actions/workflows/build.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)

一個輕量級、免安裝 Python 環境的 Windows 桌面工具。
專為需要將台股歷史資料導入 Excel 分析的使用者設計。

A lightweight Windows GUI tool for fetching Taiwan Stock (TWSE/TPEX) historical data into CSV format.

## ✨ Features (功能特色)

* **GUI 介面**：直觀的圖形介面，無需使用指令列 (Command Line)。
* **智慧搜尋**：
    * 支援 **上市 (TWSE)**、**上櫃 (TPEX)** 與 **ETF**。
    * 自動判斷股票類別 (例：輸入 `2603` 自動抓取上市，`8299` 自動抓取上櫃)。
    * 輸入 `00631` 自動修正為 `00631L`。
* **日期強健性**：
    * 支援多種日期格式 (2026/02/01 或 2026-02-01)。
    * **假日回溯**：若指定日期為假日，自動往前抓取最近一個交易日的資料。
* **Excel 友善**：
    * 輸出 `UTF-8-SIG` 編碼的 CSV，Excel 開啟不亂碼。
    * 收盤價自動四捨五入至小數點後兩位。
* **記憶功能**：自動記錄上次查詢的代碼與日期，方便每日更新。

## 🚀 Download (下載執行檔)

1.  點擊上方的 [**Actions**](https://github.com/PME26Elvis/Taiwan-Stock-Grabber/actions) 頁籤。
2.  選擇最新的 **Build Windows Exe** 流程。
3.  滑動至底部的 **Artifacts** 區域。
4.  點擊 **TaiwanStockGrabber-Windows-Exe** 下載壓縮檔。
5.  解壓縮後即可直接執行 `.exe` 檔案。

## 🛠️ Tech Stack (技術棧)

* **Language**: Python 3.10
* **GUI**: Tkinter (Native Python UI)
* **Data Source**: `yfinance` API
* **Build Tool**: PyInstaller (Compiled via GitHub Actions)

## 📝 License

This project is open source and available under the [MIT License](LICENSE).
