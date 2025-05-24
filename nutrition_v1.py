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

if not food_database: # 如果資料庫是空的 (可能因為讀檔失敗)
    print("無法載入食物資料庫，程式結束。")
else:
    user_food = input("請輸入你想查詢的食物名稱: ")

    if user_food in food_database:
        nutrition_info = food_database[user_food]
        print(f"\n--- {user_food} (每100克) ---")
        print(f"熱量: {nutrition_info['熱量']} 大卡")
        print(f"蛋白質: {nutrition_info['蛋白質']} 克")
        print(f"碳水化合物: {nutrition_info['碳水']} 克")
        print(f"脂肪: {nutrition_info['脂肪']} 克")
    else:
        print(f"\n抱歉，我們的資料庫中目前沒有 '{user_food}' 的營養資訊。")

    print("\n感謝使用簡易營養查詢程式！")