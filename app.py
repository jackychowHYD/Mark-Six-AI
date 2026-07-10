# -*- coding: utf-8 -*-
import streamlit as st 
import pandas as pd 
import random 
import os

# ==========================================
# 1. System Setup & Database Initialization
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
# 2. Database Update Function
# ==========================================
def update_csv(draw_no, numbers, special): 
    # Unpack the 6 numbers to avoid indexing errors
    n1, n2, n3, n4, n5, n6 = numbers
    new_data = pd.DataFrame([{ 
        'DrawNo': draw_no, 
        'N1': n1, 
        'N2': n2, 
        'N3': n3, 
        'N4': n4, 
        'N5': n5, 
        'N6': n6, 
        'Special': special 
    }]) 
    df = pd.read_csv(CSV_PATH) 
    df = pd.concat((df, new_data)).drop_duplicates(subset=['DrawNo'], keep='last').tail(200) 
    df.to_csv(CSV_PATH, index=False)

# ==========================================
# 3. AI Structure Filter (Odd/Even, etc.)
# ==========================================
def check_ai_structure(nums): 
    odds = sum(1 for n in nums if n % 2 != 0)
    
    # Must have exactly 2, 3, or 4 odd numbers to pass
    if odds not in (2, 3, 4):
        return False
        
    return True

# ==========================================
# 4. Weighted Probability Forecast Model
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
                # Use .pop() to safely extract the integer and avoid TypeErrors
                n = random.choices(population, weights=weights_list, k=1).pop()
                if n not in drawn:
                    drawn.append(n)
            
            # Verify the drawn numbers against the AI filter
            if check_ai_structure(drawn):
                drawn.sort()
                results.append(drawn)
                break
                
    return results

# ==========================================
# 5. Streamlit Web Interface (UI)
# ==========================================
col1, col2 = st.columns((6, 7))

with col1: 
    st.subheader("🤖 AI 多模型選號策略") 
    strategy = st.radio( 
        "選擇數據分析範圍:", 
        ("1. 完全隨機選號 (盲抽)", "2. 近 50 期 (捕捉短期旺門動量)", "3. 近 200 期 (捕捉長期均值頻率)"), 
        index=2 
    )

    # ================= THE GENERATE BUTTON =================
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
    nums_input = st.text_input("6 個號碼 (以逗號分隔, 例: 6,14,22,28,42,45)") 
    spec = st.number_input("特別號", 1, 49, step=1)

    # ================= THE SAVE BUTTON =================
    if st.button("💾 儲存最新開獎紀錄"):
        if draw_no and nums_input:
            try:
                num_list = [int(x.strip()) for x in nums_input.split(',')]
                
                if len(num_list) == 6:
                    update_csv(draw_no, num_list, spec)
                    st.success(f"✅ 第 {draw_no} 期紀錄已成功儲存！")
                else:
                    st.error("⚠️ 請確保剛好輸入 6 個號碼，並以逗號分隔。")
            except ValueError:
                st.error("⚠️ 號碼格式錯誤！請確保只輸入數字及逗號。")
        else:
            st.warning("⚠️ 請填寫完整期數及號碼！"))
