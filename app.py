# -*- coding: utf-8 -*-
import streamlit as st 
import pandas as pd 
import numpy as np 
import os
import random
import io

# Try importing PyGithub for automated repository synchronization
try:
    import github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# ==========================================
# 1. 系統設定與資料庫初始化 (同時支援 Excel 與 CSV)
# ==========================================
BASE_DIR = "." 
CSV_PATH = os.path.join(BASE_DIR, "marksix_history.csv")
EXCEL_PATH = os.path.join(BASE_DIR, "marksix_history.xlsx")

if not os.path.exists(BASE_DIR): 
    os.makedirs(BASE_DIR, exist_ok=True)

def sort_df_by_drawno(df):
    """針對期數 (DrawNo) 進行純數字解析與精確排序 (例如: 26/001 < 26/010 < 26/102)"""
    if df.empty or 'DrawNo' not in df.columns:
        return df
    
    def parse_key(val):
        s = str(val).strip()
        if '/' in s:
            parts = s.split('/')
            try:
                return (int(parts[0]), int(parts[1]))
            except ValueError:
                pass
        return (0, 0)

    df['_sort_key'] = df['DrawNo'].apply(parse_key)
    df = df.sort_values(by='_sort_key', ascending=True).reset_index(drop=True)
    df = df.drop(columns=['_sort_key'])
    return df
    
def load_history_df():
    """讀取並合併 Excel 與 CSV 資料庫，依期數數字升序排序"""
    dfs = []
    if os.path.exists(EXCEL_PATH):
        try:
            dfs.append(pd.read_excel(EXCEL_PATH))
        except Exception:
            pass
    if os.path.exists(CSV_PATH):
        try:
            dfs.append(pd.read_csv(CSV_PATH))
        except Exception:
            pass
            
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        combined['DrawNo'] = combined['DrawNo'].astype(str).str.strip()
        combined = combined.drop_duplicates(subset=['DrawNo'], keep='last')
        return sort_df_by_drawno(combined)
        
    return pd.DataFrame(columns=['DrawNo', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Special'])

def sync_to_github():
    """若設定了 GitHub Token，自動將最新 Excel 檔案同步回 GitHub 儲存庫"""
    if GITHUB_AVAILABLE and "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
        try:
            g = github.Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            
            with open(EXCEL_PATH, "rb") as f:
                content_bytes = f.read()
                
            contents = repo.get_contents("marksix_history.xlsx")
            repo.update_file(
                path="marksix_history.xlsx",
                message="🤖 Streamlit App Auto-Update Mark Six History",
                content=content_bytes,
                sha=contents.sha
            )
            st.toast("☁️ 已成功自動同步歷史紀錄至 GitHub 儲存庫！", icon="✅")
        except Exception as e:
            st.warning(f"⚠️ GitHub 自動同步失敗: {e}")

def save_history_df(df):
    """同步儲存至 Excel (.xlsx) 與 CSV (.csv)，確保排序正確並同步雲端"""
    df['DrawNo'] = df['DrawNo'].astype(str).str.strip()
    df = df.drop_duplicates(subset=['DrawNo'], keep='last')
    df = sort_df_by_drawno(df)
    
    df.to_csv(CSV_PATH, index=False)
    try:
        df.to_excel(EXCEL_PATH, index=False)
    except Exception as e:
        st.warning(f"⚠️ Excel 檔案寫入提示: {e}")
        
    sync_to_github()

# 初始化資料庫
df_init = load_history_df()
save_history_df(df_init)

st.set_page_config(page_title="Mark Six AI Pro - 生肖五行 Excel 版", layout="wide", page_icon="🍀") 
st.title("🍀 終極六合彩 AI 多模型預測系統 (生肖五行 + Excel 數據管理版)") 
st.info("⚠️ **系統免責聲明**：根據數學 nCr 計算，六合彩中頭獎機率為 1/13,983,816。期望值通常為負數，每次攪珠皆為獨立事件，本 AI 預測僅供參考，請量力而為。")

# ==========================================
# 2. 生肖與五行玄學資料庫
# ==========================================
ZODIAC_ORDER = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]

SAN_HE = {
    "鼠": ["猴", "龍"], "牛": ["蛇", "雞"], "虎": ["馬", "狗"], "兔": ["羊", "豬"],
    "龍": ["猴", "鼠"], "蛇": ["雞", "牛"], "馬": ["虎", "狗"], "羊": ["兔", "豬"],
    "猴": ["鼠", "龍"], "雞": ["蛇", "牛"], "狗": ["虎", "馬"], "豬": ["兔", "羊"]
}

LIU_HE = {
    "鼠": "牛", "牛": "鼠", "虎": "豬", "兔": "狗",
    "龍": "雞", "雞": "龍", "蛇": "猴", "猴": "蛇",
    "馬": "羊", "羊": "馬"
}

LIU_CHONG = {
    "鼠": "馬", "牛": "羊", "虎": "猴", "兔": "雞",
    "龍": "狗", "蛇": "豬", "馬": "鼠", "羊": "牛",
    "猴": "虎", "雞": "兔", "狗": "龍", "豬": "蛇"
}

# 1-49 號碼循環對應十二生肖
ZODIAC_NUMBERS = {z: [] for z in ZODIAC_ORDER}
for num in range(1, 50):
    z_name = ZODIAC_ORDER[(num - 1) % 12]
    ZODIAC_NUMBERS[z_name].append(num)

WUXING_TAILS = {
    "金": [4, 9], "木": [3, 8], "水": [1, 6], "火": [2, 7], "土": [0, 5]
}

# ==========================================
# 3. 生肖與數據模型混合預測邏輯
# ==========================================
def get_zodiac_prediction(main_zodiac, wuxing_pref, period):
    san_he_list = SAN_HE.get(main_zodiac, [])
    liu_he_zodiac = LIU_HE.get(main_zodiac, "")
    chong_zodiac = LIU_CHONG.get(main_zodiac, "")
    
    # 吉祥生肖號碼組合
    favorable_zodiacs = [main_zodiac] + san_he_list + ([liu_he_zodiac] if liu_he_zodiac else [])
    
    # 建立可用號碼池（徹底排除相沖生肖號碼）
    chong_numbers = set(ZODIAC_NUMBERS.get(chong_zodiac, []))
    fav_numbers = set()
    for z in favorable_zodiacs:
        fav_numbers.update(ZODIAC_NUMBERS.get(z, []))
        
    valid_pool = list(fav_numbers - chong_numbers)
    if len(valid_pool) < 6:
        all_valid = [n for n in range(1, 50) if n not in chong_numbers]
        valid_pool = list(set(valid_pool + all_valid))
        
    # 讀取 Excel / CSV 數據，計算近 50 期 / 近 200 期冷熱號
    df = load_history_df()
    freq = {}
    if len(df) > 0 and period > 0:
        subset = df.tail(min(period, len(df)))
        all_nums = subset[['N1', 'N2', 'N3', 'N4', 'N5', 'N6']].values.flatten()
        freq = pd.Series(all_nums).value_counts().to_dict()
        
    # 計算權重
    weights = {}
    for num in valid_pool:
        w = 1.0
        # 生肖加權
        for z in favorable_zodiacs:
            if num in ZODIAC_NUMBERS.get(z, []):
                w += 1.5
                
        # 五行尾數加權
        if wuxing_pref in WUXING_TAILS and (num % 10 in WUXING_TAILS[wuxing_pref]):
            w += 2.0
            
        # 歷史冷熱號加權（盲抽時不疊加歷史數據）
        if period > 0:
            w += (freq.get(num, 0) * 0.3)
            
        weights[num] = w

    pool_nums = list(weights.keys())
    pool_weights = np.array([weights[n] for n in pool_nums])
    pool_probs = pool_weights / np.sum(pool_weights)
    
    # 隨機抽取並進行單雙/大小號結構過濾
    attempts = 0
    while attempts < 1000:
        attempts += 1
        drawn = np.random.choice(pool_nums, size=6, replace=False, p=pool_probs)
        
        odds = sum(1 for n in drawn if n % 2 != 0)
        bigs = sum(1 for n in drawn if n >= 25)
        
        if (2 <= odds <= 4) and (2 <= bigs <= 4):
            return sorted(drawn.tolist()), san_he_list, liu_he_zodiac, chong_zodiac
            
    return sorted(random.sample(valid_pool, 6)), san_he_list, liu_he_zodiac, chong_zodiac

# ==========================================
# 4. 網頁介面 (Streamlit UI)
# ==========================================
col1, col2 = st.columns((6, 7))

with col1: 
    st.subheader("🤖 生肖五行與 AI 多模型選號策略") 
    
    strategy = st.radio( 
        "選擇數據分析範圍:", 
        ("1. 完全隨機選號 (盲抽)", "2. 近 50 期 (捕捉短期旺門動量)", "3. 近 200 期 (捕捉長期均值頻率)"), 
        index=2 
    )

    st.markdown("---")
    st.subheader("🔮 生肖與五行玄學設定")
    main_zodiac = st.selectbox("請選擇主要生肖:", ZODIAC_ORDER, index=0)
    wuxing_pref = st.selectbox("選擇五行屬性偏好:", ["無偏好", "金 (尾數 4, 9)", "木 (尾數 3, 8)", "水 (尾數 1, 6)", "火 (尾數 2, 7)", "土 (尾數 0, 5)"])
    wuxing_key = wuxing_pref.split(" ")[0] if " " in wuxing_pref else "無偏好"

    if st.button("🎲 立即生成生肖 AI 預測號碼"):
        period = 0
        if "50" in strategy: period = 50
        elif "200" in strategy: period = 200

        with st.spinner("🚀 NumPy 引擎與生肖玄學高速運算中..."):
            pred_nums, san_he, liu_he, chong = get_zodiac_prediction(main_zodiac, wuxing_key, period)
            
            st.success("✅ 預測組合生成成功！")
            st.markdown(f"**主要生肖**：`{main_zodiac}` | **三合**：`{', '.join(san_he)}` | **六合**：`{liu_he}` | 🛑 **已避開相沖**：`{chong}`")
            
            display_nums = " - ".join([str(n).zfill(2) for n in pred_nums])
            st.markdown(f"### 🎯 推薦 1 組 6 個號碼: [ **{display_nums}** ]")

with col2: 
    st.subheader("📥 餵養與管理六合彩 Excel 資料庫") 
    st.caption("手動輸入或上傳 Excel/CSV 檔案更新開獎紀錄，保持數據最新狀態") 
    
    # 手動輸入單期開獎結果
    with st.expander("📝 1. 手動輸入單期開獎結果", expanded=True):
        draw_no = st.text_input("期數 (例: 26/072)") 
        nums_input = st.text_input("6 個號碼 (以逗號分隔, 例: 6,14,22,28,42,45)") 
        spec = st.number_input("特別號", 1, 49, step=1)

        if st.button("💾 儲存開獎紀錄至 Excel/CSV"):
            if draw_no and nums_input:
                try:
                    num_list = [int(x.strip()) for x in nums_input.split(',')]
                    if len(num_list) == 6:
                        df_curr = load_history_df()
                        new_row = pd.DataFrame([{
                            'DrawNo': draw_no, 
                            'N1': num_list[0], 'N2': num_list[1], 'N3': num_list[2], 
                            'N4': num_list[3], 'N5': num_list[4], 'N6': num_list[5], 
                            'Special': spec
                        }])
                        df_updated = pd.concat([df_curr, new_row], ignore_index=True)
                        save_history_df(df_updated)
                        st.success(f"✅ 第 {draw_no} 期紀錄已成功儲存至 Excel/CSV！")
                    else:
                        st.error("⚠️ 請確保剛好輸入 6 個號碼，並以逗號分隔。")
                except ValueError:
                    st.error("⚠️ 號碼格式錯誤！請確保只輸入數字及逗號。")
            else:
                st.warning("⚠️ 請填寫完整期數及號碼！")

    # 上傳 Excel / CSV 檔案
    with st.expander("📂 2. 上傳批次歷史 Excel / CSV 檔"):
        uploaded_file = st.file_uploader("選擇 .xlsx 或 .csv 檔案", type=['xlsx', 'csv'])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.xlsx'):
                    up_df = pd.read_excel(uploaded_file)
                else:
                    up_df = pd.read_csv(uploaded_file)
                
                req_cols = ['DrawNo', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Special']
                if all(c in up_df.columns for c in req_cols):
                    df_curr = load_history_df()
                    merged_df = pd.concat([df_curr, up_df[req_cols]], ignore_index=True)
                    save_history_df(merged_df)
                    st.success("✅ 批次歷史數據已成功更新至資料庫！")
                else:
                    st.error(f"⚠️ 檔案欄位不合規，需包含: {', '.join(req_cols)}")
            except Exception as e:
                st.error(f"⚠️ 檔案讀取失敗: {e}")

    # 下載目前數據庫為 Excel
    st.markdown("---")
    df_display = load_history_df()
    st.subheader(f"📊 歷史紀錄總覽 (共 {len(df_display)} 期)")
    
    # 下載按鈕
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_display.to_excel(writer, index=False, sheet_name='MarkSix_History')
    
    st.download_button(
        label="📥 下載完整歷史紀錄 Excel 檔 (.xlsx)",
        data=buffer.getvalue(),
        file_name="marksix_history.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 數據表顯示
    st.dataframe(df_display, use_container_width=True)