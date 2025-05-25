# test_vertex_ai.py

import os
import json
import toml # 用於讀取 .streamlit/secrets.toml 檔案
from google.oauth2 import service_account # 用於從 JSON 內容創建憑證物件
import vertexai
from vertexai.generative_models import GenerativeModel # type: ignore

# secrets.toml 檔案的路徑 (假設 test_vertex_ai.py 與 .streamlit 資料夾在同一父目錄下)
# 如果您的 test_vertex_ai.py 放在 project_foodie 根目錄，這個路徑應該是正確的
SECRETS_FILE_PATH = ".streamlit/secrets.toml"

def load_secrets():
    """從 .streamlit/secrets.toml 載入秘密設定"""
    try:
        secrets = toml.load(SECRETS_FILE_PATH)
        return secrets
    except FileNotFoundError:
        print(f"錯誤：找不到秘密檔案 '{SECRETS_FILE_PATH}'。請確保檔案存在且路徑正確。")
        return None
    except Exception as e:
        print(f"錯誤：讀取秘密檔案 '{SECRETS_FILE_PATH}' 時發生錯誤: {e}")
        return None

def main():
    print("--- 開始 Vertex AI Gemini 模型測試 ---")

    secrets = load_secrets()
    if not secrets:
        print("無法載入 secrets.toml，測試終止。")
        return

    gcp_project_id = secrets.get("GCP_PROJECT_ID")
    gcp_vertex_location = secrets.get("GCP_VERTEX_LOCATION")
    gcp_credentials_json_content_str = secrets.get("GCP_CREDENTIALS_JSON_CONTENT")

    if not all([gcp_project_id, gcp_vertex_location, gcp_credentials_json_content_str]):
        missing_items = []
        if not gcp_project_id: missing_items.append("GCP_PROJECT_ID")
        if not gcp_vertex_location: missing_items.append("GCP_VERTEX_LOCATION")
        if not gcp_credentials_json_content_str: missing_items.append("GCP_CREDENTIALS_JSON_CONTENT")
        print(f"錯誤：secrets.toml 中缺少必要的設定: {', '.join(missing_items)}")
        return

    print(f"讀取到的 GCP_PROJECT_ID: '{gcp_project_id}'")
    print(f"讀取到的 GCP_VERTEX_LOCATION: '{gcp_vertex_location}'")
    # print(f"讀取到的 GCP_CREDENTIALS_JSON_CONTENT (前50字元): '{gcp_credentials_json_content_str[:50]}...'") # 不完整印出金鑰

    try:
        print("\n正在解析服務帳戶金鑰內容...")
        credentials_info = json.loads(gcp_credentials_json_content_str)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        print("服務帳戶金鑰內容解析成功，並已建立憑證物件。")

        print(f"\n正在初始化 Vertex AI (Project: '{gcp_project_id}', Location: '{gcp_vertex_location}')...")
        vertexai.init(project=gcp_project_id, location=gcp_vertex_location, credentials=credentials)
        print("Vertex AI 初始化成功。")

        model_name_to_test = "gemini-1.0-pro" # 我們用這個非常標準的模型名稱測試
        # model_name_to_test = "gemini-1.0-pro-002" # 也可以用這個
        # model_name_to_test = "gemini-1.5-flash-001" # 如果您想測試 flash 版本

        print(f"\n正在載入 Gemini 模型: '{model_name_to_test}'...")
        model = GenerativeModel(model_name_to_test)
        print(f"Gemini 模型 '{model_name_to_test}' 載入成功。")

        prompt = "你好，請用中文簡單介紹一下你自己。"
        print(f"\n準備向模型發送提示 (Prompt): \"{prompt}\"")

        print("\n正在生成內容 (呼叫 LLM)...")
        response = model.generate_content(prompt)
        print("LLM 呼叫完成。")

        if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            generated_text = response.candidates[0].text # .text 簡化了獲取
            print("\n--- LLM 成功回應 ---")
            print(generated_text)
            print("--------------------")
            print("\n測試成功！您的 GCP 設定、憑證、Vertex AI 初始化和 Gemini 模型呼叫都正常運作。")
        else:
            print("\n錯誤：LLM 回應的內容格式不符合預期，或者沒有有效的候選答案。")
            print(f"完整回應物件 (供除錯): {response}")

    except json.JSONDecodeError as e:
        print(f"\n錯誤：解析 'GCP_CREDENTIALS_JSON_CONTENT' 的 JSON 內容時失敗: {e}")
        print("請確認 secrets.toml 中的金鑰內容是完整且正確的 JSON 格式。")
    except Exception as e:
        print(f"\n在測試過程中發生未預期的錯誤: {e}")
        print("請檢查錯誤訊息，確認：")
        print("  1. Vertex AI API 是否已在您的 GCP 專案中完全啟用？")
        print("  2. 您的服務帳戶是否擁有 'Vertex AI User' 角色權限？")
        print("  3. 您的 GCP 專案是否已連結有效的計費帳戶？")
        print(f"  4. 模型 '{model_name_to_test}' 是否在區域 '{gcp_vertex_location}' 可用且您的專案有權限存取？")
        print(f"  5. secrets.toml 中的 GCP_PROJECT_ID ('{gcp_project_id}') 和 GCP_VERTEX_LOCATION ('{gcp_vertex_location}') 是否正確？")

    print("\n--- Vertex AI Gemini 模型測試結束 ---")

if __name__ == "__main__":
    main()