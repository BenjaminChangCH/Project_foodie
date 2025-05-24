import requests  # 匯入我們剛剛安裝的 requests 工具包
import json      # 匯入 Python 內建的 json 工具包，用來處理 JSON 格式資料

# 我們來試用一個會隨機回傳笑話的公開 API (不需要 API Key)
api_url = "https://official-joke-api.appspot.com/random_joke"

print(f"正在嘗試連線到 API: {api_url}")

try:
    # 使用 requests 發送一個 GET 請求到指定的 API 網址
    response = requests.get(api_url)

    # 檢查回應的狀態碼 (Status Code)
    # 狀態碼 200 通常表示請求成功
    print(f"API 回應狀態碼: {response.status_code}")

    if response.status_code == 200:
        # 印出 API 回傳的原始文字內容 (通常是 JSON 字串)
        print("\nAPI 回傳的原始資料 (JSON 字串):")
        print(response.text)

        # 嘗試將 JSON 字串轉換成 Python 的字典或列表
        joke_data = response.json() 

        print("\n成功解析 JSON 資料！")
        print(f"笑話類型: {joke_data.get('type', '未知類型')}") # .get() 可以避免 KeyError
        print(f"笑話設定: {joke_data.get('setup', 'N/A')}")
        print(f"笑話結尾: {joke_data.get('punchline', 'N/A')}")
    else:
        print(f"API 請求失敗，狀態碼: {response.status_code}")
        print(f"錯誤訊息內容: {response.text}")

except requests.exceptions.RequestException as e:
    # 處理網路連線相關的錯誤 (例如：無法連線到伺服器、DNS 查詢失敗等)
    print(f"連線 API 時發生錯誤: {e}")
except json.JSONDecodeError:
    print("無法解析 API 回傳的 JSON 資料，格式可能不正確。")
except KeyError as e:
    print(f"解析 JSON 資料時，找不到預期的欄位: {e}")
except Exception as e:
    # 捕捉其他未預期的錯誤
    print(f"發生未預期錯誤: {e}")
