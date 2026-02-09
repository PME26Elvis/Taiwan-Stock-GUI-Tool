import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# =========================================================================
# 核心邏輯層 (Core Logic)
# =========================================================================

class StockFetcher:
    def process_date(self, date_str):
        """將 2022/01/01 統一轉為 2022-01-01"""
        if not date_str:
            return None
        return date_str.replace('/', '-')

    def fetch_data(self, user_input_id, start_date_str, end_date_str=None, use_adj_close=False):
        """
        抓取數據的主要邏輯
        :param use_adj_close: Boolean, 是否使用還原權息價格
        """
        
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

        # 3. 執行下載
        # 為了抓到上次收盤，往前推 7 天
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        buffer_start_date = (start_dt - timedelta(days=7)).strftime('%Y-%m-%d')

        df = pd.DataFrame()
        found_ticker = ""

        for ticker in tickers_to_try:
            try:
                # auto_adjust=False 代表我們要同時拿到 'Close' 和 'Adj Close'
                # 這樣我們可以自由選擇要輸出哪一個
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

        # 5. 欄位選擇 (關鍵修改)
        # 根據使用者是否勾選「還原權息」來決定取用哪個欄位
        if use_adj_close:
            # 優先使用 Adj Close，若無則退回 Close
            target_col = 'Adj Close' if 'Adj Close' in final_df.columns else 'Close'
            col_name_tw = '收盤價(還原權息)'
        else:
            target_col = 'Close'
            col_name_tw = '收盤價'

        output_df = final_df[['Date', target_col, 'Volume']].copy()
        
        # 格式化
        output_df[target_col] = output_df[target_col].round(2)
        output_df['Date'] = output_df['Date'].dt.date
        output_df.columns = ['日期', col_name_tw, '交易次數(成交量)']

        # 6. 存檔
        # 檔名加入標記，讓使用者知道這份檔案是否含權息
        suffix = "_Adj" if use_adj_close else ""
        clean_id = found_ticker.replace('.TW', '').replace('.TWO', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_id}_{start_date.replace('-','')}{suffix}_{timestamp}.csv"
        
        output_df.to_csv(filename, index=False, encoding='utf-8-sig')
        full_path = os.path.abspath(filename)
        
        return full_path, f"成功！{msg_detail}"

# =========================================================================
# UI 介面層 (Presentation Layer)
# =========================================================================

class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("台股資料抓取助手")
        self.root.geometry("400x420") # 高度稍微增加以容納 Checkbox
        self.root.resizable(False, False)
        
        self.logic = StockFetcher()
        self.config_file = "user_config.json"

        # 初始化變數
        self.var_stock = tk.StringVar()
        self.var_start = tk.StringVar()
        self.var_end = tk.StringVar()
        self.var_use_adj = tk.BooleanVar(value=False) # 預設不勾選
        self.status_msg = tk.StringVar(value="準備就緒")

        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        p_x = 20
        p_y = 5

        # 1. 股票代碼
        lbl_stock = tk.Label(self.root, text="股票代碼 (預設 00631L):", font=("微軟正黑體", 10))
        lbl_stock.pack(anchor="w", padx=p_x, pady=(15, 0))
        tk.Entry(self.root, textvariable=self.var_stock, font=("Arial", 11)).pack(fill="x", padx=p_x, pady=p_y)

        # 2. 開始日期
        lbl_start = tk.Label(self.root, text="開始日期 (格式 YYYY/MM/DD):", font=("微軟正黑體", 10))
        lbl_start.pack(anchor="w", padx=p_x, pady=(10, 0))
        tk.Entry(self.root, textvariable=self.var_start, font=("Arial", 11)).pack(fill="x", padx=p_x, pady=p_y)
        tk.Label(self.root, text="提示: 支援 2026/02/01 或 2026-02-01", font=("微軟正黑體", 8), fg="gray").pack(anchor="w", padx=p_x)

        # 3. 結束日期
        lbl_end = tk.Label(self.root, text="結束日期 (預設今日):", font=("微軟正黑體", 10))
        lbl_end.pack(anchor="w", padx=p_x, pady=(10, 0))
        tk.Entry(self.root, textvariable=self.var_end, font=("Arial", 11)).pack(fill="x", padx=p_x, pady=p_y)

        # 4. 功能選項 (Checkbox)
        chk_adj = tk.Checkbutton(self.root, text="下載還原權息價格 (Adj Close)", 
                                 variable=self.var_use_adj, font=("微軟正黑體", 10))
        chk_adj.pack(anchor="w", padx=p_x, pady=(10, 0))

        # 5. 按鈕
        self.btn_run = tk.Button(self.root, text="開始抓取並存檔", command=self.on_submit, 
                                 bg="#E0E0E0", font=("微軟正黑體", 11, "bold"), height=2)
        self.btn_run.pack(fill="x", padx=p_x, pady=(20, 10))

        # 6. 狀態列
        tk.Label(self.root, textvariable=self.status_msg, fg="blue", font=("微軟正黑體", 9), wraplength=360).pack(pady=5)

    def on_submit(self):
        stock = self.var_stock.get()
        start = self.var_start.get()
        end = self.var_end.get()
        use_adj = self.var_use_adj.get() # 取得勾選狀態

        if not start:
            messagebox.showwarning("提示", "請至少輸入「開始日期」！")
            return

        self.btn_run.config(state="disabled", text="處理中...")
        self.status_msg.set("正在連線抓取資料，請稍候...")
        
        # 傳入 use_adj 參數
        threading.Thread(target=self.run_logic_thread, args=(stock, start, end, use_adj)).start()

    def run_logic_thread(self, stock, start, end, use_adj):
        try:
            path, msg = self.logic.fetch_data(stock, start, end, use_adj)
            if path:
                self.save_config(stock, start, use_adj)
                self.update_ui_success(path, msg)
            else:
                self.update_ui_fail(msg)
        except Exception as e:
            self.update_ui_fail(f"系統錯誤: {str(e)}")

    def update_ui_success(self, path, msg):
        self.root.after(0, lambda: self._ui_success(path, msg))

    def _ui_success(self, path, msg):
        self.btn_run.config(state="normal", text="開始抓取並存檔")
        self.status_msg.set(f"完成！檔案已存至:\n{path}")
        messagebox.showinfo("成功", f"{msg}\n\n檔案已儲存:\n{path}")

    def update_ui_fail(self, msg):
        self.root.after(0, lambda: self._ui_fail(msg))

    def _ui_fail(self, msg):
        self.btn_run.config(state="normal", text="開始抓取並存檔")
        self.status_msg.set("發生錯誤")
        messagebox.showerror("錯誤", msg)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.var_stock.set(data.get("stock", ""))
                    self.var_start.set(data.get("start_date", ""))
                    # 讀取上次是否勾選
                    self.var_use_adj.set(data.get("use_adj", False))
            except:
                pass

    def save_config(self, stock, start, use_adj):
        data = {
            "stock": stock if stock else "00631L",
            "start_date": start,
            "use_adj": use_adj
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()
