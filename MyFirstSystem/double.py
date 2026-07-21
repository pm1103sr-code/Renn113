import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd

# ==========================================
# 1. 系統與頁面初始化
# ==========================================
st.set_page_config(
    page_title="AI 泰國蝦爆籠大師",
    page_icon="🦐",
    layout="wide"
)

# 安全讀取 API Key
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error("⚠️ 系統啟動失敗：請確認 `.streamlit/secrets.toml` 中已正確設定 `GEMINI_API_KEY`。")
    st.stop()


# ==========================================
# 2. 資料庫快取與讀取 (嚴守防坑指南：使用 gviz)
# ==========================================
@st.cache_data(ttl=600)  # 快取 10 分鐘，優化效能與 API 請求次數
def load_fishing_records(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """
    讀取 Google Sheets 作為輕量資料庫。
    ⚠️ 絕對不使用 gid=0，一律使用 gviz api 並指定 sheet_name！
    """
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.warning("目前尚無歷史戰績資料，或資料庫連線尚未設定。")
        return pd.DataFrame()


# ==========================================
# 3. 系統主介面 UI/UX
# ==========================================
st.title("🦐 AI 泰國蝦爆籠大師：實境標點分析系統")
st.markdown("**「看不懂水泡沒關係，讓 AI 幫你找蝦窟！」** 拍照上傳，立刻獲得職業級下竿建議。")

# 使用 Tabs 收納不同功能，保持介面清爽
tab_analysis, tab_records = st.tabs(["📸 實境水池分析", "📊 戰績資料庫 (開發示範)"])

with tab_analysis:
    # 檔案上傳區
    uploaded_file = st.file_uploader("請上傳一張您前方釣蝦場水池的清晰照片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 使用 columns 進行左右排版
        col_img, col_ai = st.columns([1, 1], gap="large")

        with col_img:
            # ⚠️ 防坑指南：使用 Pillow 正確讀取圖片轉為 Bytes
            image = Image.open(uploaded_file)
            st.image(image, caption="您的實境視野", use_container_width=True)

        with col_ai:
            st.subheader("🤖 小容 AI 敏捷分析")
            if st.button("🚀 開始尋找黃金標點", type="primary", use_container_width=True):
                with st.spinner("AI 正在高速解析水流與氣泡分佈..."):
                    try:
                        # 🌟 終極升級：切換至最新世代 gemini-3.5-flash 模型，突破新帳號限制！
                        model = genai.GenerativeModel('gemini-3.5-flash')

                        # 打造強大且具備領域知識的 Prompt
                        prompt = """
                        你是一位擁有20年經驗的職業釣蝦大師。請分析這張釣蝦場的照片，並針對「泰國蝦」提供以下建議：
                        1. 【黃金標點預測】：明確指出照片中哪裡可能是蝦子群聚的「蝦窟」（例如：水泡區周圍、打氣孔旁、死角、陰影處、幫浦進水處）。
                        2. 【水流評估與釣組】：根據水波紋推測水流狀態，並給予浮標調校（如：敏釣、頓釣）與量水深的建議。
                        3. 【實戰晃餌策略】：提供適合當下環境的誘蝦技巧（如：拖底、微晃餌、找蝦網邊緣）。
                        請用充滿自信、幽默且專業的繁體中文條列式回答。
                        """

                        # 執行多模態分析
                        response = model.generate_content([prompt, image])

                        st.success("✅ 解析完成！請參考以下大師建議：")
                        st.markdown(response.text)

                    except Exception as e:
                        st.error(f"分析過程發生錯誤，請重試。詳細錯誤訊息：{e}")

            # 展開元件：人機協作回饋機制
            with st.expander("💡 人機協作：記錄本次釣況"):
                st.write("根據 AI 的建議下竿後，請記錄您的真實戰果，幫助系統未來迭代進化！")
                st.number_input("該標點成功起蝦數量", min_value=0, step=1)
                st.text_input("使用的餌料 (如：赤尾青、豬肉餌)")
                if st.button("儲存戰績 (尚未串接寫入功能)"):
                    st.success("戰績已暫存！大師之路又邁進了一步！")

with tab_records:
    st.subheader("歷史爆籠數據庫")
    st.info("此區塊展示如何正確、安全地從 Google Sheets 讀取您的歷史戰果。")

    # 示範讀取資料庫的架構
    demo_sheet_id = "YOUR_GOOGLE_SHEET_ID_HERE"
    demo_sheet_name = "戰績表"

    st.code(f"""
    # 讀取程式碼範例：
    sheet_id = "{demo_sheet_id}"
    sheet_name = "{demo_sheet_name}"
    df = load_fishing_records(sheet_id, sheet_name)
    st.dataframe(df)
    """, language="python")