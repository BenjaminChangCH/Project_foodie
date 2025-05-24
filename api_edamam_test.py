import requests  # 匯入 requests 工具包
import json      # 匯入 json 工具包 (雖然 response.json() 會自動處理，但 import 著以備不時之需)

# ==============================================================================
# 重要：請將下面的 YOUR_APP_ID 和 YOUR_APP_KEY 替換成您真實的 Edamam App ID 和 App Key
# 這些是您的個人憑證，請妥善保管，不要直接分享包含真實金鑰的程式碼到公開場合。
EDAMAM_APP_ID = "d3dffabe"  # 替換成您的 App ID
EDAMAM_APP_KEY = "84e836c03e271f07dafeb480112e9595" # 替換成您的 App Key
# ==============================================================================

# API 的基礎網址和端點路徑
BASE_URL = "https://api.edamam.com"
PARSER_ENDPOINT = "/api/food-database/v2/parser"

# 我們要查詢的食物
ingredient_to_search = "apple" # 您可以改成其他英文食物名稱，例如 "banana", "chicken breast"

# 組合完整的請求網址 (URL)
# 我們會將參數直接加在網址後面，用 f-string 來組合
# Edamam API 參數: ingr, app_id, app_key
request_url = f"{BASE_URL}{PARSER_ENDPOINT}?ingr={ingredient_to_search}&app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}"
# 您也可以加上 &nutrition-type=logging 試試看

print(f"準備發送請求到: {request_url}\n")

try:
    # 發送 GET 請求
    response = requests.get(request_url)

    # 印出 API 回應狀態碼
    print(f"API 回應狀態碼: {response.status_code}")

    # 檢查請求是否成功 (狀態碼 200 表示成功)
    if response.status_code == 200:
        print("請求成功！")
        
        # 嘗試將回應內容解析為 JSON 格式 (Python 字典/列表)
        # response.json() 會自動幫我們做這件事
        data = response.json()
        
        print("\nAPI 回傳的 JSON 資料 (已解析為 Python 物件):")
        # 為了方便閱讀，我們用 json.dumps 格式化輸出，設定縮排
        print(json.dumps(data, indent=4, ensure_ascii=False)) 
        # ensure_ascii=False 讓中文字符能正確顯示 (如果 API 回傳的資料包含中文)

        # 嘗試從回傳的資料中提取一些資訊 (這部分會根據 API 回傳的實際 JSON 結構而定)
        # 例如，Edamam parser 的回應通常包含 "parsed", "hints" 等欄位
        if "parsed" in data and data["parsed"]:
            first_parsed_food = data["parsed"][0]["food"]
            food_label = first_parsed_food.get("label", "未知標籤")
            food_id = first_parsed_food.get("foodId", "未知ID")
            print(f"\n解析到的第一個食物項目:")
            print(f"  標籤 (Label): {food_label}")
            print(f"  食物ID (Food ID): {food_id}")
            if "nutrients" in first_parsed_food:
                 calories = first_parsed_food["nutrients"].get("ENERC_KCAL", "N/A")
                 print(f"  熱量 (KCAL per 100g): {calories}")

    else:
        print(f"API 請求失敗，狀態碼: {response.status_code}")
        print("回應內容:")
        print(response.text) # 印出原始的錯誤回應內容

except requests.exceptions.RequestException as e:
    print(f"連線 API 時發生網路或請求錯誤: {e}")
except json.JSONDecodeError:
    print("無法解析 API 回傳的 JSON 資料，格式可能不正確。")
except KeyError as e:
    print(f"解析 JSON 資料時，找不到預期的欄位(Key): {e}")
except Exception as e:
    print(f"發生未預期的錯誤: {e}")