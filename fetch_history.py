# -*- coding: utf-8 -*-
import requests
import pandas as pd
import os
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_marksix_data():
    print("🌐 正在從網上歷史資料庫抓取六合彩數據 (2025-2026)...")
    
    urls = [
        "https://www.nfd.com.tw/house/year/2025.htm",
        "https://www.nfd.com.tw/house/year/2026.htm"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    all_data = []
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=15)
            response.encoding = 'big5' 
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            parsed_data = []
            for row in rows:
                cols = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if len(cols) >= 10:
                    parsed_data.append(cols[:10])
            
            if parsed_data:
                df = pd.DataFrame(parsed_data, columns=['YEAR', 'DATE', 'TIMES', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'S1'])
                all_data.append(df)
                
        except Exception as e:
            print(f"⚠️ 讀取 {url} 失敗，具體原因: {e}")
            
    if not all_data:
        print("❌ 無法獲取任何數據，請檢查網絡連線或重新執行。")
        return
        
    final_df = pd.concat(all_data, ignore_index=True)
    final_df['YEAR'] = pd.to_numeric(final_df['YEAR'], errors='coerce')
    final_df = final_df.dropna(subset=['YEAR'])
    
    numeric_cols = ['YEAR', 'TIMES', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'S1']
    for col in numeric_cols:
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int)
        
    final_df['DrawNo'] = final_df.apply(
        lambda row: f"{str(row['YEAR'])[-2:]}/{row['TIMES']:03d}", axis=1
    )
    
    final_df = final_df.rename(columns={'S1': 'Special'})
    result_df = final_df[['DrawNo', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Special']].tail(200)
    
    base_dir = r"E:\python\MarkSix"
    csv_path = os.path.join(base_dir, "marksix_history.csv")
    excel_path = os.path.join(base_dir, "marksix_history.xlsx")
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        
    result_df.to_csv(csv_path, index=False, encoding='utf-8')
    try:
        result_df.to_excel(excel_path, index=False)
    except Exception as e:
        print(f"Excel 導出提示: {e}")
        
    print(f"✅ 成功獲取並儲存最新的 200 期六合彩結果至 CSV 與 Excel！")

if __name__ == "__main__":
    fetch_marksix_data()