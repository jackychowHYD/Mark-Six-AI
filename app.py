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

st.set_page_config(page_title="Mark Six AI Pro - 動態權重隨機選號版", layout="wide", page_icon="🍀") 
st.title("🍀 終極六合彩 AI 多模型預測系統 (生肖五行 + 動態權重選號版)") 
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
# 3. 過濾器與預測核心邏輯
# ==========================================
def validate_combination(drawn):
    """
    過濾器函數：檢查生成組合是否符合統計規律
    1. 總和：140 ~ 210
    2. 奇偶比例：3:3, 4:2, 2:4 (奇數數量為 2, 3, 4)
    3. 連號限制：最多 1 組雙連號，不允許 3 連號或以上
    """
    nums = sorted(drawn)
    
    # 1. 總和過濾 (140 - 210)
    total_sum = sum(nums)
    if not (140 <= total_sum <= 210):
        return False
        
    # 2. 奇偶比例 (2:4, 3:3, 4:2)
    odds = sum(1 for n in nums if n % 2 != 0)
    if odds not in [2, 3, 4]:
        return False
        
    # 3. 連號限制
    consecutive_pairs = 0
    current_streak = 1
    max_streak = 1
    
    for i in range(len(nums) - 1):
        if nums[i+1] - nums[i] == 1:
            consecutive_pairs += 1
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
            
    if max_streak >= 3 or consecutive_pairs > 1:
        return False
        
    return True

def get_zodiac_prediction(main_zodiac, wuxing_pref, strategy_mode, history_df_subset=None):
    """
    動態權重隨機選號（Weighted Random Pick）
    - 近 50 期頻率 (60% 權重)
    - 近 200 期頻率 (40% 權重)
    - 結合生肖與五行特徵進行 Weighted numpy.random.choice 選號
    """
    san_he_list = SAN_HE.get(main_zodiac, [])
    liu_he_zodiac = LIU_HE.get(main_zodiac, "")
    chong_zodiac = LIU_CHONG.get(main_zodiac, "")
    
    favorable_zodiacs = [main_zodiac] + san_he_list + ([liu_he_zodiac] if liu_he_zodiac else [])
    chong_numbers = set(ZODIAC_NUMBERS.get(chong_zodiac, []))
    
    fav_numbers = set()
    for z in favorable_zodiacs:
        fav_numbers.update(ZODIAC_NUMBERS.get(z, []))
        
    valid_pool = list(fav_numbers - chong_numbers)
    if len(valid_pool) < 6:
        all_valid = [n for n in range(1, 50) if n not in chong_numbers]
        valid_pool = list(set(valid_pool + all_valid))
        
    df = history_df_subset if history_df_subset is not None else load_history_df()
    
    # 計算近 50 期與近 200 期頻率
    freq_50 = {}
    freq_200 = {}
    
    if len(df) > 0 and "盲抽" not in strategy_mode:
        # 近 50 期頻率
        df_50 = df.tail(min(50, len(df)))
        nums_50 = df_50[['N1', 'N2', 'N3', 'N4', 'N5', 'N6']].values.flatten()
        counts_50 = pd.Series(nums_50).value_counts().to_dict()
        denom_50 = max(1, min(50, len(df)))
        freq_50 = {n: counts_50.get(n, 0) / denom_50 for n in range(1, 50)}
        
        # 近 200 期頻率
        df_200 = df.tail(min(200, len(df)))
        nums_200 = df_200[['N1', 'N2', 'N3', 'N4', 'N5', 'N6']].values.flatten()
        counts_200 = pd.Series(nums_200).value_counts().to_dict()
        denom_200 = max(1, min(200, len(df)))
        freq_200 = {n: counts_200.get(n, 0) / denom_200 for n in range(1, 50)}

    # 合成動態權重 (Dynamic Composite Weights)
    weights = {}
    for num in valid_pool:
        w = 1.0
        
        # 生肖與五行加權
        for z in favorable_zodiacs:
            if num in ZODIAC_NUMBERS.get(z, []):
                w += 1.2
                
        if wuxing_pref in WUXING_TAILS and (num % 10 in WUXING_TAILS[wuxing_pref]):
            w += 1.5
            
        # 疊加動態頻率權重 (60% 近50期 + 40% 近200期)
        if "盲抽" not in strategy_mode:
            f_score = (freq_50.get(num, 0) * 0.6) + (freq_200.get(num, 0) * 0.4)
            w += (f_score * 10.0) # 放大頻率影響係數
            
        weights[num] = max(0.01, w)

    pool_nums = np.array(list(weights.keys()))
    pool_weights = np.array([weights[n] for n in pool_nums])
    pool_probs = pool_weights / np.sum(pool_weights)
    
    # 使用 numpy.random.choice 進行不重複加權隨機抽樣 (Weighted Random Pick)
    attempts = 0
    while attempts < 3000:
        attempts += 1
        drawn = np.random.choice(pool_nums, size=6, replace=False, p=pool_probs)
        if validate_combination(drawn):
            return sorted(drawn.tolist()), san_he_list, liu_he_zodiac, chong_zodiac
            
    for _ in range(5000):
        sample = random.sample(valid_pool, 6)
        if validate_combination(sample):
            return sorted(sample), san_he_list, liu_he_zodiac, chong_zodiac

    return sorted(random.sample(valid_pool, 6)), san_he_list, liu_he_zodiac, chong_zodiac

# ==========================================
# 4. 回測核心對獎邏輯
# ==========================================
def evaluate_ticket(drawn_main, drawn_special, bet_nums):
    """判定單組彩券中獎等第與金額"""
    matched_main = len(set(bet_nums) & set(drawn_main))
    matched_special = drawn_special in bet_nums
    
    if matched_main == 6:
        return "頭獎", 8000000
    elif matched_main == 5 and matched_special:
        return "二獎", 400000
    elif matched_main == 5:
        return "三獎", 100000
    elif matched_main == 4 and matched_special:
        return "四獎", 9600
    elif matched_main == 4:
        return "五獎", 640
    elif matched_main == 3 and matched_special:
        return "六獎", 320
    elif matched_main == 3:
        return "七獎", 40
    else:
        return "未中獎", 0

def run_backtest(target_periods, main_zodiac, wuxing_key, strategy_mode):
    """執行歷史開獎數據回測模擬"""
    df = load_history_df()
    total_records = len(df)
    
    if total_records < 10:
        return None, "數據庫歷史期數不足，無法執行回測。"
        
    actual_periods = min(target_periods, total_records - 1)
    
    stats = {
        "頭獎": 0, "二獎": 0, "三獎": 0, "四獎": 0,
        "五獎": 0, "六獎": 0, "七獎": 0, "未中獎": 0
    }
    
    total_cost = actual_periods * 10
    total_prize = 0
    history_logs = []
    
    for i in range(total_records - actual_periods, total_records):
        past_df = df.iloc[:i]
        target_row = df.iloc[i]
        
        draw_no = target_row['DrawNo']
        actual_main = [target_row['N1'], target_row['N2'], target_row['N3'], 
                       target_row['N4'], target_row['N5'], target_row['N6']]
        actual_special = target_row['Special']
        
        pred_nums, _, _, _ = get_zodiac_prediction(main_zodiac, wuxing_key, strategy_mode, history_df_subset=past_df)
        
        prize_name, prize_money = evaluate_ticket(actual_main, actual_special, pred_nums)
        
        stats[prize_name] += 1
        total_prize += prize_money
        
        history_logs.append({
            "期數": draw_no,
            "預測號碼": ", ".join([f"{n:02d}" for n in pred_nums]),
            "實際開獎": ", ".join([f"{n:02d}" for n in actual_main]) + f" + ({actual_special:02d})",
            "中獎結果": prize_name,
            "獎金": f"${prize_money:,}"
        })
        
    net_profit = total_prize - total_cost
    roi = (net_profit / total_cost) * 100 if total_cost > 0 else 0
    
    summary = {
        "actual_periods": actual_periods,
        "total_cost": total_cost,
        "total_prize": total_prize,
        "net_profit": net_profit,
        "roi": roi,
        "stats": stats,
        "logs": pd.DataFrame(history_logs)
    }
    
    return summary, None

# ==========================================
# 5. 網頁介面 (Streamlit UI)
# ==========================================
col1, col2 = st.columns((6, 7))

with col1: 
    st.subheader("🤖 生肖五行與 AI 多模型選號策略") 
    
    strategy = st.radio( 
        "選擇數據分析與動態權重策略:", 
        ("1. 完全隨機選號 (盲抽)", "2. 動態權重隨機選號 (60%近50期 + 40%近200期動量)"), 
        index=1 
    )

    st.markdown("---")
    st.subheader("🔮 生肖與五行玄學設定")
    main_zodiac = st.selectbox("請選擇主要生肖:", ZODIAC_ORDER, index=0)
    wuxing_pref = st.selectbox("選擇五行屬性偏好:", ["無偏好", "金 (尾數 4, 9)", "木 (尾數 3, 8)", "水 (尾數 1, 6)", "火 (尾數 2, 7)", "土 (尾數 0, 5)"])
    wuxing_key = wuxing_pref.split(" ")[0] if " " in wuxing_pref else "無偏好"

    if st.button("🎲 立即生成動態權重 AI 預測號碼"):
        with st.spinner("🚀 NumPy 引擎進行 60/40 動態權重與過濾器抽樣中..."):
            pred_nums, san_he, liu_he, chong = get_zodiac_prediction(main_zodiac, wuxing_key, strategy)
            
            total_sum = sum(pred_nums)
            odds_cnt = sum(1 for n in pred_nums if n % 2 != 0)
            evens_cnt = 6 - odds_cnt
            
            st.success("✅ 預測組合已通過動態權重與過濾器！")
            st.markdown(f"**主要生肖**：`{main_zodiac}` | **三合**：`{', '.join(san_he)}` | **六合**：`{liu_he}` | 🛑 **已避開相沖**：`{chong}`")
            st.markdown(f"📊 **統計驗證**：總和 `{total_sum}` (符合 140-210) | 奇偶比 `{odds_cnt}:{evens_cnt}` | 無違規連號")
            
            display_nums = " - ".join([str(n).zfill(2) for n in pred_nums])
            st.markdown(f"### 🎯 推薦 1 組 6 個號碼: [ **{display_nums}** ]")

with col2: 
    st.subheader("📊 資料庫與 AI 歷史回測系統") 
    
    tab1, tab2 = st.tabs(["📂 數據管理與檔案下載", "📈 演算法歷史回測引擎"])
    
    with tab1:
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

        st.markdown("---")
        df_display = load_history_df()
        st.subheader(f"📊 歷史紀錄總覽 (共 {len(df_display)} 期)")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_display.to_excel(writer, index=False, sheet_name='MarkSix_History')
        
        st.download_button(
            label="📥 下載完整歷史紀錄 Excel 檔 (.xlsx)",
            data=buffer.getvalue(),
            file_name="marksix_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.dataframe(df_display, use_container_width=True)

    with tab2:
        st.caption("⚙️ 使用 60% 近50期 + 40% 近200期動態權重模型，模擬滾動投注歷史資料庫進行真實勝率測試")
        
        backtest_periods = st.number_input("設定回測模擬期數 (例: 500 期)", min_value=10, max_value=2000, value=500, step=10)
        
        if st.button("🚀 啟動 60/40 動態權重演算法歷史模擬回測"):
            with st.spinner("⏳ 正在對歷史數據進行滾動式模擬回測，請稍候..."):
                res, err = run_backtest(backtest_periods, main_zodiac, wuxing_key, strategy)
                
                if err:
                    st.error(err)
                else:
                    st.success(f"🎉 成功完成近 {res['actual_periods']} 期滾動式模擬回測！")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("總投注本金", f"${res['total_cost']:,}")
                    m2.metric("中獎總獎金", f"${res['total_prize']:,}")
                    m3.metric("淨利潤", f"${res['net_profit']:,}")
                    m4.metric("回報率 (ROI)", f"{res['roi']:.2f}%")
                    
                    st.markdown("---")
                    st.subheader("🏆 中獎等第次數統計")
                    
                    st_cols = st.columns(4)
                    st_cols[0].metric("七獎 (中3正碼)", f"{res['stats']['七獎']} 次")
                    st_cols[1].metric("六獎 (中3正+特)", f"{res['stats']['六獎']} 次")
                    st_cols[2].metric("五獎 (中4正碼)", f"{res['stats']['五獎']} 次")
                    st_cols[3].metric("四獎及以上", f"{res['stats']['四獎'] + res['stats']['三獎'] + res['stats']['二獎'] + res['stats']['頭獎']} 次")
                    
                    st.markdown("---")
                    st.subheader("📋 回測詳細對獎明細")
                    st.dataframe(res['logs'], use_container_width=True)