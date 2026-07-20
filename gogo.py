import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# ==========================================
# 1. 頁面與 UI/UX 規範設定
# ==========================================
st.set_page_config(
    page_title="產品年度銷售分析與 AI 商業洞察",
    page_icon="📈",
    layout="wide"
)

st.title("📈 產品年度銷售分析與 AI 商業洞察系統")
st.caption("結合動態數據模擬與 Gemini 2.5 Flash 人機協作決策")
st.write("---")


# ==========================================
# 2. 資料庫與數據處理 (含 Google Sheets gviz 標準讀取寫法)
# ==========================================
@st.cache_data
def load_google_sheet_data(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """
    [防坑指南] Google Sheets 讀取函數
    使用 gviz API 並指定 sheet_name，避免 HTTP 400 錯誤
    """
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(csv_url)


def generate_sales_data() -> pd.DataFrame:
    """隨機產生 12 個月產品銷售數據"""
    product_prices = {'A產品': 500, 'B產品': 300, 'C產品': 100}
    months = [f"{i}月" for i in range(1, 13)]

    data = {'月份': months}
    for product in product_prices.keys():
        data[f"{product}_銷量"] = np.random.randint(100, 1000, size=12)

    df = pd.DataFrame(data)
    for product, price in product_prices.items():
        df[f"{product}_營收"] = df[f"{product}_銷量"] * price

    df['總銷量'] = df[[f"{p}_銷量" for p in product_prices.keys()]].sum(axis=1)
    df['總營收'] = df[[f"{p}_營收" for p in product_prices.keys()]].sum(axis=1)
    return df


# 使用 Session State 維持數據穩定性
if 'df' not in st.session_state:
    st.session_state.df = generate_sales_data()

col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("🔄 重新產生隨機數據", type="primary"):
        st.session_state.df = generate_sales_data()
        st.session_state.ai_insight = None

df = st.session_state.df

# ==========================================
# 3. KPI 儀表板與 Plotly 資料視覺化
# ==========================================
total_revenue = df['總營收'].sum()
total_volume = df['總銷量'].sum()
avg_monthly = total_revenue / 12

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("💰 年度總營業額", f"${total_revenue:,.0f} 元")
kpi2.metric("📦 年度總銷售量", f"{total_volume:,.0f} 件")
kpi3.metric("📊 月平均營業額", f"${avg_monthly:,.0f} 元")

st.write("---")

tab1, tab2 = st.tabs(["📊 資料視覺化分析", "📋 原始數據明細"])

with tab1:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("產品各月度銷售量趨勢")
        fig_line = go.Figure()
        colors = {'A產品': '#1f77b4', 'B產品': '#ff7f0e', 'C產品': '#2ca02c'}
        for p in ['A產品', 'B產品', 'C產品']:
            fig_line.add_trace(go.Scatter(
                x=df['月份'], y=df[f"{p}_銷量"],
                mode='lines+markers', name=p,
                line=dict(color=colors[p], width=3)
            ))
        fig_line.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.02))
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("年度全部項目分析 (營收佔比)")
        pie_values = [df['A產品_營收'].sum(), df['B產品_營收'].sum(), df['C產品_營收'].sum()]
        fig_pie = px.pie(
            names=['A產品', 'B產品', 'C產品'],
            values=pie_values,
            hole=0.4,
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.dataframe(df, use_container_width=True, hide_index=True)

# ==========================================
# 4. Gemini API 人機協作（智慧模型探針與容錯處理）
# ==========================================
st.write("---")
st.subheader("✨ AI 首席分析師：一鍵商業洞察")

# 安全地從 Streamlit Secrets 讀取 API 金鑰
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ 未偵測到 `GEMINI_API_KEY`，請確認 `.streamlit/secrets.toml` 已設定。")
else:
    if st.button("🧠 商業洞察與決策建議", type="primary"):
        with st.spinner("AI 正在連接 Gemini API 解析數據中..."):
            try:
                genai.configure(api_key=api_key)

                # 1. 自動偵測目前 API Key 真正支援的模型清單
                available_models = [
                    m.name.replace('models/', '')
                    for m in genai.list_models()
                    if 'generateContent' in m.supported_generation_methods
                ]

                # 2. 嚴格優先指定 gemini-2.5-flash
                target_model = "gemini-2.5-flash"

                if target_model in available_models:
                    active_model = target_model
                else:
                    # 容錯處理：若 2.5-flash 尚在權限同步中，選取備援 Flash 模型
                    flash_candidates = [m for m in available_models if 'flash' in m]
                    active_model = flash_candidates[0] if flash_candidates else available_models[0]

                # 3. 呼叫 Gemini 進行商業分析
                model = genai.GenerativeModel(active_model)
                data_csv = df.to_csv(index=False)

                prompt = f"""
                你是一位頂尖的商業數據分析師。請根據以下 12 個月的銷售數據 CSV，產出一份精簡且具體的商業洞察報告。
                產品單價設定：A產品 $500, B產品 $300, C產品 $100。

                數據資料：
                {data_csv}

                請分析：
                1. 核心業績亮點與銷售主力產品。
                2. 月度趨勢中的極端值或異常變化點。
                3. 3 點具體可執行的下一步營運建議（例如促銷搭售、庫存準備等）。
                """

                response = model.generate_content(prompt)
                st.session_state.ai_insight = response.text
                st.session_state.used_model = active_model
                st.session_state.all_models = available_models

            except Exception as e:
                st.error(f"❌ AI 通話失敗：{e}")

# 顯示分析報告與診斷資訊
if st.session_state.get('ai_insight'):
    st.success(f"✅ 已成功調用模型：`{st.session_state.used_model}`")
    with st.expander("💡 查看 AI 分析師商業洞察報告", expanded=True):
        st.markdown(st.session_state.ai_insight)

    with st.expander("🔍 系統模型診斷資訊", expanded=False):
        st.write("目前 API 金鑰已連線並可使用的模型列表：")
        st.json(st.session_state.get('all_models', []))