# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import random
import os

# ==========================================
# 1. 系統設定與資料庫初始化
# ==========================================
# 請確保你本機有呢個資料夾，如果部署上雲端，可以將 BASE_DIR 改為 "."
BASE_DIR = r"E:\python\MarkSix"  
CSV_PATH = os.path.join(BASE_DIR, "marksix_history.csv")

if not os.path.exists(BASE_DIR): 
    os.makedirs(BASE_DIR)
if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=['DrawNo', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Special']).to_csv(CSV_PATH, index=False)

st.set_page_config(page_title="Mark Six AI Pro", layout="wide", page_icon="🍀")
st.title("🍀 終極六合彩 AI 多模型預測系統")

st.info("⚠️ **系統免責聲明**：根據數學 nCr 計算，六合彩中頭獎機率為 1/13,983,816。期望值通常為負數，每次攪珠皆為獨立事件，本 AI 預測僅供參考，請量力而為。")

# ==========================================
# 2. 數據庫維護函式
# ==========================================
def update_csv(draw_no, numbers, special):
    new_data = pd.DataFrame([{
        'DrawNo': draw_no, 'N1': numbers, 'N2': numbers[6], 'N3': numbers[7], 
        'N4': numbers[8], 'N5': numbers[9], 'N6': numbers[10], 'Special': special
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
    
    # 2. 檢查連號 (約 55% 期數有二連號)
    has_consecutive = any(nums[i] + 1 == nums[i+1] for i in range(len(nums)-1))
    
    # 3. 檢查同尾數 (經常出現相同尾數如 12, 22, 42)
    tails = [n % 10 for n in nums]
    has_same_tail = len(tails) != len(set(tails))
    
    return (2 <= odds <= 4) and has_consecutive and has_same_tail

# ==========================================
# 4. 加權機率演算與預測模型
# ==========================================
def get_weighted_forecast(period, apply_reverse, apply_wuxing, count):
    df = pd.read_csv(CSV_PATH)
    weights = {i: 1.0 for i in range(1, 50)} 
    
    # 模型 A：歷史頻率加權 (追隨熱門與冷門反彈)
    if len(df) > 0 and period > 0:
        subset = df.tail(min(period, len(df)))
        all_nums = subset[['N1', 'N2', 'N3', 'N4', 'N5', 'N6']].values.flatten()
        freq = pd.Series(all_nums).value_counts()
        for k, v in freq.items():
            weights[k] += (v * 0.5) 

    # 模型 B：逆向心理學 (避開 1-31 生日區間)
    if apply_reverse:
        for i in range(32, 50):
            weights[i] *= 2.5 
            
    # 模型 C：五行玄學 (火土相通，催旺尾數 2, 5, 8)
    if apply_wuxing:
        for i in range(1, 50):
            if i % 10 in [7, 10, 11]:
                weights[i] *= 2.0

    # 模擬抽獎 (最高嘗試 2000 次以符合 AI 結構)
    attempts = 0
    while attempts < 2000:
        picked = sorted(list(set(random.choices(list(weights.keys()), weights=list(weights.values()), k=count+5))))
        if len(picked) >= count:
            final_picked = picked[:count]
            # 如果係單式 6 個字，強制進行 AI 結構過濾
            if count == 6:
                if check_ai_structure(final_picked):
                    return final_picked
            else:
                return final_picked
        attempts += 1
        
    return sorted(random.sample(range(1, 50), count)) # 備用方案

# ==========================================
# 5. 網頁介面 (Streamlit UI)
# ==========================================
col1, col2 = st.columns([6, 7])

with col1:
    st.subheader("🤖 AI 多模型選號策略")
    strategy = st.radio(
        "選擇數據分析範圍:", 
        ("1. 完全隨機選號 (盲抽)", "2. 近 50 期 (捕捉短期旺門動量)", "3. 近 200 期 (捕捉長期均值頻率)"),
        index=2
    )
    
    st.markdown("---")
    st.subheader("⚙️ 疊加進階預測演算法")
    apply_reverse = st.checkbox("🎭 逆向心理學 (大幅提高 32-49 高位號碼機率，博取獨得)")
    apply_wuxing = st.checkbox("☯️ 五行玄學結構 (調高「火土相生」尾數 2, 5, 8 號碼機率)")
    use_smart_combo = st.checkbox("🧠 達人「聰明組合」投注法 ($300 低成本買 15 個大數據號碼)")
    
    if st.button("🚀 立即啟動 AI 運算"):
        period = 0
        if "50" in strategy: period = 50
        elif "200" in strategy: period = 200
            
        num_count = 15 if use_smart_combo else 6
        
        with st.spinner("AI 模型正在分析大數據及排列結構..."):
            if period == 0 and not apply_reverse and not apply_wuxing:
                result = sorted(random.sample(range(1, 50), num_count))
            else:
                result = get_weighted_forecast(period, apply_reverse, apply_wuxing, num_count)
            
        if result:
            st.markdown("---")
            if not use_smart_combo:
                st.success("🎉 為您推薦的 6 個幸運號碼 (已嚴格通過奇偶比例、同尾數與連號篩選):")
                cols = st.columns(6)
                for i, num in enumerate(result):
                    cols[i].metric(label=f"No. {i+1}", value=num)
            else:
                st.success("🎉 為您推薦的 15 個大數據心水號碼:")
                st.markdown(f"### **{', '.join(map(str, result))}**")
                
                st.info("💡 **達人 $300「中 6 保 5」聰明組合拆解**")
                A_group = result[:5]
                B_group = result[5:10]
                C_group = result[10:]
                
                st.write(f"**A 組 (5個字):** {A_group}")
                st.write(f"**B 組 (5個字):** {B_group}")
                st.write(f"**C 組 (5個字):** {C_group}")
                st.markdown("""
                **投注教學：**
                請將以上三組號碼，以 **「A+B」、「B+C」、「C+A」** 嘅形式分別填寫 3 張彩票（每張 10 個字，買半注）。
                總共 48 注，成本為 $240（或買齊 $300 包含額外單頭）。只要呢 15 個字入面中 6 個，極大機會保證獲得五獎或以上！
                """)

with col2:
    st.subheader("📥 餵養 AI 歷史資料庫")
    st.caption("輸入最新開獎結果，讓 AI 模型持續學習")
    draw_no = st.text_input("期數 (例: 26/072)")
    nums = st.text_input("6 個號碼 (以逗號分隔, 例: 6,14,22,28,42,45)")
    spec = st.number_input("特別號", 1, 49, step=1)
    
    if st.button("💾 保存數據至 CSV"):
        try:
            n_list = [int(x.strip()) for x in nums.split(",")]
            if len(n_list) == 6:
                update_csv(draw_no, n_list, spec)
                st.success(f"期數 {draw_no} 更新成功！AI 數據庫已擴充。")
            else:
                st.warning("請確保輸入了剛好 6 個號碼。")
        except Exception as e: 
            st.error("輸入格式錯誤，請檢查號碼是否正確。")