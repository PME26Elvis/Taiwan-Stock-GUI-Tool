import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# =========================================================================
# 核心邏輯層 (Core Logic) - 繼承自階段一並優化
# =========================================================================

class StockFetcher:
    def process_date(self, date_str):
        """將 2022/01/01 統一轉為 2022-01-01"""
        if not date_str:
            return None
        return date_str.replace('/', '-')

    def fetch_data(self, user_input_id, start_date_str, end_date_str=None):
        """抓取數據的主要邏輯"""
        
        # 1. 處理代碼預設值
        if not user_input_id:
            user_input_id = "00631L"
        stock_id = user_input_id.strip().upper()

        # 智慧切換上市櫃
        if '.TW' in stock_id or '.TWO' in stock_id:
            tickers_to_try = [stock_id]
        else:
            tickers_to_try = [f"{stock_id}.TW", f"{stock_id}.TWO"]

        # 2. 處理日期格式
        start_date = self.process_date(start_date_str)
        end_date = self.process_date(end_date_str)

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # 3. 執行下載 (包含假日回溯邏輯)
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        buffer_start_date = (start_dt - timedelta(days=7)).strftime('%Y-%m-%d')

        df = pd.DataFrame()
        found_ticker = ""

        for ticker in tickers_to_try:
            try:
                temp_df = yf.download(ticker, start=buffer_start_date, end=end_date, progress=False, auto_adjust=False)
                if not temp_df.empty:
                    df = temp_df
                    found_ticker = ticker
                    break
            except Exception:
                continue

        if df.empty:
            return None, f"找不到 {stock_id} 的資料，請檢查代碼。"

        # 4. 數據清洗
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date'])

        # 篩選日期
        user_start_dt = pd.to_datetime(start_date)
        valid_history = df[df['Date'] <= user_start_dt]

        msg_detail = ""
        if valid_history.empty:
            final_df = df.copy()
            msg_detail = "(注意: 指定日期無資料，已抓取最近數據)"
        else:
            target_start_date = valid_history['Date'].iloc[-1]
            final_df = df[df['Date'] >= target_start_date].copy()
            if target_start_date < user_start_dt:
                msg_detail = f"(已自動回溯至前一交易日: {target_start_date.date()})"

        # 格式化
        output_df = final_df[['Date', 'Close', 'Volume']].copy()
        output_df['Close'] = output_df['Close'].round(2)
        output_df['Date'] = output_df['Date'].dt.date
        output_df.columns = ['日期', '收盤價', '交易次數(成交量)']

        # 5. 存檔
        clean_id = found_ticker.replace('.TW', '').replace('.TWO', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_id}_{start_date.replace('-','')}_{timestamp}.csv"
        
        # 儲存在程式執行目錄下
        output_df.to_csv(filename, index=False, encoding='utf-8-sig')
        full_path = os.path.abspath(filename)
        
        return full_path, f"成功！{msg_detail}"

# =========================================================================
# UI 介面層 (Presentation Layer)
# =========================================================================

class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("台股資料抓取助手 v2.0")
        self.root.geometry("400x380")
        self.root.resizable(False, False)
        
        self.logic = StockFetcher()
        self.config_file = "user_config.json"

        # 初始化變數
        self.var_stock = tk.StringVar()
        self.var_start = tk.StringVar()
        self.var_end = tk.StringVar()
        self.status_msg = tk.StringVar(value="準備就緒")

        # 載入上次設定
        self.load_config()

        self.create_widgets()

    def create_widgets(self):
        # 設定通用 padding
        p_x = 20
        p_y = 5

        # 1. 股票代碼區
        lbl_stock = tk.Label(self.root, text="股票代碼 (預設 00631L):", font=("微軟正黑體", 10))
        lbl_stock.pack(anchor="w", padx=p_x, pady=(15, 0))
        
        entry_stock = tk.Entry(self.root, textvariable=self.var_stock, font=("Arial", 11))
        entry_stock.pack(fill="x", padx=p_x, pady=p_y)

        # 2. 開始日期區
        lbl_start = tk.Label(self.root, text="開始日期 (格式 YYYY/MM/DD):", font=("微軟正黑體", 10))
        lbl_start.pack(anchor="w", padx=p_x, pady=(10, 0))
        
        entry_start = tk.Entry(self.root, textvariable=self.var_start, font=("Arial", 11))
        entry_start.pack(fill="x", padx=p_x, pady=p_y)
        
        # 快捷提示
        lbl_hint = tk.Label(self.root, text="提示: 支援 2026/02/01 或 2026-02-01", font=("微軟正黑體", 8), fg="gray")
        lbl_hint.pack(anchor="w", padx=p_x)

        # 3. 結束日期區
        lbl_end = tk.Label(self.root, text="結束日期 (預設今日):", font=("微軟正黑體", 10))
        lbl_end.pack(anchor="w", padx=p_x, pady=(10, 0))
        
        entry_end = tk.Entry(self.root, textvariable=self.var_end, font=("Arial", 11))
        entry_end.pack(fill="x", padx=p_x, pady=p_y)

        # 4. 按鈕區
        self.btn_run = tk.Button(self.root, text="開始抓取並存檔", command=self.on_submit, 
                                 bg="#E0E0E0", font=("微軟正黑體", 11, "bold"), height=2)
        self.btn_run.pack(fill="x", padx=p_x, pady=(20, 10))

        # 5. 狀態列
        lbl_status = tk.Label(self.root, textvariable=self.status_msg, 
                              fg="blue", font=("微軟正黑體", 9), wraplength=360)
        lbl_status.pack(pady=5)

    def on_submit(self):
        """按鈕點擊事件"""
        stock = self.var_stock.get()
        start = self.var_start.get()
        end = self.var_end.get()

        if not start:
            messagebox.showwarning("提示", "請至少輸入「開始日期」！")
            return

        # 鎖定按鈕避免重複點擊
        self.btn_run.config(state="disabled", text="處理中...")
        self.status_msg.set("正在連線抓取資料，請稍候...")

        # 開啟新執行緒 (Thread) 執行耗時任務，避免視窗卡死
        threading.Thread(target=self.run_logic_thread, args=(stock, start, end)).start()

    def run_logic_thread(self, stock, start, end):
        """背景執行邏輯"""
        try:
            path, msg = self.logic.fetch_data(stock, start, end)
            
            if path:
                # 成功
                self.save_config(stock, start) # 記憶本次輸入
                self.update_ui_success(path, msg)
            else:
                # 邏輯層回傳失敗
                self.update_ui_fail(msg)
                
        except Exception as e:
            self.update_ui_fail(f"系統錯誤: {str(e)}")

    def update_ui_success(self, path, msg):
        """跨執行緒更新 UI (成功)"""
        self.root.after(0, lambda: self._ui_success(path, msg))

    def _ui_success(self, path, msg):
        self.btn_run.config(state="normal", text="開始抓取並存檔")
        self.status_msg.set(f"完成！檔案已存至:\n{path}")
        messagebox.showinfo("成功", f"{msg}\n\n檔案已儲存:\n{path}")

    def update_ui_fail(self, msg):
        """跨執行緒更新 UI (失敗)"""
        self.root.after(0, lambda: self._ui_fail(msg))

    def _ui_fail(self, msg):
        self.btn_run.config(state="normal", text="開始抓取並存檔")
        self.status_msg.set("發生錯誤")
        messagebox.showerror("錯誤", msg)

    def load_config(self):
        """讀取上次的設定"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.var_stock.set(data.get("stock", ""))
                    # 這裡可以決定是否要自動填入上次日期，或者留白
                    # 為了方便 Update，我們填入上次的日期
                    self.var_start.set(data.get("start_date", ""))
            except:
                pass

    def save_config(self, stock, start):
        """儲存本次設定"""
        data = {
            "stock": stock if stock else "00631L", # 存入實際使用的值
            "start_date": start
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f)
        except:
            pass

# =========================================================================
# 主程式入口
# =========================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()
