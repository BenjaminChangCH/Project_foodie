# edamam_module.py

import streamlit as st
import requests
import json

_edamam_credentials_loaded = False
EDAMAM_APP_ID = None
EDAMAM_APP_KEY = None

# edamam_module.py
# ... (檔案開頭的 import 和憑證變數) ...

def load_edamam_credentials(): # 這個函式應該不變
    global _edamam_credentials_loaded, EDAMAM_APP_ID, EDAMAM_APP_KEY, \
           NUTRITION_ANALYSIS_APP_ID, NUTRITION_ANALYSIS_APP_KEY
    # ... (函式內容不變) ...
    if _edamam_credentials_loaded:
        return True

    app_id_from_secrets = st.secrets.get("EDAMAM_APP_ID")
    app_key_from_secrets = st.secrets.get("EDAMAM_APP_KEY")

    if app_id_from_secrets and app_key_from_secrets:
        EDAMAM_APP_ID = app_id_from_secrets
        EDAMAM_APP_KEY = app_key_from_secrets
        NUTRITION_ANALYSIS_APP_ID = app_id_from_secrets 
        NUTRITION_ANALYSIS_APP_KEY = app_key_from_secrets
        _edamam_credentials_loaded = True
        return True
    else:
        _edamam_credentials_loaded = False
        return False

def get_food_data_with_measures(food_name_to_query): # <<< 確認函式名稱是這個！
    """
    (原 get_food_nutrition_data 函式，更名以明確其主要獲取的是食物資料和份量單位)
    使用 Edamam Food Database API (/parser) 根據食物名稱查詢其基本資料、
    預設營養資訊 (通常是每100g) 以及可用的份量單位 (measures)。
    """
    global _edamam_credentials_loaded, EDAMAM_APP_ID, EDAMAM_APP_KEY # 確保引用了正確的全局變數

    if not _edamam_credentials_loaded: # 檢查憑證
        if not load_edamam_credentials(): # 如果未載入，嘗試載入
            print("錯誤 (edamam_module.py): get_food_data_with_measures - Edamam 憑證載入失敗。")
            return None # 載入失敗則返回 None

    # 再次檢查 food_name_to_query 和憑證是否有效
    if not food_name_to_query or not EDAMAM_APP_ID or not EDAMAM_APP_KEY:
        print(f"錯誤 (edamam_module.py): get_food_data_with_measures - 缺少查詢參數 food_name ('{food_name_to_query}') 或 Edamam API 憑證。")
        return None

    base_url = "https://api.edamam.com/api/food-database/v2/parser"
    params = {
        "ingr": food_name_to_query,
        "app_id": EDAMAM_APP_ID,
        "app_key": EDAMAM_APP_KEY,
        "nutrition-type": "logging"
    }

    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        food_item_data = None
        if data.get("parsed") and len(data["parsed"]) > 0 and data["parsed"][0].get("food"):
            food_item_data = data["parsed"][0]["food"]
        elif data.get("hints") and len(data["hints"]) > 0 and data["hints"][0].get("food"):
            food_item_data = data["hints"][0]["food"]

        if food_item_data:
            nutrients_per_100g = food_item_data.get("nutrients", {})
            measures_data = []
            if "measures" in food_item_data and isinstance(food_item_data["measures"], list):
                for m_item in food_item_data["measures"]:
                    if "uri" in m_item and "label" in m_item and "weight" in m_item:
                        measures_data.append({
                            "uri": m_item["uri"], 
                            "label": m_item["label"],
                            "weight": round(m_item["weight"], 2)
                        })

            # 確保 "100 grams" 選項存在
            found_100g = False
            for m in measures_data:
                if m['label'].lower() == 'gram' and m['weight'] == 1.0: # Edamam 對 "gram" measure 的 weight 是 1
                    # 不要直接修改這個，我們額外加一個 "100 grams"
                    pass
                if m['label'] == '100 grams':
                    found_100g = True
                    break
            if not found_100g:
                 measures_data.insert(0, { # 將 "100 grams" 放在列表開頭
                    "uri": "http://www.edamam.com/ontologies/edamam.owl#Measure_gram", 
                    "label": "100 grams", 
                    "weight": 100.0
                })


            processed_data = {
                "food_id": food_item_data.get("foodId"), 
                "label": food_item_data.get("label", food_name_to_query),
                "nutrients_per_100g": { 
                    "calories": nutrients_per_100g.get("ENERC_KCAL"),
                    "protein": nutrients_per_100g.get("PROCNT"),
                    "fat": nutrients_per_100g.get("FAT"),
                    "carbs": nutrients_per_100g.get("CHOCDF"),
                    "fiber": nutrients_per_100g.get("FIBTG"),
                },
                "image_url": food_item_data.get("image"),
                "measures": measures_data
            }

            if processed_data["nutrients_per_100g"]:
                processed_data["nutrients_per_100g"] = {
                    k: v for k, v in processed_data["nutrients_per_100g"].items() if v is not None
                }
            return {k: v for k, v in processed_data.items() if v is not None or k == "nutrients_per_100g"}
        else:
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f"錯誤 (edamam_module.py): Edamam Food DB API HTTP 錯誤: {http_err} - 回應內容: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"錯誤 (edamam_module.py): Edamam Food DB API 請求失敗: {req_err}")
        return None
    except json.JSONDecodeError:
        print("錯誤 (edamam_module.py): 無法解析來自 Edamam Food DB API 的回應。")
        return None
    except Exception as e:
        print(f"錯誤 (edamam_module.py): 查詢 Edamam Food DB API 時發生未預期錯誤: {e}")
        return None

# ... (analyze_nutrition_for_specific_amount 函式保持不變) ...
def analyze_nutrition_for_specific_amount(food_name_or_id, quantity, unit_label, measure_uri=None):
    # ... (函式內容不變) ...
    global _edamam_credentials_loaded, NUTRITION_ANALYSIS_APP_ID, NUTRITION_ANALYSIS_APP_KEY

    if not _edamam_credentials_loaded: 
        if not load_edamam_credentials():
            print("錯誤 (edamam_module.py): analyze_nutrition_for_specific_amount - Edamam 憑證載入失敗。")
            return None

    if not food_name_or_id or quantity is None or quantity <= 0 or not unit_label or \
       not NUTRITION_ANALYSIS_APP_ID or not NUTRITION_ANALYSIS_APP_KEY:
        print("錯誤 (edamam_module.py): analyze_nutrition_for_specific_amount - 缺少必要的查詢參數或憑證。")
        return None

    analysis_base_url = f"https://api.edamam.com/api/nutrition-details?app_id={NUTRITION_ANALYSIS_APP_ID}&app_key={NUTRITION_ANALYSIS_APP_KEY}"

    ingredient_line = f"{quantity} {unit_label} {food_name_or_id}"
    if unit_label.lower() in ["gram", "grams", "g"]:
        ingredient_line = f"{quantity}g {food_name_or_id}"
    elif unit_label.lower() in ["kilogram", "kilograms", "kg"]:
        ingredient_line = f"{quantity}kg {food_name_or_id}"

    payload = { "ingr": [ingredient_line] }

    try:
        response = requests.post(analysis_base_url, json=payload, timeout=15)
        response.raise_for_status()
        nutrition_details = response.json()

        if nutrition_details and "calories" in nutrition_details and "totalNutrients" in nutrition_details:
            nutrients_parsed = {}
            for key, nutrient_data in nutrition_details.get("totalNutrients", {}).items():
                if isinstance(nutrient_data, dict) and "label" in nutrient_data and "quantity" in nutrient_data and "unit" in nutrient_data:
                    nutrients_parsed[nutrient_data["label"]] = {
                        "quantity": round(nutrient_data["quantity"], 2),
                        "unit": nutrient_data["unit"]
                    }

            return {
                "calories": nutrition_details.get("calories"),
                "total_weight_grams": nutrition_details.get("totalWeight"), 
                "diet_labels": nutrition_details.get("dietLabels", []),
                "health_labels": nutrition_details.get("healthLabels", []),
                "cautions": nutrition_details.get("cautions", []),
                "total_nutrients_by_label": nutrients_parsed, 
                "raw_total_nutrients": nutrition_details.get("totalNutrients", {}), 
                "raw_total_daily": nutrition_details.get("totalDaily", {}) 
            }
        elif "error" in nutrition_details:
            print(f"錯誤 (edamam_module.py): Nutrition Analysis API 回應錯誤: {nutrition_details.get('error')}")
            return None
        else:
            print("錯誤 (edamam_module.py): Nutrition Analysis API 回應格式不如預期。")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"錯誤 (edamam_module.py): Edamam Nutrition Analysis API HTTP 錯誤: {http_err} - 回應內容: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"錯誤 (edamam_module.py): Edamam Nutrition Analysis API 請求失敗: {req_err}")
        return None
    except json.JSONDecodeError:
        print("錯誤 (edamam_module.py): 無法解析來自 Edamam Nutrition Analysis API 的回應。")
        return None
    except Exception as e:
        print(f"錯誤 (edamam_module.py): 呼叫 Edamam Nutrition Analysis API 時發生未預期錯誤: {e}")
        return None