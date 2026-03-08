# stock_scraper_with_indicators.py
import yfinance as yf
import pandas as pd
import numpy as np
import os


def fetch_and_add_indicators(ticker, period="2y"):
    print(f"開始抓取 {ticker} 股價資料...")
    # 1. 抓取股價資料
    df = yf.download(ticker, period=period)
    
    if df.empty and ticker.endswith('.TW'):
        print(f"⚠️ {ticker} 查無資料，這可能是上櫃股票，自動嘗試切換為 .TWO ...")
        # 把 .TW 換成 .TWO
        ticker = ticker.replace('.TW', '.TWO')
        # 再抓一次！
        df = yf.download(ticker, period="1y")
    
    if df.empty:
        print(f"❌ 找不到 {ticker} 的資料，請確認股票代號是否正確。")
        return None
    
    # 統一欄位名稱 (移除 MultiIndex 若存在)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # 2. 加入常見技術指標 (特徵工程)
    print("計算技術指標中 (MA, RSI, MACD, Bollinger Bands)...")
    
    # 簡單移動平均線 (MA)
    df['MA_5'] = df['Close'].rolling(window=5).mean()
    df['MA_10'] = df['Close'].rolling(window=10).mean()
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    
    # 相對強弱指標 (RSI - 14天)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 布林通道 (Bollinger Bands - 20天, 2個標準差)
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    std_dev = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (std_dev * 2)
    df['BB_Lower'] = df['BB_Middle'] - (std_dev * 2)
    
    # 移除因計算指標產生的初始空值
    df.dropna(inplace=True)
    
    # 3. 輸出檔案
    # 移除代號中的 .TW 或 .TWO (如果是上櫃股票)，讓檔名更乾淨
    clean_ticker = ticker.replace('.TW', '').replace('.TWO', '')
    filename = f"{clean_ticker}.csv"    
    save_dir = r"D:\桌布\github\Stock csv files"
    
    # 檢查該資料夾是否存在，如果不存在就自動幫你建立一個
    os.makedirs(save_dir, exist_ok=True)
    full_path = os.path.join(save_dir, filename)    # 將資料夾路徑與檔名結合在一起，變成完整的絕對路徑
    
    # 將資料存到指定的完整路徑中
    df.to_csv(full_path)
    print(f"處理完成！檔案已儲存為: {full_path}")
    
    return df

if __name__ == "__main__":
    stock_mapping = {
        "台積電": "2330.TW",
        "鴻海": "2317.TW",
        "聯發科": "2454.TW",
        "長榮": "2603.TW",
        "蘋果": "AAPL",
        "特斯拉": "TSLA",
        "輝達": "NVDA"
    }

    # 使用 input() 讓程式暫停，等待使用者輸入
    user_input = input("請輸入你想查詢的股票名稱 (例如: 台積電) 或代號 (例如: 2330, AAPL): ").strip()

    # 判斷與轉換使用者的輸入
    if user_input in stock_mapping:
        # 情況 A：如果輸入的是字典裡有的中文名稱，自動轉換
        target_ticker = stock_mapping[user_input]
        print(f"👉 系統已將「{user_input}」轉換為標準代號: {target_ticker}")
        
    elif user_input.isdigit() and len(user_input) == 4:
        # 情況 B：如果只輸入了 4 個數字 (台灣上市股票常見格式)，貼心自動補上 .TW
        target_ticker = f"{user_input}.TW"
        print(f"👉 偵測到台灣股票代碼，系統自動補上後綴: {target_ticker}")
        
    else:
        # 情況 C：其他情況 (例如使用者已經很標準地輸入了 AAPL 或 2330.TW)
        target_ticker = user_input.upper() 

    # 正式啟動你的抓取函式
    print("-" * 40)
    result_df = fetch_and_add_indicators(target_ticker)
    
    # 顯示結果
    if result_df is not None:
        print("\n✅ 資料預覽 (前五筆)：")
        print(result_df.head())