# app_streamlit.py

import streamlit as st
import io # 用於處理圖片上傳的位元組流

# 匯入我們自己建立的 vision_api 模組
# 假設您的 vision_api.py 檔案位於名為 'vision_module' 的資料夾中，
# 並且 'vision_module' 資料夾與 'app_streamlit.py' 在同一層級 (都在 'project_foodie' 內)。
# 如果您的資料夾名稱不同 (例如您之前使用的是 'Ճ<y_bin_46>python_code')，請相應修改 'vision_module'。
try:
    from vision_module import vision_api 
except ImportError as e:
    # 如果匯入失敗，很可能是檔案路徑或名稱有問題
    st.error(f"錯誤：無法匯入 vision_api 模組: {e}。"
             "請確認 'vision_module/vision_api.py' (或您實際的模組路徑) 檔案存在，並且資料夾結構正確。")
    st.stop() # 停止應用程式執行，因為核心模組無法載入

# 設定網頁的標題和佈局方式
st.set_page_config(page_title="AI 食物助手 (Vision API 測試)", layout="wide")
st.title("📸 AI 食物圖片分析助手")
st.subheader("使用 Google Cloud Vision API")

# --- 非常重要：在應用程式啟動時，呼叫一次憑證設定函式 ---
# 這會執行 vision_api.py 中的 setup_google_credentials()，
# 嘗試從 .streamlit/secrets.toml (本地) 或 Streamlit Cloud Secrets (部署時) 讀取金鑰內容，
# 並設定好環境變數，以便 google-cloud-vision 套件可以找到憑證。
if hasattr(vision_api, 'setup_google_credentials'): # 檢查函式是否存在於模組中
    vision_api.setup_google_credentials()
else:
    st.error("嚴重錯誤：'setup_google_credentials' 函式在 vision_api 模組中未定義。應用程式無法繼續。")
    st.stop() # 如果核心的憑證設定函式不存在，則停止應用程式
# ---------------------------------------------------------------

# 側邊欄的說明文字
st.sidebar.header("使用說明")
st.sidebar.info(
    """
    1.  點擊下方的「瀏覽檔案」按鈕，或直接將圖片拖放到該區域，以上傳一張包含食物的圖片。
    2.  圖片上傳成功後，它會顯示在頁面左側。
    3.  點擊右側的「開始分析圖片」按鈕。
    4.  應用程式將使用 Google Cloud Vision API 來辨識圖片中的主要食物內容標籤。
    """
)

# 在側邊欄顯示一個警告，如果憑證設定不成功
# vision_api._google_credentials_set 是我們在 vision_api.py 中設定的全域變數，用來追蹤憑證狀態
if hasattr(vision_api, '_google_credentials_set') and not vision_api._google_credentials_set:
    st.sidebar.error(
        "警告：GCP 憑證未能成功載入。圖片分析功能可能無法使用。 "
        "請檢查您的 `.streamlit/secrets.toml` 檔案中的 'GCP_CREDENTIALS_JSON_CONTENT' 項目，"
        "或相關的 GCP 設定與金鑰權限。",
        icon="⚠️"
    )

# --- 主應用程式介面 ---
# 檔案上傳元件
uploaded_file = st.file_uploader(
    "1. 請上傳食物圖片進行分析:", 
    type=["jpg", "jpeg", "png"], # 限制可上傳的檔案類型為這三種圖片格式
    help="將圖片拖放到此處，或點擊瀏覽檔案。支援 JPG, JPEG, PNG 格式。" # 滑鼠移到上傳區域時顯示的輔助說明文字
)

if uploaded_file is not None: # 如果使用者已成功上傳檔案
    image_bytes = uploaded_file.getvalue() # 獲取上傳圖片的原始位元組數據

    # 使用 st.columns 將頁面分為兩欄，讓圖片和結果並排顯示，佈局更美觀
    col1, col2 = st.columns([0.6, 0.4]) # 左欄佔 60% 寬度，右欄佔 40%

    with col1: # 在左欄顯示上傳的圖片
        st.image(image_bytes, caption="您上傳的圖片", use_column_width=True) # use_column_width=True 讓圖片寬度符合欄寬

    with col2: # 在右欄顯示分析按鈕和分析結果
        if st.button("🔍 開始分析圖片", type="primary", use_container_width=True, key="analyze_button"):
            if image_bytes: # 再次確認圖片數據存在 (通常 uploaded_file is not None 就表示存在)
                # 檢查 GCP 憑證是否已成功設定 (從 vision_api 模組的全域變數讀取狀態)
                if not vision_api._google_credentials_set:
                    st.error("無法進行分析：GCP 憑證尚未成功設定。請檢查您的 secrets.toml 設定或程式碼中的憑證處理邏輯。")
                else:
                    # 顯示處理中動畫 (spinner)，並呼叫 vision_api 模組中的分析函式
                    with st.spinner("圖片分析中，過程可能會需要幾秒鐘，請稍候..."):
                        if hasattr(vision_api, 'analyze_image_labels'): # 再次檢查函式是否存在於模組中
                            analysis_results = vision_api.analyze_image_labels(image_bytes)
                        else:
                            st.error("嚴重錯誤：'analyze_image_labels' 函式在 vision_api 模組中未定義。")
                            analysis_results = None # 設為 None 以避免後續錯誤

                    st.markdown("---") # 畫一條分隔線，讓結果更清晰
                    if analysis_results is not None: # 如果 analyze_image_labels 函式成功執行 (可能返回空列表，或有結果)
                        if analysis_results: # 如果結果列表不是空的 (即有辨識到標籤)
                            st.subheader("👁️ 圖片分析結果 (來自 Google Vision API):")
                            # 迭代顯示每一個辨識到的標籤及其信賴度
                            for description, score in analysis_results:
                                # 之後我們會在這裡加入中文翻譯的步驟
                                st.write(f"- **{description}** (信賴度: {score:.1%})") # .1% 表示顯示為百分比，小數點後一位
                        else: # 結果列表是空的 (API 成功呼叫了，但沒辨識出任何它認為相關的標籤)
                            st.info("未能從圖片中分析出任何顯著的標籤 (Vision API 返回了空的結果列表)。")
                    # 如果 analysis_results 為 None，表示在 analyze_image_labels 函式內部發生了錯誤，
                    # 且該函式應該已經透過 st.error 或 print (在終端機顯示) 處理了錯誤訊息的提示。
            else:
                # 理論上 uploaded_file is not None 時 image_bytes 就會有值, 但多一層檢查無妨
                st.warning("圖片內容為空，請重新上傳。") 
else: # 如果使用者還沒上傳檔案
    st.info("請先上傳一張食物圖片，然後點擊「開始分析圖片」按鈕。")

st.markdown("---") # 頁尾分隔線
st.caption("此應用程式使用 Google Cloud Vision API 進行圖片內容分析。")