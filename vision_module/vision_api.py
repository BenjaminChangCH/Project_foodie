# vision_module/vision_api.py

import streamlit as st
import os
import tempfile
import json

# 嘗試載入 google.cloud.vision 套件
# 這有助於在套件未安裝時提供明確的錯誤訊息
try:
    from google.cloud import vision
except ImportError:
    # 如果在 Streamlit 環境中執行，st.error 會在 APP UI 上顯示錯誤
    # 如果這個模組在非 Streamlit 環境被載入，這個 UI 錯誤不會出現
    if 'streamlit' in globals() and hasattr(st, 'error'): # 檢查 st 是否可用
        st.error("Python 套件 'google-cloud-vision' 尚未安裝。 "
                 "請在您的終端機中執行 'pip3 install google-cloud-vision' 指令來安裝。")
    else: # Fallback to print if st is not available (e.g. module imported in a non-Streamlit context)
        print("錯誤：Python 套件 'google-cloud-vision' 尚未安裝。 "
              "請在您的終端機中執行 'pip3 install google-cloud-vision' 指令來安裝。")
    vision = None # 將 vision 設為 None，以便後續檢查 import 是否失敗

_google_credentials_set = False # 模組級別的變數，用來追蹤憑證是否已經設定成功

def setup_google_credentials():
    """
    設定 Google Cloud 憑證。
    此函式會優先從 Streamlit Secrets (st.secrets) 讀取 GCP JSON 金鑰的內容。
    這種方法適用於 Streamlit Community Cloud 部署，也適用於在本機使用 .streamlit/secrets.toml 檔案的情況。
    """
    global _google_credentials_set # 宣告我們要修改的是模組級別的 _google_credentials_set
    if _google_credentials_set: # 如果之前已經成功設定過，就直接返回，不再重複設定
        # print("DEBUG (vision_api.py): Google 憑證已設定，跳過重複設定。") # 除錯時可取消註解
        return

    try:
        # "GCP_CREDENTIALS_JSON_CONTENT" 是我們約定在 st.secrets
        # (無論是雲端的 Secrets 設定，還是本地的 .streamlit/secrets.toml 檔案) 中使用的金鑰名稱
        gcp_creds_content_from_secrets = st.secrets.get("GCP_CREDENTIALS_JSON_CONTENT")

        if gcp_creds_content_from_secrets: # 如果成功從 st.secrets 讀取到內容
            # print("DEBUG (vision_api.py): 在 st.secrets 中找到 GCP_CREDENTIALS_JSON_CONTENT。") # 除錯時可取消註解
            # 驗證讀取到的內容是否為合法的 JSON 格式
            try:
                json.loads(gcp_creds_content_from_secrets) # 嘗試解析 JSON
            except json.JSONDecodeError as e:
                # 如果 JSON 格式錯誤，則顯示錯誤訊息
                error_message = ("錯誤：在 Streamlit Secrets 中的 'GCP_CREDENTIALS_JSON_CONTENT' "
                                 f"不是一個有效的 JSON 格式。請檢查其內容。詳細錯誤: {e}")
                if 'streamlit' in globals() and hasattr(st, 'error'): st.error(error_message, icon="🚨")
                else: print(error_message)
                _google_credentials_set = False # 標記為設定失敗
                return # 結束函式

            # 將 JSON 字串內容寫入一個暫存檔案中
            # delete=False 確保檔案在 with 區塊結束後不會馬上被刪除，
            # 因為 os.environ 需要一個持續有效的檔案路徑，直到 vision.ImageAnnotatorClient() 被實例化。
            # Streamlit Cloud 環境會在應用程式會話結束時清理這些暫存檔案。
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_creds_file:
                temp_creds_file.write(gcp_creds_content_from_secrets)
                temp_file_path = temp_creds_file.name # 取得這個暫存檔案的完整路徑

            # 設定 GOOGLE_APPLICATION_CREDENTIALS 環境變數，使其指向這個暫存檔案的路徑
            # Google Cloud 的 Python 客戶端函式庫會自動尋找這個環境變數
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path
            _google_credentials_set = True # 標記為設定成功
            # print(f"DEBUG (vision_api.py): Google 憑證已透過 st.secrets 設定到暫存檔案: {temp_file_path}") # 除錯時可取消註解
            return # 設定成功，結束函式

        # 如果 st.secrets 中沒有，則檢查 GOOGLE_APPLICATION_CREDENTIALS 環境變數是否已經由其他方式設定
        # (例如，使用者在本機終端機中為了其他測試，直接設定了指向 .json 實體檔案的路徑)
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # print(f"DEBUG (vision_api.py): 在 os.environ 中找到 GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}") # 除錯用
            if os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")): # 檢查該路徑的檔案是否存在
                _google_credentials_set = True # 假設它是一個有效的憑證檔案路徑
                # print("DEBUG (vision_api.py): 現有的 GOOGLE_APPLICATION_CREDENTIALS 環境變數路徑有效。") # 除錯用
                return # 設定成功，結束函式
            else:
                # 環境變數設定了，但指向的檔案不存在
                warning_message = (f"警告：環境變數 GOOGLE_APPLICATION_CREDENTIALS "
                                 f"指向一個不存在的檔案: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
                if 'streamlit' in globals() and hasattr(st, 'warning'): st.warning(warning_message, icon="⚠️")
                else: print(warning_message)
                _google_credentials_set = False # 標記為設定失敗
                return # 結束函式

        # 如果 st.secrets 和環境變數兩種主要方式都找不到有效的憑證
        if not _google_credentials_set:
            # print("DEBUG (vision_api.py): 未能透過任何主要方法找到憑證。") # 除錯用
            # 這個訊息主要會在 Streamlit app 啟動時，如果 setup_google_credentials 被調用但失敗時顯示
            info_message = ("提示：Google Cloud 憑證尚未透過 st.secrets ('GCP_CREDENTIALS_JSON_CONTENT') "
                            "或有效的 'GOOGLE_APPLICATION_CREDENTIALS' 環境變數進行配置。"
                            "圖片分析相關功能可能無法正常運作。")
            if 'streamlit' in globals() and hasattr(st, 'info'): st.info(info_message, icon="ℹ️")
            else: print(info_message)

    except Exception as e: # 捕獲其他所有未預期的錯誤
        error_message = f"設定 Google Cloud 憑證時發生未預期的錯誤: {e}"
        # print(f"DEBUG (vision_api.py): 在 setup_google_credentials 中發生例外: {e}") # 除錯用
        if 'streamlit' in globals() and hasattr(st, 'error'): st.error(error_message, icon="🔥")
        else: print(error_message)
        _google_credentials_set = False # 標記為設定失敗


def analyze_image_labels(image_content_bytes):
    """
    使用 Google Cloud Vision API 的標籤偵測 (Label Detection) 功能來分析傳入的圖片內容。
    Args:
        image_content_bytes (bytes): 圖片的原始位元組內容。
    Returns:
        list: 一個包含 (標籤描述, 信賴度分數) 元組的列表。
              如果在設定憑證失敗、Vision API 套件未載入，或 API 呼叫過程中發生錯誤，則返回 None。
    """
    global _google_credentials_set # 確保我們能存取模組級別的 _google_credentials_set 變數

    if vision is None: # 檢查 from google.cloud import vision 是否成功
        error_message = "錯誤：Google Cloud Vision API 的 Python 客戶端函式庫未能成功載入。無法分析圖片。"
        if 'streamlit' in globals() and hasattr(st, 'error'): st.error(error_message)
        else: print(error_message)
        return None

    if not _google_credentials_set: # 如果憑證尚未設定成功
        # print("DEBUG (vision_api.py): 呼叫 analyze_image_labels 時憑證未設定，嘗試再次設定。") # 除錯用
        # 嘗試再次設定憑證。這是一個備援措施，理想情況下 setup_google_credentials() 應在 app 啟動時被呼叫一次。
        setup_google_credentials() 
        if not _google_credentials_set: # 如果再次設定仍然失敗
            warning_message = "警告：Google Cloud 憑證未能正確設定。圖片分析無法繼續。"
            # print("DEBUG (vision_api.py): 從 analyze_image_labels 再次設定憑證失敗。") # 除錯用
            if 'streamlit' in globals() and hasattr(st, 'warning'): st.warning(warning_message, icon="⚠️")
            else: print(warning_message)
            return None # 返回 None，表示無法分析

    # print("DEBUG (vision_api.py): 憑證已設定，準備呼叫 Vision API。") # 除錯用
    try:
        # 實例化 Vision API 的客戶端。它會自動使用 GOOGLE_APPLICATION_CREDENTIALS 環境變數。
        client = vision.ImageAnnotatorClient()
        # 將圖片的位元組內容封裝成 Vision API 可辨識的 Image 物件。
        image = vision.Image(content=image_content_bytes)

        # 呼叫 label_detection 方法進行標籤偵測。
        response = client.label_detection(image=image)

        # 檢查 API 的回應中是否有錯誤訊息。
        if response.error.message:
            error_message = f"Vision API 錯誤: {response.error.message}"
            # print(f"DEBUG (vision_api.py): Vision API 回應錯誤: {response.error.message}") # 除錯用
            if 'streamlit' in globals() and hasattr(st, 'error'): st.error(error_message)
            else: print(error_message)
            return None # 返回 None 表示 API 呼叫有誤

        # 如果沒有錯誤，從回應中提取標籤資訊。
        extracted_labels = []
        if response.label_annotations: # label_annotations 是一個列表，包含所有辨識出的標籤
            for label in response.label_annotations:
                # label.description 是標籤的文字描述 (例如 "apple", "fruit")
                # label.score 是該標籤的信賴度分數 (0.0 到 1.0 之間)
                extracted_labels.append((label.description, label.score))
        # print(f"DEBUG (vision_api.py): 成功提取的標籤: {extracted_labels}") # 除錯用
        return extracted_labels # 返回提取的標籤列表

    except Exception as e: # 捕獲在呼叫 Vision API 過程中可能發生的其他 Python 錯誤
        error_message = f"呼叫 Vision API 時發生未預期的 Python 錯誤: {e}"
        # print(f"DEBUG (vision_api.py): 呼叫 Vision API 時發生例外: {e}") # 除錯用
        if 'streamlit' in globals() and hasattr(st, 'error'): st.error(error_message, icon="🔥")
        else: print(error_message)
        return None # 返回 None 表示發生錯誤
