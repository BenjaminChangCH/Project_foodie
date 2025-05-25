# language_module.py

import streamlit as st # 主要用於可能的錯誤/警告提示

# 嘗試載入 google.cloud.language 套件
try:
    from google.cloud import language_v1 # 或者 language_v2，取決於您想用的版本特性，v1 通常穩定
    # from google.cloud.language_v1 import enums # 如果需要用到 enums
    # from google.cloud.language_v1 import types # 如果需要用到 types
except ImportError:
    if 'streamlit' in globals() and hasattr(st, 'error'):
        st.error("Python 套件 'google-cloud-language' 尚未安裝。 "
                 "請在終端機中執行 'pip3 install google-cloud-language' 指令來安裝。")
    else:
        print("錯誤：Python 套件 'google-cloud-language' 尚未安裝。 "
              "請在終端機中執行 'pip3 install google-cloud-language' 指令來安裝。")
    language_v1 = None # 設為 None 以便後續檢查

# Natural Language API 客戶端通常不需要像 Vision API 那樣複雜的憑證設定，
# 如果 GOOGLE_APPLICATION_CREDENTIALS 環境變數已為 Vision API 設定好，
# Natural Language API 客戶端通常也能自動使用它。
# 我們假設 vision_api.py 中的 setup_google_credentials() 已經被主程式呼叫過了。

def analyze_text_entities(list_of_text_strings):
    """
    使用 Google Cloud Natural Language API 分析一組文字字串中的實體。

    Args:
        list_of_text_strings (list): 一個包含多個文字字串的列表 (例如從 Vision API 獲取的標籤描述)。

    Returns:
        list: 一個包含分析結果的列表，每個結果是一個字典，包含：
              'original_text': 原始輸入的文字字串
              'entities': 一個該文字字串中辨識出的實體列表，每個實體包含：
                          'name': 實體的標準名稱
                          'type': 實體的類型 (例如 'CONSUMER_GOOD', 'OTHER', 'LOCATION' 等)
                          'salience': 實體的顯著性分數 (0.0 到 1.0)
                          'mid': 知識圖譜 ID (如果可用)
              返回 None 如果 API 客戶端未初始化或發生錯誤。
    """
    if language_v1 is None: # 如果 import language_v1 失敗
        print("錯誤 (language_module.py): Natural Language API 客戶端函式庫未能成功載入。")
        return None

    # 實例化 Natural Language API 客戶端
    # 它會自動使用 GOOGLE_APPLICATION_CREDENTIALS 環境變數 (假設已由 vision_api.setup_google_credentials 設定)
    try:
        client = language_v1.LanguageServiceClient()
    except Exception as e:
        print(f"錯誤 (language_module.py): 初始化 Natural Language API 客戶端失敗: {e}")
        if 'streamlit' in globals() and hasattr(st, 'error'):
            st.error(f"初始化 Natural Language API 客戶端失敗: {e}")
        return None

    results = []

    for text_content in list_of_text_strings:
        if not text_content or not isinstance(text_content, str):
            results.append({
                "original_text": text_content,
                "entities": [],
                "error": "Input text is invalid"
            })
            continue

        try:
            document = language_v1.types.Document(
                content=text_content,
                type_=language_v1.types.Document.Type.PLAIN_TEXT # type_ 有底線以避免與 Python 關鍵字衝突
            )

            # 設定額外功能，例如實體的情感分析 (可選)
            # features = language_v1.types.AnnotateTextRequest.Features(
            #     extract_entities=True,
            #     extract_entity_sentiment=False # 設為 True 如果需要情感分析
            # )
            # response = client.annotate_text(document=document, features=features)
            # entities = response.entities

            # 只進行實體分析
            response = client.analyze_entities(document=document)
            entities = response.entities

            current_text_entities = []
            for entity in entities:
                entity_data = {
                    "name": entity.name,
                    # entity.type 在 v1 中是一個枚舉值，需要轉換成字串名稱
                    "type": language_v1.types.Entity.Type(entity.type_).name,
                    "salience": round(entity.salience, 3),
                    "mid": entity.metadata.get("mid", None) # 獲取 MID (如果存在)
                    # "wikipedia_url": entity.metadata.get("wikipedia_url", None) # 獲取維基百科連結 (如果存在)
                }
                current_text_entities.append(entity_data)

            results.append({
                "original_text": text_content,
                "entities": current_text_entities
            })

        except Exception as e:
            print(f"錯誤 (language_module.py): 為文字 '{text_content}' 分析實體時發生錯誤: {e}")
            results.append({
                "original_text": text_content,
                "entities": [],
                "error": str(e)
            })

    return results

# # 範例用法 (可以在測試此模組時取消註解):
# if __name__ == '__main__':
#     # 需要確保 GOOGLE_APPLICATION_CREDENTIALS 環境變數已設定 (可以手動設定或透過 vision_api.setup_google_credentials)
#     # 或者，如果您在一個 Streamlit app 上下文中測試，且 secrets.toml 已設定：
#     # import vision_module # 假設您也需要它來設定憑證
#     # vision_module.vision_api.setup_google_credentials() # 確保憑證已設定

#     sample_texts = ["Granny Smith apple and banana", "delicious baked food", "chicken noodle soup recipe"]
#     analysis_results = analyze_text_entities(sample_texts)

#     if analysis_results:
#         for result in analysis_results:
#             print(f"--- 分析原文: {result['original_text']} ---")
#             if result.get("error"):
#                 print(f"  錯誤: {result['error']}")
#             for entity in result["entities"]:
#                 print(f"  實體名稱: {entity['name']}")
#                 print(f"    類型: {entity['type']}")
#                 print(f"    顯著性: {entity['salience']}")
#                 print(f"    MID: {entity['mid']}")
#             print("-" * 20)