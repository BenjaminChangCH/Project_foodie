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

# --- 主程式開始 ---
food_database = load_food_database() # 呼叫函式來載入資料

if not food_database:
    print("無法載入食物資料庫，程式結束。")
else:
    # 初始化這一餐的營養總計變數
    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    meal_items = [] # 用一個列表來記錄這一餐吃了什麼

    print("\n開始記錄一餐的食物。輸入食物名稱，每種預設為100克。")
    print("輸入完成後，請直接按 Enter 或輸入 '完成'。")

    while True: # 這是一個無限迴圈，需要用 break 來跳出
        user_food = input("請輸入食物名稱 (或按 Enter/輸入 '完成' 來結束): ").strip() # .strip() 去除頭尾空白

        if not user_food or user_food.lower() == '完成' or user_food.lower() == 'done':
            if not meal_items: # 如果什麼都沒輸入就結束
                print("您沒有輸入任何食物。")
            break # 跳出 while 迴圈

        if user_food in food_database:
            nutrition_info = food_database[user_food]
            
            # 累加營養素
            total_calories += nutrition_info['熱量']
            total_protein += nutrition_info['蛋白質']
            total_carbs += nutrition_info['碳水']
            total_fat += nutrition_info['脂肪']
            meal_items.append(user_food) # 將食物加入到餐點列表

            print(f"已加入 '{user_food}' (100克): 熱量 {nutrition_info['熱量']:.1f} 大卡, 蛋白質 {nutrition_info['蛋白質']:.1f} 克")
        else:
            print(f"抱歉，資料庫中沒有 '{user_food}' 的資訊，請嘗試其他食物。")
        
        print("-" * 20) # 分隔線

    # 迴圈結束後，顯示總計結果
    if meal_items: # 只有在 meal_items 不是空的時候才顯示總結
        print("\n--- 本餐營養總結 ---")
        print(f"您食用的品項: {', '.join(meal_items)}") # .join() 將列表元素用逗號連接成字串
        print(f"總熱量: {total_calories:.1f} 大卡")     # :.1f 表示印出小數點後一位
        print(f"總蛋白質: {total_protein:.1f} 克")
        print(f"總碳水化合物: {total_carbs:.1f} 克")
        print(f"總脂肪: {total_fat:.1f} 克")

    print("\n感謝使用多品項營養查詢程式！")