# utils/vision_api.py
# Google Cloud Vision API統合

from google.cloud import vision
from typing import Optional


def identify_fish_vision(image_bytes: bytes) -> Optional[str]:
    """
    Google Cloud Vision APIを使用して画像から魚を識別
    
    Args:
        image_bytes: 画像データ
        
    Returns:
        魚の名前 (英語) または None
    """
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        
        # ラベル検出
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        # Web検出（より正確な識別のため）
        web_response = client.web_detection(image=image)
        web_entities = web_response.web_detection.web_entities
        
        # 魚関連のキーワード
        fish_keywords = [
            'fish', 'mackerel', 'tuna', 'salmon', 'sardine',
            'bass', 'bream', 'flounder', 'cod', 'trout',
            'さば', 'まぐろ', 'さけ', 'いわし', 'あじ'
        ]
        
        # ラベルをチェック
        for label in labels:
            desc = label.description.lower()
            if any(keyword in desc for keyword in fish_keywords):
                return label.description
        
        # Webエンティティをチェック
        for entity in web_entities:
            if entity.description:
                desc = entity.description.lower()
                if any(keyword in desc for keyword in fish_keywords):
                    return entity.description
        
        return None
        
    except Exception as e:
        print(f"❌ Vision APIエラー: {e}")
        return None