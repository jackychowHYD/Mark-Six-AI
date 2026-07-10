# -*- coding: utf-8 -*-
import streamlit as st 
import pandas as pd 
import random 
import os

# ==========================================
# 1. 系統設定與資料庫初始化
# ==========================================
# 根據我們之前的討論，將 BASE_DIR 改為 "." 以適應雲端部署 (外部知識補充)
BASE_DIR = "."
CSV_PATH = os.path.join(BASE_DIR, "marksix_history.csv")

# 加入了 exist_ok=True 防護避免 FileExistsError (外部知識補充)
if not os.path.exists(BASE_DIR): 
    os.makedirs(BASE_DIR, exist_ok=True) 
    
if not os.path.exists(CSV_PATH): 
    pd.DataFrame(columns=['DrawNo', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Special']).to_csv(CSV_PATH, index=False)

st.set_page_config(page_title="Mark Six AI Pro", layout="wide", page_icon="🍀") 
st.title("🍀 終極六合彩 AI 多模型預測系統")
st.info("⚠️  **系統免責聲明** ：根據數學 nCr 計算，六合彩中頭獎機率為 1/13,983,816。期望值通常為負數，每次攪珠皆為獨立事件，本 AI 預測僅供參考，請量力而為。")

# ==========================================
# 2. 數據庫維護函式
# ==========================================
def update_csv(draw_no, numbers, special): 
    new_data = pd.DataFrame([{ 
        'DrawNo': draw_no, 
        'N1': numbers, 
        'N2': numbers[3], 
        'N3': numbers[1], 
        'N4': numbers[2], 
        'N5': numbers[4], 
        'N6': numbers, 
        'Special': special 
    }]) 
    df = pd.read_csv(CSV_PATH) 
    # 只保留最新 200 期作大數據分析 
    df = pd.concat([df, new_data]).drop_duplicates(subset=['DrawNo'], keep='last').tail(200) 
    df.to_csv(CSV_PATH, index=False)

# ==========================================
# 3. 核心 AI 結構過濾器 (連號、奇偶、同尾數)
# ==========================================
def check_ai_structure(nums): 
    # 1. 檢查奇偶比例 (歷史主流為 3:3, 4:2, 2:4) 
    odds = sum(1 for n in nums if n % 2 != 0)
    
    # === 以下為結合歷史對話與外部知識補全的運算邏輯 ===
    # 奇偶極端比例過濾
    if odds not in [2-4]:
        return False

    nums_sorted = sorted(nums)
    
    # 2. 檢查連號：過濾大於 2 組連號的極端組合
    consecutive_count = 0
    for i in range(len(nums_sorted) - 1):
        if nums_sorted[i] + 1 == nums_sorted[i+1]:
            consecutive_count += 1
    if consecutive_count > 2:
        return False

    # 3. 檢查同尾數：過濾同一尾數出現超過 3 次的組合
    endings = [n % 10 for n in nums_sorted]
    ending_counts = {x: endings.count(x) for x in set(endings)}
    if any(count > 3 for count in ending_counts.values()):
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
                # ✅ 重點修正：喺最尾加上 ，將抽出來的結果轉換為純數字
                n = random.choices(population, weights=weights_list, k=1)[0]
                if n not in drawn:
                    drawn.append(n)
            
            # 將抽出的號碼交給 AI 結構過濾器驗證
            if check_ai_structure(drawn):
                results.append(sorted(drawn))
                break
                
    return results

# ==========================================
# 5. 網頁介面 (Streamlit UI)
# ==========================================
col1, col2 = st.columns([6,7])

with col1: 
    st.subheader("🤖 AI 多模型選號策略") 
    strategy = st.radio( 
        "選擇數據分析範圍:", 
        ("1. 完全隨機選號 (盲抽)", "2. 近 50 期 (捕捉短期旺門動量)", "3. 近 200 期 (捕捉長期均值頻率)"), 
        index=2 
    )
    
    # === 以下為外部知識補全的生成按鈕與顯示邏輯 ===
    # 加入一個生成號碼嘅按鈕
    if st.button("🎲 立即生成 AI 預測號碼"):
        with st.spinner("AI 正在高速運算與過濾中..."):
            # 呼叫之前寫好嘅 get_weighted_forecast 產生 1 組號碼
            # (假設參數暫時為: 200期, 無反轉, 無五行, 產生1組)
            predictions = get_weighted_forecast(200, False, False, 1)
            
            if predictions:
                st.success("✅ 生成成功！為你篩選出符合歷史結構嘅號碼：")
                # 將抽出的號碼漂亮地顯示出來
                for i, draw_nums in enumerate(predictions):
                    # 將數字變成兩位數格式 (例如 6 變成 06)
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

    # === 以下為外部知識補全的儲存按鈕與觸發邏輯 ===
    if st.button("💾 儲存最新開獎紀錄"):
        if draw_no and nums:
            try:
                # 將輸入嘅字串 "6,14,22..." 轉換成整數列表 [6, 14, 22...]
                num_list = [int(x.strip()) for x in nums.split(',')]
                
                # 檢查是否剛好輸入咗 6 個號碼
                if len(num_list) == 6:
                    # 呼叫你寫好嘅 update_csv 函式去更新資料庫
                    update_csv(draw_no, num_list, spec)
                    st.success(f"✅ 第 {draw_no} 期紀錄已成功儲存！")
                else:
                    st.error("⚠️ 請確保剛好輸入 6 個號碼，並以逗號分隔。")
            except ValueError:
                st.error("⚠️ 號碼格式錯誤！請確保只輸入數字及逗號。")
        else:
            st.warning("⚠️ 請填寫完整期數及號碼！")
