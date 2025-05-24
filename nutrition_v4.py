# (這裡接續上面的 load_food_database 函式)
import csv  # 匯入 Python 內建的 csv 模組，方便處理 CSV 檔案

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


# --- 主程式開始 ---
food_database = load_food_database()

if not food_database:
    print("無法載入食物資料庫，程式結束。")
else:
    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    meal_items_details = [] # 記錄食物名稱和克數

    print("\n開始記錄一餐的食物。")
    print("輸入完成後，請直接按 Enter 或輸入 '完成'。")

    while True:
        user_food = input("\n請輸入食物名稱 (或按 Enter/輸入 '完成' 來結束): ").strip()

        if not user_food or user_food.lower() == '完成' or user_food.lower() == 'done':
            if not meal_items_details:
                print("您沒有輸入任何食物。")
            break

        if user_food in food_database:
            nutrition_info_per_100g = food_database[user_food] # 這是每100克的營養
            actual_grams = get_valid_grams_input(user_food) #把獲取克數的邏輯抽出來成為一個函式
            
            # 計算實際攝取營養 (按比例)
            # (資料庫營養 / 100) * 實際克數
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

            print(f"已加入 '{user_food}' ({actual_grams:.1f}克): 熱量 {actual_calories:.1f} 大卡, 蛋白質 {actual_protein:.1f} 克")
        else:
            print(f"抱歉，資料庫中沒有 '{user_food}' 的資訊，請嘗試其他食物。")
        
    # 迴圈結束後，顯示總計結果
    if meal_items_details:
        print("\n--- 本餐營養總結 ---")
        print(f"您食用的品項: {', '.join(meal_items_details)}")
        print(f"總熱量: {total_calories:.1f} 大卡")
        print(f"總蛋白質: {total_protein:.1f} 克")
        print(f"總碳水化合物: {total_carbs:.1f} 克")
        print(f"總脂肪: {total_fat:.1f} 克")

    print("\n感謝使用進階營養查詢程式！")