import streamlit as st  # Streamlit 本身
import requests         # 用於發送 API 請求
import json             # 用於處理 JSON 資料 (主要是為了美化輸出，fetch_food_from_api 會用到)
import pandas as pd # <--- 新增這一行
# 用於處理資料框 (DataFrame)，如果需要顯示表格或進行資料處理

# --- 請填入您真實且有效的 Edamam API 憑證 ---
EDAMAM_APP_ID = "d3dffabe"  # 替換成您的 App ID
EDAMAM_APP_KEY = "84e836c03e271f07dafeb480112e9595" # 替換成您的 App Key
# 如果您的 Edamam 設定仍然需要 Edamam-Account-User 標頭
# USER_ID_FOR_HEADER = "mytestuser123" # 您可以取消註解並使用它
# ------------------------------------------------

def fetch_food_from_api(food_name_to_search): # 這是我們之前定義的函式
    """
    嘗試從 Edamam API 獲取指定食物的營養資訊。
    """
    base_url = "https://api.edamam.com"
    parser_endpoint = "/api/food-database/v2/parser"
    request_url = f"{base_url}{parser_endpoint}?ingr={food_name_to_search}&app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}"

    headers_to_send = {}
    # # 如果您的 Edamam 設定需要 User ID Header (定義 USER_ID_FOR_HEADER 並取消下面這行的註解)
    # if 'USER_ID_FOR_HEADER' in globals() and USER_ID_FOR_HEADER:
    #    headers_to_send["Edamam-Account-User"] = USER_ID_FOR_HEADER

    try:
        response = None
        if headers_to_send:
            response = requests.get(request_url, headers=headers_to_send)
        else:
            response = requests.get(request_url)

        if response.status_code != 200:
            # 在 Streamlit 中，我們可以用 st.error() 顯示錯誤訊息給開發者看，但函式本身應回傳 None
            # st.error(f"API 錯誤：狀態碼 {response.status_code} - {response.text}") # 暫時先不在函式內用st元件
            print(f"DEBUG: API 錯誤：狀態碼 {response.status_code} - {response.text}") # 除錯時可用 print
            return None

        data = response.json()

        if "parsed" in data and data["parsed"]:
            api_food_data = data["parsed"][0]["food"]
            nutrients_from_api = api_food_data.get("nutrients", {})
            formatted_nutrition_data = {
                "食物名稱": api_food_data.get("label", food_name_to_search),
                "食物ID": api_food_data.get("foodId", "N/A"),
                "熱量": nutrients_from_api.get("ENERC_KCAL", 0.0),
                "蛋白質": nutrients_from_api.get("PROCNT", 0.0),
                "碳水": nutrients_from_api.get("CHOCDF", 0.0),
                "脂肪": nutrients_from_api.get("FAT", 0.0)
            }
            return formatted_nutrition_data
        else:
            # st.warning(f"API 未能解析食物: '{food_name_to_search}'") # 暫時先不在函式內用st元件
            print(f"DEBUG: API 未能解析食物: '{food_name_to_search}'") # 除錯時可用 print
            return None

    except requests.exceptions.RequestException as e:
        # st.error(f"呼叫 API 時發生網路或請求錯誤: {e}") # 暫時先不在函式內用st元件
        print(f"DEBUG: 呼叫 API 時發生網路或請求錯誤: {e}") # 除錯時可用 print
        return None
    # ... (其他 except 區塊，為了簡潔，暫時省略 print/st.error，但函式應回傳 None) ...
    except json.JSONDecodeError:
        print(f"DEBUG: 無法解析 API 回傳的 JSON 資料。")
        return None
    except KeyError as e:
        print(f"DEBUG: 解析 API 回應時，找不到預期的欄位(Key): {e}")
        return None
    except Exception as e:
        print(f"DEBUG: 處理 API 回應時發生未知錯誤: {e}")
        return None



# --- 保留我們之前能成功運作的 Streamlit UI 測試程式碼 ---
st.title("Streamlit 測試頁面") 
st.write("哈囉！如果看到這行字，表示 Streamlit 基本運作正常！") 
st.balloons()

st.markdown("---") 
st.title("簡易食物營養查詢器 (API版)") 

# ↓↓↓ UI 邏輯修改開始 ↓↓↓
with st.form(key="food_search_form"): # 建立一個表單，並給它一個唯一的 key
    # 將文字輸入框放在表單內部
    food_name_input = st.text_input("請輸入想查詢的食物名稱 (建議英文):", "apple") 
    
    # 建立一個表單提交按鈕
    submitted = st.form_submit_button("查詢營養成分 (透過 API)") 

# 當表單被提交後 (無論是點擊按鈕還是按 Enter)，submitted 會變成 True
if submitted: # 檢查表單是否已提交
    if food_name_input: # 確保使用者有輸入內容
        st.write(f"正在透過 API 為 '{food_name_input}' 查詢營養資訊，請稍候...")
        
        nutrition_data = fetch_food_from_api(food_name_input) 
        
        if nutrition_data:
            st.success("API 查詢成功！") 
            retrieved_food_label = nutrition_data.get('食物名稱', food_name_input)
            st.subheader(f"'{retrieved_food_label}' 的營養成分 (通常為每100克):")
            
            display_data_dict = {
                "熱量 (KCAL)": nutrition_data.get("熱量", "N/A"),
                "蛋白質 (g)": nutrition_data.get("蛋白質", "N/A"),
                "碳水化合物 (g)": nutrition_data.get("碳水", "N/A"),
                "脂肪 (g)": nutrition_data.get("脂肪", "N/A")
            }
            df_to_display = pd.DataFrame(
                list(display_data_dict.items()), 
                columns=["營養素", "含量"]
            )
            st.dataframe(df_to_display)
        else:
            st.error(f"無法從 API 獲取 '{food_name_input}' 的營養資訊。請檢查食物名稱 (建議使用英文) 或稍後再試。")
    else:
        st.warning("請先輸入食物名稱再查詢。")

# st.markdown("---") # 之前的分隔線 (如果需要可以保留或調整位置)
# st.caption("這是一個使用 Edamam API 的簡易 Streamlit 應用程式。") # 之前的 caption
# ↑↑↑ UI 邏輯修改結束 ↑↑↑ 