import csv
import requests  # 確保匯入 requests
import json      # 確保匯入 json

EDAMAM_APP_ID = "d3dffabe"  # 替換成您的 App ID
EDAMAM_APP_KEY = "84e836c03e271f07dafeb480112e9595" # 替換成您的 App Key

def load_food_database(filename="foods.csv"):
    """從 CSV 檔案載入食物資料到字典中。"""
    food_db = {}
    try:
        with open(filename, mode='r', encoding='utf-8') as csvfile:
            # csv.DictReader 會將每一行讀取為一個字典，鍵是第一行(欄位名稱)
            reader = csv.DictReader(csvfile)
            for row in reader:
                # row 會像這樣：{'FoodName': '蘋果', 'Calories': '52', ...}
                food_name = row['FoodName']
                # 注意：從 CSV 讀取的數字預設是字串，需要轉換成數字類型
                food_db[food_name] = {
                    "熱量": float(row['Calories']),    # float 可以處理小數
                    "蛋白質": float(row['Protein']),
                    "碳水": float(row['Carbs']),
                    "脂肪": float(row['Fat'])
                }
    except FileNotFoundError:
        print(f"錯誤：找不到資料庫檔案 {filename}")
    except Exception as e:
        print(f"讀取資料庫時發生錯誤：{e}")
    return food_db

def get_valid_grams_input(food_name_prompt):
    """
    提示使用者輸入特定食物的食用克數，並驗證輸入。
    會持續提示直到輸入一個有效的正浮點數為止，然後返回該浮點數。
    food_name_prompt: (字串) 要在提示訊息中顯示的食物名稱。
    """
    while True: # 開始一個無限迴圈，直到獲得有效輸入
        grams_input_str = input(f"請輸入 '{food_name_prompt}' 的食用克數 (例如: 150): ").strip()
        
        if not grams_input_str:  # 檢查是否為空輸入 (使用者直接按 Enter)
            print("未輸入克數，請重新輸入。")
            continue  # 跳過這次迴圈剩下的部分，直接開始下一次迴圈 (重新 input)
        
        try:
            # 嘗試將輸入的字串轉換為浮點數
            actual_grams = float(grams_input_str) 
            
            if actual_grams <= 0: # 檢查克數是否為正數
                print("克數必須大於0，請重新輸入。")
                continue # 如果小於等於0，重新開始迴圈
            
            # 如果程式執行到這裡，表示 actual_grams 是一個有效的正浮點數
            return actual_grams  # 返回有效克數，並結束函式及迴圈
            
        except ValueError:
            # 如果在 float() 轉換時發生 ValueError (例如輸入了文字)
            print("輸入的克數無效，請輸入純數字 (例如: 100 或 75.5)。")
            # except 區塊結束後，while 迴圈會自然地 continue 到下一次迭代

def fetch_food_from_api(food_name_to_search):
    """
    嘗試從 Edamam API 獲取指定食物的營養資訊。

    參數:
        food_name_to_search (str): 要查詢的食物名稱。

    回傳:
        dict: 如果成功找到食物並解析，則回傳包含 "熱量", "蛋白質", "碳水", "脂肪" 鍵的字典。
              其格式應與 food_database 中的項目一致。
        None: 如果發生任何錯誤 (網路、API金鑰、找不到食物、解析錯誤等)。
    """
    base_url = "https://api.edamam.com"
    parser_endpoint = "/api/food-database/v2/parser"

    # 使用函式參數 food_name_to_search 來查詢，而不是固定的 "apple"
    request_url = f"{base_url}{parser_endpoint}?ingr={food_name_to_search}&app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}"
    # 如果需要，可以加上 &nutrition-type=logging

    print(f"正在從 API 查詢 '{food_name_to_search}'...") # 可以保留一個簡單的查詢提示

    headers_to_send = {}
    # 如果您的 Edamam 設定需要 User ID Header (取消下一行的註解並確保 USER_ID_FOR_HEADER 已定義)
    # headers_to_send["Edamam-Account-User"] = USER_ID_FOR_HEADER

    try:
        if headers_to_send: # 只有當 headers_to_send 不是空字典時才傳遞 headers 參數
            response = requests.get(request_url, headers=headers_to_send)
        else:
            response = requests.get(request_url)

        # 檢查是否有 HTTP 錯誤 (例如 401, 403, 404, 500 等)
        # response.raise_for_status() 會在發生 HTTP 錯誤時拋出異常
        if response.status_code != 200:
            print(f"API 錯誤：狀態碼 {response.status_code} - {response.text}")
            return None

        data = response.json()

        # 檢查 API 是否真的找到了食物並且有 "parsed" 列表
        if "parsed" in data and data["parsed"]:
            # 我們取第一個解析到的食物結果
            api_food_data = data["parsed"][0]["food"] 
            
            # 從 API 回應中提取我們需要的營養素
            # Edamam API 回傳的營養素鍵名可能與我們的不同，例如 ENERC_KCAL, PROCNT, CHOCDF, FAT
            nutrients_from_api = api_food_data.get("nutrients", {}) # .get() 更安全，如果 "nutrients" 不存在則回傳空字典

            # 將提取到的營養素格式化成我們程式內部統一的字典結構
            formatted_nutrition_data = {
                "熱量": nutrients_from_api.get("ENERC_KCAL", 0.0), # 熱量
                "蛋白質": nutrients_from_api.get("PROCNT", 0.0),  # 蛋白質
                "碳水": nutrients_from_api.get("CHOCDF", 0.0),  # 碳水化合物
                "脂肪": nutrients_from_api.get("FAT", 0.0)     # 脂肪
            }
            return formatted_nutrition_data
        else:
            # API 成功回應，但沒有解析到任何食物 (例如，輸入了一個不存在的食物名稱)
            print(f"API 未能解析食物: '{food_name_to_search}'")
            return None

    except requests.exceptions.RequestException as e:
        print(f"呼叫 API 時發生網路或請求錯誤: {e}")
        return None
    except json.JSONDecodeError:
        print("無法解析 API 回傳的 JSON 資料。")
        return None
    except KeyError as e:
        print(f"解析 API 回應時，找不到預期的欄位(Key): {e}")
        return None
    except Exception as e: # 捕捉其他所有未預期錯誤
        print(f"處理 API 回應時發生未知錯誤: {e}")
        return None

# --- 主程式開始 ---
food_database = load_food_database() # 載入本地 CSV 資料

# (EDAMAM_APP_ID, EDAMAM_APP_KEY, USER_ID_FOR_HEADER 應該定義在檔案頂部)

if not food_database:
    # 即使本地資料庫載入失敗，我們仍然可以嘗試使用 API，所以不直接結束程式
    print("警告：本地食物資料庫 food.csv 載入失敗或為空，將僅依賴 API 查詢。")
    food_database = {} # 確保 food_database 是一個空字典，而不是 None

total_calories = 0.0
total_protein = 0.0
total_carbs = 0.0
total_fat = 0.0
meal_items_details = []

print("\n歡迎使用進階營養查詢程式！")
# ... (其他歡迎訊息) ...

while True:
    user_food = input("\n請輸入食物名稱 (或按 Enter/輸入 '完成' 來結束): ").strip()

    if not user_food or user_food.lower() == '完成' or user_food.lower() == 'done':
        if not meal_items_details:
            print("您沒有記錄任何食物。")
        break

    nutrition_info_per_100g = None # 先預設為 None

    if user_food in food_database: # 先檢查本地 CSV
        nutrition_info_per_100g = food_database[user_food]
        print(f"'{user_food}' 的資訊從本地資料庫載入。")
    else:
        # 如果本地找不到，嘗試從 API 獲取
        print(f"本地資料庫找不到 '{user_food}'，嘗試從網路 API 查詢...")
        api_nutrition_data = fetch_food_from_api(user_food) # 呼叫新函式
        
        if api_nutrition_data:
            nutrition_info_per_100g = api_nutrition_data
            print(f"'{user_food}' 的資訊成功從網路 API 獲取！")
            # (進階：未來可以考慮將 api_nutrition_data 更新回 food_database 或 foods.csv)
        else:
            # API 也找不到，或查詢失敗
            print(f"抱歉，'{user_food}' 在本地資料庫和網路 API 中都找不到相關資訊。")

    # 在獲取到 nutrition_info_per_100g 之後 (無論是從本地還是 API)
    if nutrition_info_per_100g: # 只有當成功獲取到營養資訊時，才進行後續操作
        actual_grams = get_valid_grams_input(user_food) # 呼叫克數輸入函式
        
        # 計算實際攝取營養
        actual_calories = (nutrition_info_per_100g['熱量'] / 100) * actual_grams
        actual_protein = (nutrition_info_per_100g['蛋白質'] / 100) * actual_grams
        actual_carbs = (nutrition_info_per_100g['碳水'] / 100) * actual_grams
        actual_fat = (nutrition_info_per_100g['脂肪'] / 100) * actual_grams
        
        # 累加營養素
        total_calories += actual_calories
        total_protein += actual_protein
        total_carbs += actual_carbs
        total_fat += actual_fat
        
        meal_items_details.append(f"{user_food} ({actual_grams:.1f}克)")
        print(f"已加入: '{user_food}' ({actual_grams:.1f}克) - 熱量 {actual_calories:.1f} 大卡, 蛋白質 {actual_protein:.1f} 克")
    # else: 如果 nutrition_info_per_100g 仍然是 None，則不進行任何操作，上面已經印過找不到了
    
# --- while 迴圈結束後，顯示總計結果 ---
if meal_items_details:
    print("\n========== 本餐營養總結 ==========")
    # ... (後續的總結打印邏輯和之前一樣) ...
    print(f"您記錄的品項: {', '.join(meal_items_details)}")
    print(f"總熱量       : {total_calories:.1f} 大卡")
    print(f"總蛋白質     : {total_protein:.1f} 克")
    print(f"總碳水化合物 : {total_carbs:.1f} 克")
    print(f"總脂肪       : {total_fat:.1f} 克")
    print("===================================")

print("\n感謝您的使用！")
