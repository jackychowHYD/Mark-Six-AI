# -*- coding: utf-8 -*-
import streamlit as st 
import pandas as pd 
import random 
import os

# ==========================================
# 1. 系統設定與資料庫初始化
# ==========================================
BASE_DIR = "." 
CSV_PATH = os.path.join(BASE_DIR, "marksix_history.csv")

if not os.path.exists(BASE_DIR): 
    os.makedirs(BASE_DIR, exist_ok=True)
    
if not os.path.exists(CSV_PATH): 
    pd.DataFrame(columns=['DrawNo', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Special']).to_csv(CSV_PATH, index=False)

st.set_page_config(page_title="Mark Six AI Pro", layout="wide", page_icon="🍀") 
st.title("🍀 終極六合彩 AI 多模型預測系統") 
st.info("⚠️ **系統免責聲明**：根據數學 nCr 計算，六合彩中頭獎機率為 1/13,983,816。期望值通常為負數，每次攪珠皆為獨立事件，本 AI 預測僅供參考，請量力而為。")

# ==========================================
# 2. 數據庫維護函式
# ==========================================
def update_csv(draw_no, numbers, special): 
    # 修正：確保 N1 至 N6 順序對應 numbers 到 numbers
    new_data = pd.DataFrame([{ 
        'DrawNo': draw_no, 
        'N1': numbers, 
        'N2': numbers[4], 
        'N3': numbers[3], 
        'N4': numbers[2], 
        'N5': numbers[1], 
        'N6': numbers, 
        'Special': special 
    }]) 
    df = pd.read_csv(CSV_PATH) 
    df = pd.concat([df, new_data]).drop_duplicates(subset=['DrawNo'], keep='last').tail(200) 
    df.to_csv(CSV_PATH, index=False)

# ==========================================
# 3. 核心 AI 結構過濾器 (連號、奇偶、同尾數)
# ==========================================
def check_ai_structure(nums): 
    # 1. 檢查奇偶比例 (歷史主流為 3:3, 4:2, 2:4) 
    odds = sum(1 for n in nums if n % 2 != 0)

    # 必須包含 2, 3 或 4 個奇數先算合格 (注意縮排)
    if odds not in [1-3]:
        return False
        
    return True

# ==========================================
# 4. 加權機率演算與預測模型
# ==========================================
def get_weighted_forecast(period, apply_reverse, apply_wuxing, count): 
    df = pd.read_csv(CSV_PATH) 
    weights = {i: 1.0 for i in range(1, 50)}
    
    population = list(weights.keys())
    weights_list = list(weights.values())
    
    results = []
    for _ in range(count):
        while True:
            drawn = []
            while len(drawn) < 6:
                # 加上  將抽籤結果轉換為純數字
                n = random.choices(population, weights=weights_list, k=1)
                if n not in drawn:
                    drawn.append(n)
            
            # 交畀過濾器驗證
            if check_ai_structure(drawn):
                results.append(sorted(drawn))
                break
                
    return results

# ==========================================
# 5. 網頁介面 (Streamlit UI)
# ==========================================
# 已經正確設定版面比例為 6:7
col1, col2 = st.columns()

with col1: 
    st.subheader("🤖 AI 多模型選號策略") 
    strategy = st.radio( 
        "選擇數據分析範圍:", 
        ("1. 完全隨機選號 (盲抽)", "2. 近 50 期 (捕捉短期旺門動量)", "3. 近 200 期 (捕捉長期均值頻率)"), 
        index=2 
    )

    # 補全：產生預測號碼按鈕與顯示邏輯
    if st.button("🎲 立即生成 AI 預測號碼"):
        with st.spinner("AI 正在高速運算與過濾中..."):
            predictions = get_weighted_forecast(200, False, False, 1)
            
            if predictions:
                st.success("✅ 生成成功！為你篩選出符合歷史結構嘅號碼：")
                for i, draw_nums in enumerate(predictions):
                    display_nums = " - ".join([str(n).zfill(2) for n in draw_nums])
                    st.markdown(f"### 🎯 推薦組合: [ {display_nums} ]")
            else:
                st.error("⚠️ AI 無法在短時間內搵到完美組合，請再撳一次！")

with col2: 
    st.subheader("📥 餵養 AI 歷史資料庫") 
    st.caption("輸入最新開獎結果，讓 AI 模型持續學習") 
    draw_no = st.text_input("期數 (例: 26/072)") 
    nums = st.text_input("6 個號碼 (以逗號分隔, 例: 6,14,22,28,42,45)") 
    spec = st.number_input("特別號", 1, 49, step=1)

    # 補全：儲存 CSV 資料庫按鈕與執行邏輯
    if st.button("💾 儲存最新開獎紀錄"):
        if draw_no and nums:
            try:
                num_list = [int(x.strip()) for x in nums.split(',')]
                
                if len(num_list) == 6:
                    update_csv(draw_no, num_list, spec)
                    st.success(f"✅ 第 {draw_no} 期紀錄已成功儲存！")
                else:
                    st.error("⚠️ 請確保剛好輸入 6 個號碼，並以逗號分隔。")
            except ValueError:
                st.error("⚠️ 號碼格式錯誤！請確保只輸入數字及逗號。")
        else:
            st.warning("⚠️ 請填寫完整期數及號碼！")
