# app_streamlit.py

import streamlit as st
import io
import uuid # 用於為每個食物項目產生唯一ID

# 匯入我們自己建立的模組
try:
    from vision_module import vision_api # 或者您實際的 vision 模組路徑，例如 from Ճ<y_bin_46>python_code import vision_api
    import llm_module      # LLM 模組
    # Edamam 模組暫時不在此「全LLM」流程中使用，如果您想比較或備用，可以保留 import edamam_module
except ImportError as e:
    st.error(f"錯誤：無法匯入必要的程式模組: {e}。"
             "請確認 'vision_module/vision_api.py' 和 'llm_module.py' 檔案都存在且路徑正確。")
    st.stop() 

st.set_page_config(page_title="AI 食物助手 v5 - 全 LLM 分析 (含除錯)", layout="wide")
st.title("📸 AI 食物圖片全智能分析 (Vision API + LLM)")
st.subheader("食物辨識、典型份量建議、營養估算、多項目總計")

# --- 初始化 API 客戶端和憑證 ---
if hasattr(vision_api, 'setup_google_credentials'):
    vision_api.setup_google_credentials() 
else:
    st.error("嚴重錯誤：'setup_google_credentials' (Vision API) 函式未定義。")
    st.stop()

if hasattr(llm_module, 'initialize_vertex_ai'):
    if not llm_module._vertex_ai_initialized: 
        llm_module.initialize_vertex_ai() 
else:
    st.error("嚴重錯誤：'initialize_vertex_ai' (LLM) 函式未定義。")
    st.stop() 

# --- Session State 初始化 ---
default_session_state = {
    "uploaded_image_bytes": None,
    "current_file_name": None,
    "vision_object_results": None,
    "food_items_analysis": [], # 儲存最終分析出的食物項目列表
    "image_processed_flag": False 
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 側邊欄說明與狀態 ---
st.sidebar.header("使用說明")
st.sidebar.info(
    """
    1.  **上傳圖片**。
    2.  **AI 分析**：點擊按鈕。
    3.  **檢視與調整**：查看辨識出的食物列表，您可以調整克數並重新計算營養。
    4.  **查看總計**：底部顯示總營養。
    """
)
if hasattr(vision_api, '_google_credentials_set') and not vision_api._google_credentials_set:
    st.sidebar.error("GCP 憑證警告：Vision API 可能無法使用。", icon="⚠️")
if hasattr(llm_module, '_vertex_ai_initialized') and not llm_module._vertex_ai_initialized:
    st.sidebar.error("Vertex AI (LLM) 警告：LLM 功能可能無法使用。", icon="⚠️")


# --- 主應用程式介面 ---
uploaded_file = st.file_uploader(
    "1. 請上傳食物圖片進行分析:", 
    type=["jpg", "jpeg", "png"], 
    help="支援 JPG, JPEG, PNG 格式的圖片檔案。",
    key="file_uploader_main" # 確保有唯一的 key
)

if uploaded_file is not None:
    if st.session_state.current_file_name != uploaded_file.name:
        st.session_state.uploaded_image_bytes = uploaded_file.getvalue()
        st.session_state.current_file_name = uploaded_file.name
        st.session_state.food_items_analysis = [] 
        st.session_state.image_processed_flag = False 
        st.rerun() 

    image_bytes_to_show = st.session_state.get("uploaded_image_bytes")
    
    col_main, col_sidebar_placeholder = st.columns([0.65, 0.35])

    with col_main:
        if image_bytes_to_show:
            st.image(image_bytes_to_show, caption="您上傳的圖片", use_container_width=True)

        if st.button("🤖 **開始 AI 智能分析圖片中的所有食物**", key="analyze_all_foods_button", type="primary", use_container_width=True):
            st.session_state.food_items_analysis = [] 
            st.session_state.image_processed_flag = False
            st.markdown("--- DEBUGGING OUTPUTS BELOW ---") # 標記除錯輸出的開始

            if not vision_api._google_credentials_set or not llm_module._vertex_ai_initialized:
                st.error("錯誤：AI 服務未完全準備就緒 (GCP憑證或Vertex AI初始化問題)。請檢查側邊欄警告。")
            elif image_bytes_to_show:
                with st.spinner("AI 正在努力工作中... (Vision API 物件偵測...)"):
                    vision_results = vision_api.analyze_image_objects(image_bytes_to_show)
                
                # --- 加入除錯訊息 ---
                st.write("--- DEBUG: Vision API 原始結果 (vision_results) ---")
                st.json(vision_results if vision_results is not None else "Vision API 未返回結果或結果為 None (例如憑證或API呼叫問題)")
                # --- 除錯訊息結束 ---
                
                if vision_results: # 確保 vision_results 不是 None 也不是空列表
                    temp_food_items = []
                    processed_vision_names = set()
                    unique_vision_objects = []
                    for name, score in vision_results:
                        if score > 0.45 and name.lower() not in processed_vision_names : # 稍微降低信賴度閾值以進行測試
                            unique_vision_objects.append((name, score))
                            processed_vision_names.add(name.lower())
                    
                    # --- 加入除錯訊息 ---
                    st.write("--- DEBUG: 初步過濾和去重後的 Vision API 物件 (unique_vision_objects) ---")
                    st.json(unique_vision_objects if unique_vision_objects else "沒有符合初步過濾條件的 Vision API 物件")
                    # --- 除錯訊息結束 ---

                    if not unique_vision_objects:
                         st.info("Vision API 未偵測到足夠可用於後續分析的物件。")

                    for i, (object_name, vision_score) in enumerate(unique_vision_objects):
                        item_id = str(uuid.uuid4())
                        
                        st.write(f"--- DEBUG: 正在用 LLM 精煉 Vision 物件 {i+1}/{len(unique_vision_objects)}: '{object_name}' (Vision 信賴度: {vision_score:.2f}) ---")
                        
                        with st.spinner(f"LLM 正在處理物件 '{object_name}'..."):
                            refined_name_result = llm_module.refine_food_name_with_llm(object_name)
                        
                        st.write(f"--- DEBUG: LLM 對 '{object_name}' 的精煉結果 (refined_name_result) ---")
                        st.json(refined_name_result if refined_name_result else "LLM refine_food_name_with_llm 未返回結果或結果為 None")
                        
                        if refined_name_result and refined_name_result["status"] == "success":
                            food_name = refined_name_result["refined_name"]
                            original_vision_name = refined_name_result.get("original_name", object_name)
                            
                            st.write(f"--- DEBUG: LLM 精煉成功，食物名稱: '{food_name}'。準備獲取典型份量。 ---")
                            
                            with st.spinner(f"LLM 正在為 '{food_name}' 建議典型份量..."):
                                typical_portion_result = llm_module.get_typical_portion_grams_with_llm(food_name)
                            
                            st.write(f"--- DEBUG: LLM 對 '{food_name}' 的典型份量建議結果 (typical_portion_result) ---")
                            st.json(typical_portion_result if typical_portion_result else "LLM get_typical_portion_grams_with_llm 未返回結果或結果為 None")

                            suggested_grams = 100 # 預設值
                            if typical_portion_result and typical_portion_result["status"] == "success" and typical_portion_result["grams"] is not None:
                                suggested_grams = typical_portion_result["grams"]
                            elif typical_portion_result and typical_portion_result["status"] == "unknown_weight":
                                st.caption(f"提示：AI 未能為 '{food_name}' 建議典型克數，預設為 {suggested_grams}克。")
                            
                            st.write(f"--- DEBUG: 食物 '{food_name}'，建議/預設克數: {suggested_grams}克。準備獲取營養數據。 ---")
                            
                            with st.spinner(f"LLM 正在查詢 '{food_name}' ({suggested_grams}克) 的營養數據..."):
                                nutrition_data_result = llm_module.get_nutrition_from_llm(food_name, suggested_grams)
                            
                            st.write(f"--- DEBUG: LLM 對 '{food_name}' ({suggested_grams}克) 的營養數據查詢結果 (nutrition_data_result) ---")
                            st.json(nutrition_data_result if nutrition_data_result else "LLM get_nutrition_from_llm 未返回結果或結果為 None")
                            
                            nutrition_info = None
                            if nutrition_data_result and nutrition_data_result["status"] == "success":
                                nutrition_info = nutrition_data_result["data"]
                            elif nutrition_data_result and nutrition_data_result["status"] == "no_data":
                                 st.caption(f"提示：AI 未能查詢到 '{food_name}' ({suggested_grams}克) 的詳細營養數據。")
                            
                            temp_food_items.append({
                                "id": item_id,
                                "vision_object_name": original_vision_name,
                                "llm_refined_name": food_name,
                                "llm_suggested_grams": suggested_grams,
                                "user_grams": suggested_grams, 
                                "llm_nutrition_data": nutrition_info, 
                                "status_name_refinement": refined_name_result["status"],
                                "status_portion_suggestion": typical_portion_result.get("status") if typical_portion_result else "error",
                                "status_nutrition_fetch": nutrition_data_result.get("status") if nutrition_data_result else "error"
                            })
                        elif refined_name_result and refined_name_result["status"] == "category":
                            st.info(f"AI 判斷 '{object_name}' 是一個食物類別 '{refined_name_result['refined_name']}'，而非具體品項，已略過。")
                        elif refined_name_result and refined_name_result["status"] in ["not_food", "unknown_food"]:
                             st.info(f"AI 判斷 '{object_name}' 為 '{refined_name_result['status']}' ({refined_name_result.get('refined_name', '')})，已略過。")
                        # 其他 "error" 狀態會被自然略過

                    st.session_state.food_items_analysis = temp_food_items
                    st.session_state.image_processed_flag = True 
                    if not st.session_state.food_items_analysis:
                        st.warning("AI 分析完成，但未能從圖片中辨識出可供分析的具體食物項目。") 
                    else:
                        st.success(f"AI 分析完成！共辨識出 {len(st.session_state.food_items_analysis)} 個食物項目。請在下方調整份量並查看總營養。")
                    st.markdown("--- END DEBUGGING OUTPUTS ---") # 標記除錯輸出的結束
                    st.rerun() # 分析完成後，重跑一次以更新 UI 顯示食物列表

                else: # vision_results 是 None 或空
                    st.info("Vision API 未偵測到任何物件。請嘗試另一張圖片或檢查 API 設定。")
            else: 
                st.warning("請先上傳圖片。")

        # --- 顯示已分析的食物項目列表，並允許使用者修改份量 ---
        if st.session_state.image_processed_flag and st.session_state.food_items_analysis:
            st.markdown("---")
            st.subheader("📊 步驟 2: 檢視食物分析結果與調整份量")
            
            # 使用 st.session_state.food_items_analysis 來迭代，以確保修改能正確反映
            # 為了能修改列表中的項目（例如 user_grams, llm_nutrition_data），我們需要用索引來操作
            
            items_to_remove_indices = [] 

            for index in range(len(st.session_state.food_items_analysis)):
                item = st.session_state.food_items_analysis[index] # 獲取當前項目的可變引用

                # 使用 expander 來包裹每個食物項目，使介面更整潔
                with st.expander(f"食物項目 {index + 1}: **{item['llm_refined_name']}** (原始偵測: *{item['vision_object_name']}*)", expanded=True):
                    
                    col_gram_input, col_recalc_button, col_remove_button = st.columns([2,1,1])

                    with col_gram_input:
                        # 份量調整
                        new_user_grams = st.number_input(
                            f"份量 (克)", 
                            min_value=1, 
                            value=item["user_grams"], 
                            step=10, # 調整步伐
                            key=f"grams_input_{item['id']}" 
                        )
                    
                    item_needs_recalculation = False
                    if new_user_grams != item["user_grams"]:
                        item["user_grams"] = new_user_grams # 直接更新 session state 中的值
                        item["llm_nutrition_data"] = None # 克數變了，舊的營養數據失效
                        item_needs_recalculation = True # 標記需要重新計算按鈕出現
                    
                    # 如果沒有營養數據，也標記為需要計算 (通常是首次，或上一步LLM查詢營養失敗)
                    if item["llm_nutrition_data"] is None and item["status_nutrition_fetch"] != "no_data":
                         item_needs_recalculation = True

                    with col_recalc_button:
                        # 為了讓按鈕在同一行，可以使用 st.empty() 或 CSS，但簡單起見先這樣
                        st.write("") # 佔位，讓按鈕稍微下來一點
                        if st.button(f"🔄 計算營養", key=f"recalc_button_{item['id']}", help=f"使用 {item['user_grams']}克 重新計算 '{item['llm_refined_name']}' 的營養"):
                            with st.spinner(f"正在為 '{item['llm_refined_name']}' ({item['user_grams']}克) 重新查詢營養..."):
                                nutrition_result = llm_module.get_nutrition_from_llm(item["llm_refined_name"], item["user_grams"])
                                if nutrition_result and nutrition_result["status"] == "success":
                                    # 直接修改 session_state 中的項目
                                    st.session_state.food_items_analysis[index]["llm_nutrition_data"] = nutrition_result["data"]
                                    st.session_state.food_items_analysis[index]["status_nutrition_fetch"] = "success"
                                elif nutrition_result and nutrition_result["status"] == "no_data":
                                    st.session_state.food_items_analysis[index]["llm_nutrition_data"] = {}
                                    st.session_state.food_items_analysis[index]["status_nutrition_fetch"] = "no_data"
                                    st.warning(f"AI 未能提供 '{item['llm_refined_name']}' ({item['user_grams']}克) 的詳細營養數據。")
                                else: 
                                    st.session_state.food_items_analysis[index]["llm_nutrition_data"] = None
                                    st.session_state.food_items_analysis[index]["status_nutrition_fetch"] = "error"
                                    st.error(f"為 '{item['llm_refined_name']}' ({item['user_grams']}克) 查詢營養時發生錯誤。")
                            st.rerun() 

                    with col_remove_button:
                        st.write("") # 佔位
                        if st.button(f"❌ 移除", key=f"remove_button_{item['id']}", type="secondary"):
                            items_to_remove_indices.append(index)
                    
                    # 顯示該項目的營養成分
                    if item.get("llm_nutrition_data"): # 使用 .get() 避免因 key 不存在而報錯
                        nut_data = item["llm_nutrition_data"]
                        st.write(f"**估計營養 ({item['user_grams']} 克):**")
                        col_nut_disp_1, col_nut_disp_2 = st.columns(2)
                        with col_nut_disp_1:
                            st.metric("熱量", f"{nut_data.get('calories_kcal', 0):.0f} kcal", delta_color="off")
                            st.metric("蛋白質", f"{nut_data.get('protein_g', 0):.1f} g", delta_color="off")
                            st.metric("膳食纖維", f"{nut_data.get('fiber_g', 0):.1f} g", delta_color="off")
                        with col_nut_disp_2:
                            st.metric("總脂肪", f"{nut_data.get('fat_g', 0):.1f} g", delta_color="off")
                            st.metric("總碳水化合物", f"{nut_data.get('carbohydrates_g', 0):.1f} g", delta_color="off")
                    elif item["status_nutrition_fetch"] == "no_data":
                         st.caption(f"（AI 未能提供此項目 ({item['user_grams']}克) 的詳細營養數據）")
                    elif item_needs_recalculation: # 如果需要重新計算但按鈕還沒按
                         st.caption(f"（請點擊「🔄 計算營養」以獲取 {item['user_grams']}克的數據）")
                    elif item["status_nutrition_fetch"] == "error":
                         st.caption(f"（查詢此項目 ({item['user_grams']}克) 的營養時發生錯誤）")


            # 執行刪除 (在主迭代外部進行，避免修改正在迭代的列表)
            if items_to_remove_indices:
                for index_to_remove in sorted(items_to_remove_indices, reverse=True):
                    st.session_state.food_items_analysis.pop(index_to_remove)
                st.rerun() 

            # --- 顯示總營養攝取 ---
            if st.session_state.food_items_analysis: # 只有當列表不為空時才計算和顯示總計
                total_nutrition_summary = {
                    "calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, 
                    "carbohydrates_g": 0.0, "fiber_g": 0.0
                }
                valid_items_for_sum = 0
                for item in st.session_state.food_items_analysis:
                    if item.get("llm_nutrition_data"): # 只累加有成功獲取到營養數據的項目
                        nut_data = item["llm_nutrition_data"]
                        total_nutrition_summary["calories_kcal"] += float(nut_data.get('calories_kcal', 0))
                        total_nutrition_summary["protein_g"] += float(nut_data.get('protein_g', 0))
                        total_nutrition_summary["fat_g"] += float(nut_data.get('fat_g', 0))
                        total_nutrition_summary["carbohydrates_g"] += float(nut_data.get('carbohydrates_g', 0))
                        total_nutrition_summary["fiber_g"] += float(nut_data.get('fiber_g', 0))
                        valid_items_for_sum +=1
                
                if valid_items_for_sum > 0:
                    st.markdown("---")
                    st.subheader("📈 總計營養攝取 (所有已計算項目加總)")
                    sum_col1, sum_col2, sum_col3 = st.columns(3)
                    sum_col1.metric("總熱量", f"{total_nutrition_summary['calories_kcal']:.0f} kcal")
                    sum_col2.metric("總蛋白質", f"{total_nutrition_summary['protein_g']:.1f} g")
                    sum_col3.metric("總脂肪", f"{total_nutrition_summary['fat_g']:.1f} g")
                    
                    sum_col4, sum_col5, _ = st.columns(3)
                    sum_col4.metric("總碳水化合物", f"{total_nutrition_summary['carbohydrates_g']:.1f} g")
                    sum_col5.metric("總膳食纖維", f"{total_nutrition_summary['fiber_g']:.1f} g")


elif uploaded_file is None and st.session_state.get("current_file_name") is not None:
    # 使用者清除了上傳的檔案，重置相關 session state
    for key_to_reset in default_session_state.keys():
            if key_to_reset in st.session_state:
                 st.session_state[key_to_reset] = default_session_state[key_to_reset]
    st.rerun() 

elif uploaded_file is None:
    st.info("👈 請先上傳一張食物圖片以開始分析。")


st.markdown("---") 
st.caption("此應用程式使用 Google Cloud Vision API 及 Vertex AI (Gemini LLM) 進行分析。營養數據由 AI 生成，僅供參考，不應用於醫療用途。")