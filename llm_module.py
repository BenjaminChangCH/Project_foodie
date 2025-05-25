# llm_module.py
import streamlit as st
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason # type: ignore
import vertexai.preview.generative_models as generative_models # type: ignore
import json
from google.oauth2 import service_account # <<< 新增或確認此行

# 模組級別變數
_vertex_ai_initialized = False
_llm_model = None
_llm_model_name = "gemini-1.0-pro" # 使用基礎模型名稱，通常會指向最新的穩定版

# 您需要在 secrets.toml 中設定您的 GCP 專案 ID 和 Vertex AI 的區域
# 例如：
# GCP_PROJECT_ID = "your-gcp-project-id"
# GCP_VERTEX_LOCATION = "asia-east1" # 例如台灣的區域是 asia-east1, 或 us-central1 等

# llm_module.py
# ... (其他 import) ...

# llm_module.py
# ... (保留 _vertex_ai_initialized, _llm_model, _llm_model_name 的定義) ...

def initialize_vertex_ai():
    global _vertex_ai_initialized, _llm_model

    if _vertex_ai_initialized:
        return True

    gcp_project_id_from_secrets = st.secrets.get("GCP_PROJECT_ID")
    gcp_vertex_location_from_secrets = st.secrets.get("GCP_VERTEX_LOCATION")
    gcp_credentials_json_content = st.secrets.get("GCP_CREDENTIALS_JSON_CONTENT")

    # --- 更新的除錯 print 語句 ---
    print(f"--- DEBUG (llm_module.py | initialize_vertex_ai) ---")
    print(f"從 st.secrets 讀取的 GCP_PROJECT_ID: '{gcp_project_id_from_secrets}'")
    print(f"從 st.secrets 讀取的 GCP_VERTEX_LOCATION: '{gcp_vertex_location_from_secrets}'")
    # print(f"從 st.secrets 讀取的 GCP_CREDENTIALS_JSON_CONTENT (前100字元): '{str(gcp_credentials_json_content)[:100]}...'") # 注意不要完整印出金鑰
    # --- 除錯 print 語句結束 ---

    if not all([gcp_project_id_from_secrets, gcp_vertex_location_from_secrets, gcp_credentials_json_content]):
        missing_items = []
        if not gcp_project_id_from_secrets: missing_items.append("GCP_PROJECT_ID")
        if not gcp_vertex_location_from_secrets: missing_items.append("GCP_VERTEX_LOCATION")
        if not gcp_credentials_json_content: missing_items.append("GCP_CREDENTIALS_JSON_CONTENT")
        error_message = f"錯誤 (llm_module.py): st.secrets 中缺少必要的設定: {', '.join(missing_items)}。請檢查 .streamlit/secrets.toml。"
        if hasattr(st, 'error') and callable(st.error): st.error(error_message)
        else: print(error_message)
        _vertex_ai_initialized = False
        return False

    try:
        # 將從 secrets 讀取的 JSON 字串內容轉換為 Python 字典
        credentials_info = json.loads(gcp_credentials_json_content)

        # 從該字典創建一個 google.auth 的憑證物件
        credentials = service_account.Credentials.from_service_account_info(credentials_info)

        # 在初始化 Vertex AI 時，明確傳遞 project, location 和 credentials
        print(f"DEBUG (llm_module.py): 即將使用「明確的憑證物件」和以下參數初始化 Vertex AI: project='{gcp_project_id_from_secrets}', location='{gcp_vertex_location_from_secrets}'")
        vertexai.init(
            project=gcp_project_id_from_secrets,
            location=gcp_vertex_location_from_secrets,
            credentials=credentials  # <<< 明確傳遞憑證物件
        )

        _llm_model = GenerativeModel(_llm_model_name) # _llm_model_name 仍然是 "gemini-1.0-pro-002" 或您選擇的
        _vertex_ai_initialized = True
        print(f"DEBUG (llm_module.py): Vertex AI 初始化成功 (使用明確憑證)，已載入模型: '{_llm_model_name}'")
        return True

    except json.JSONDecodeError as e:
        error_message = f"錯誤 (llm_module.py): 'GCP_CREDENTIALS_JSON_CONTENT' 的內容不是有效的 JSON 格式: {e}"
        if hasattr(st, 'error') and callable(st.error): st.error(error_message)
        else: print(error_message)
        _vertex_ai_initialized = False
        return False
    except Exception as e:
        error_message = f"錯誤 (llm_module.py): 初始化 Vertex AI 或載入 Gemini 模型 '{_llm_model_name}' 失敗 (使用明確憑證): {e}"
        if hasattr(st, 'error') and callable(st.error): st.error(error_message)
        else: print(error_message)
        _vertex_ai_initialized = False
        return False
# ... (檔案中其他的函式 _generate_llm_response, refine_food_name_with_llm 等保持不變) ...

def _generate_llm_response(prompt_text, task_description="LLM 任務"):
    """
    通用的 LLM 回應生成函式。
    Args:
        prompt_text (str): 要發送給 LLM 的完整提示。
        task_description (str): 用於錯誤訊息中描述當前任務。
    Returns:
        str: LLM 生成的文字回應，或在錯誤時返回 None。
    """
    global _llm_model
    if not _vertex_ai_initialized:
        # print(f"警告 (llm_module.py): Vertex AI 未初始化，無法執行 {task_description}。")
        if not initialize_vertex_ai(): # 嘗試再次初始化
            return None
    
    if not _llm_model:
        print(f"錯誤 (llm_module.py): LLM 模型未載入，無法執行 {task_description}。")
        return None

    try:
        # print(f"DEBUG (llm_module.py): Sending prompt for {task_description}:\n{prompt_text}") # 除錯用
        
        # 設定生成參數，讓回答更穩定、簡潔
        generation_config = generative_models.GenerationConfig(
            temperature=0.1, # 溫度較低，回答更具確定性和一致性
            top_p=0.8,
            top_k=20,
            max_output_tokens=1024 # 根據預期回答長度調整，營養成分可能需要多一點
        )
        
        safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        response = _llm_model.generate_content(
            [prompt_text],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False,
        )
        
        # print(f"DEBUG (llm_module.py): LLM raw response for {task_description}: {response}") # 除錯用

        if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            if response.candidates[0].finish_reason not in [FinishReason.STOP, FinishReason.MAX_TOKENS]:
                print(f"警告 (llm_module.py): LLM ({task_description}) 生成內容可能未正常結束，原因: {response.candidates[0].finish_reason.name}")
            
            raw_text_response = response.candidates[0].content.parts[0].text.strip()
            # print(f"DEBUG (llm_module.py): LLM response text for {task_description} (raw): '{raw_text_response}'") # 除錯用
            return raw_text_response
        else:
            # print(f"警告 (llm_module.py): LLM ({task_description}) 未回傳有效內容。")
            return None
            
    except Exception as e:
        error_message = f"錯誤 (llm_module.py): 呼叫 LLM ({task_description}) 時發生錯誤: {e}"
        # print(f"DEBUG (llm_module.py): Exception during LLM call for {task_description}: {e}")
        # 在 Streamlit UI 中的錯誤應該由主程式 app_streamlit.py 處理，模組主要負責 print 供後台除錯
        print(error_message) 
        return None


def refine_food_name_with_llm(object_name_from_vision):
    """
    使用 LLM 分析 Vision API 偵測到的物件名稱，判斷是否為食物並精煉名稱。
    """
    prompt = f"""
    指令：
    分析以下由圖片辨識系統偵測到的物件名稱："{object_name_from_vision}"。
    你的任務是判斷這個物件名稱是否代表一個「具體的可食用食物品項」。

    判斷規則：
    1. 如果該物件名稱明確是一個「具體的可食用食物」(例如："apple", "banana", "chicken breast", "fried rice", "sushi")，請直接回覆該食物的常見、精確的英文名稱。
    2. 如果該物件名稱是一個「廣泛的食物類別」(例如："fruit", "vegetable", "meat", "dessert", "baked goods")，而不是一個可以獨立食用的具體品項，請回覆 "CATEGORY:[該類別的英文名稱]"，例如 "CATEGORY:Fruit"。
    3. 如果該物件名稱明確「不是可食用食物」(例如："plate", "table", "person", "utensil", "hand", "text")，請回覆 "NOT_FOOD"。
    4. 如果根據提供的物件名稱，你「無法明確判斷」它是否為具體食物 (例如："brown object", "round shape")，請回覆 "UNKNOWN_FOOD"。

    回答要求：
    - 你的回答只能是上述四種情況之一的結果。
    - 不要包含任何額外的解釋、前綴或引號。

    物件名稱："{object_name_from_vision}"
    你的判斷結果：
    """
    
    llm_response = _generate_llm_response(prompt, task_description=f"食物名稱精煉 for '{object_name_from_vision}'")
    
    if llm_response:
        if llm_response == "NOT_FOOD":
            return {"status": "not_food", "refined_name": object_name_from_vision}
        elif llm_response == "UNKNOWN_FOOD":
            return {"status": "unknown_food", "refined_name": object_name_from_vision}
        elif llm_response.startswith("CATEGORY:"):
            category_name = llm_response.split("CATEGORY:",1)[1].strip()
            return {"status": "category", "refined_name": category_name, "original_name": object_name_from_vision}
        else: # 假設是精煉後的食物名稱
            return {"status": "success", "refined_name": llm_response.strip(), "original_name": object_name_from_vision}
    return {"status": "error", "refined_name": object_name_from_vision, "error_message": "LLM response was None or empty"}


def get_typical_portion_grams_with_llm(refined_food_name):
    """
    使用 LLM 為指定的食物名稱建議一個「典型的單人份食用克數」。
    """
    prompt = f"""
    指令：
    針對以下食物名稱：「{refined_food_name}」。
    請提供一個「常見的」或「標準的」單人份食用份量，單位是「克 (grams)」。

    回答要求：
    1. 你的回答應該**只有一個數字**，代表克數。例如：150
    2. 如果你無法為這個食物判斷一個常見的克數，或者它通常不以克為單位衡量 (例如 "water")，請回覆 "UNKNOWN_WEIGHT"。
    3. 不要包含任何額外的文字、單位 (如 "g" 或 "克") 或解釋。

    食物名稱：「{refined_food_name}」
    建議的克數 (只需數字)：
    """
    llm_response = _generate_llm_response(prompt, task_description=f"典型份量克數建議 for '{refined_food_name}'")

    if llm_response:
        if llm_response == "UNKNOWN_WEIGHT":
            return {"status": "unknown_weight", "grams": None}
        try:
            grams = int(float(llm_response.strip())) # 嘗試轉換為浮點數再轉整數，以處理可能的 ".0"
            if grams > 0:
                 return {"status": "success", "grams": grams}
            else: # 克數小於等於0不合理
                return {"status": "error", "grams": None, "error_message": "LLM returned non-positive gram value."}
        except ValueError:
            # print(f"警告 (llm_module.py): LLM 為 '{refined_food_name}' 回傳的份量克數 '{llm_response}' 不是有效數字。")
            return {"status": "error", "grams": None, "error_message": f"LLM response '{llm_response}' is not a valid number for grams."}
    return {"status": "error", "grams": None, "error_message": "LLM response was None or empty for portion weight."}


def get_nutrition_from_llm(food_name, grams):
    """
    使用 LLM 為指定克數的特定食物查詢估計的營養成分。
    """
    if not food_name or not isinstance(grams, (int, float)) or grams <= 0:
        return {"status": "error", "data": None, "error_message": "Invalid input for food_name or grams."}

    prompt = f"""
    指令：
    請提供 {grams} 克「{food_name}」的估計營養成分。
    你需要包含以下營養素，並確保單位正確：
    - 熱量 (Calories / kcal)
    - 蛋白質 (Protein / g)
    - 總脂肪 (Total Fat / g)
    - 總碳水化合物 (Total Carbohydrates / g)
    - 膳食纖維 (Dietary Fiber / g)

    回答要求：
    1. 你的回答必須是一個**單行的、合法的 JSON 物件**。
    2. JSON 物件的鍵 (key) 必須是以下固定名稱 (全小寫，底線分隔)："calories_kcal", "protein_g", "fat_g", "carbohydrates_g", "fiber_g"。
    3. JSON 物件的值 (value) 必須是**數字** (可以是整數或小數)。
    4. 如果你找不到特定食物或份量的完整營養數據，或者某項營養素數據未知，請在該營養素的值使用 0 或 null。如果完全無法提供任何營養數據，請回覆一個空的 JSON 物件 {{}}。
    5. 不要包含任何 JSON 物件以外的文字、解釋或換行。

    範例回答格式：
    {{"calories_kcal": 200, "protein_g": 5.2, "fat_g": 8.1, "carbohydrates_g": 30.5, "fiber_g": 3.1}}
    或 (如果部分未知):
    {{"calories_kcal": 150, "protein_g": 12, "fat_g": null, "carbohydrates_g": 25, "fiber_g": 1.5}}
    或 (如果完全未知):
    {{}}

    食物：{grams} 克「{food_name}」
    JSON 格式的營養成分：
    """
    llm_response = _generate_llm_response(prompt, task_description=f"營養成分查詢 for {grams}g of '{food_name}'")

    if llm_response:
        try:
            # 嘗試去除 LLM 可能回傳的 markdown JSON 標記 (```json ... ```)
            if llm_response.startswith("```json"):
                llm_response = llm_response.strip("```json").strip("```").strip()
            elif llm_response.startswith("```"): # 有些模型可能只用 ```
                llm_response = llm_response.strip("```").strip()

            # print(f"DEBUG (llm_module.py): Cleaned LLM response for nutrition: '{llm_response}'") # 除錯用
            
            if not llm_response: # 如果清理後變空字串
                 return {"status": "error", "data": None, "error_message": "LLM returned an empty response after cleaning for nutrition."}

            nutrition_data = json.loads(llm_response) # 解析 LLM 回傳的 JSON 字串

            # 基本驗證，確保是字典且至少包含一些預期鍵值 (或為空字典表示找不到)
            if isinstance(nutrition_data, dict):
                # 可以再做更細緻的鍵值和型態檢查，但這裡我們先假設 LLM 盡力遵循格式
                # 如果是空字典，也視為一種有效的「找不到資料」的回應
                if not nutrition_data: # 如果是空字典 {}
                    return {"status": "no_data", "data": {}, "message": f"LLM 未能提供 {food_name} 的營養數據。"}

                # 標準化我們期望的鍵值 (可選，但建議)
                expected_keys = ["calories_kcal", "protein_g", "fat_g", "carbohydrates_g", "fiber_g"]
                processed_nutrition = {}
                all_keys_present_and_numeric_or_null = True
                for key in expected_keys:
                    value = nutrition_data.get(key)
                    if value is not None and not isinstance(value, (int, float)):
                        # print(f"警告 (llm_module.py): 營養素 '{key}' 的值 '{value}' 不是數字，將設為 0。")
                        processed_nutrition[key] = 0 # 或 None，取決於如何處理無效值
                        # all_keys_present_and_numeric_or_null = False # 如果嚴格要求所有鍵都必須是數字
                    elif value is None:
                         processed_nutrition[key] = 0 # 如果 LLM 回傳 null，我們當作 0
                    else:
                        processed_nutrition[key] = value
                
                # 如果我們只關心這些鍵，可以只回傳它們
                # return {"status": "success", "data": processed_nutrition}
                
                # 或者回傳 LLM 給的完整字典，讓主程式去挑選
                return {"status": "success", "data": nutrition_data} # 回傳 LLM 給的原始解析後的字典
            else:
                return {"status": "error", "data": None, "error_message": "LLM response for nutrition was not a valid JSON object (dictionary)."}

        except json.JSONDecodeError as e:
            # print(f"錯誤 (llm_module.py): 解析 LLM 回傳的營養 JSON 時失敗: {e}\n原始回應: '{llm_response}'") # 除錯用
            return {"status": "error", "data": None, "error_message": f"Failed to parse LLM's nutrition JSON response. Raw response: '{llm_response}'. Error: {e}"}
        except Exception as e: # 其他可能的錯誤
            # print(f"錯誤 (llm_module.py): 處理 LLM 營養回應時發生未知錯誤: {e}") # 除錯用
            return {"status": "error", "data": None, "error_message": f"Unknown error processing LLM nutrition response: {e}"}

    return {"status": "error", "data": None, "error_message": "LLM response was None or empty for nutrition."}

# 注意：initialize_vertex_ai() 應該在 app_streamlit.py 啟動時被明確呼叫一次。
