# utils/vision_api.py

from typing import Optional
from google.cloud import vision
from google.oauth2 import service_account
from googletrans import Translator
import streamlit as st

translator = Translator()


def get_vision_client():
    """Get authenticated Vision API client"""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        return vision.ImageAnnotatorClient(credentials=credentials)
    except Exception as e:
        print(f"Vision API クライアント作成エラー: {e}")
        raise


def jp(text: str) -> str:
    try:
        result = translator.translate(text, dest="ja")
        return result.text
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return text


def identify_fish_vision(image_bytes: bytes) -> Optional[str]:
    try:
        print("Vision API: クライアント初期化中...")
        client = get_vision_client()
        
        image = vision.Image(content=image_bytes)
        
        print("Vision API: ラベル検出実行中...")
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        print("Vision API: Web検出実行中...")
        web_response = client.web_detection(image=image)
        web_entities = web_response.web_detection.web_entities
        
        print(f"検出されたラベル: {[l.description for l in labels[:10]]}")
        print(f"Web エンティティ: {[e.description for e in web_entities[:10] if e.description]}")
        
        specific_fish = [
            'mackerel', 'tuna', 'salmon', 'sardine', 'bass', 'sea bass',
            'bream', 'sea bream', 'flounder', 'cod', 'trout', 'snapper',
            'yellowtail', 'amberjack', 'grouper', 'halibut', 'rockfish',
            'herring', 'anchovy', 'bonito', 'skipjack', 'albacore',
            'swordfish', 'marlin', 'barracuda', 'sea perch', 'red snapper',
            'black bass', 'striped bass', 'carp', 'catfish', 'pike',
            'mullet', 'horse mackerel', 'jack mackerel', 'spanish mackerel',
            'kingfish', 'pompano', 'mahi mahi', 'dolphinfish', 'wahoo',
            'sheepshead', 'porgy', 'sole', 'plaice', 'turbot', 'monkfish'
        ]
        
        print("戦略1: Web検出から具体的な魚種を検索中...")
        for entity in web_entities:
            if entity.description and entity.score > 0.5:
                desc = entity.description.lower()
                for fish in specific_fish:
                    if fish in desc:
                        japanese_name = jp(entity.description)
                        print(f"具体的な魚種をWeb検出で発見: {entity.description} -> {japanese_name}")
                        return japanese_name
        
        print("戦略2: ラベル検出から具体的な魚種を検索中...")
        for label in labels:
            if label.score > 0.7:
                desc = label.description.lower()
                for fish in specific_fish:
                    if fish in desc:
                        japanese_name = jp(label.description)
                        print(f"具体的な魚種をラベル検出で発見: {label.description} -> {japanese_name}")
                        return japanese_name
        
        print("戦略3: Web検出から一般的な魚を検索中...")
        for entity in web_entities:
            if entity.description and entity.score > 0.6:
                desc = entity.description.lower()
                if 'fish' in desc and desc != 'fish':
                    japanese_name = jp(entity.description)
                    print(f"一般的な魚種をWeb検出で発見: {entity.description} -> {japanese_name}")
                    return japanese_name
        
        print("戦略4: ラベル検出から一般的な魚を検索中...")
        for label in labels:
            if label.score > 0.6:
                desc = label.description.lower()
                if 'fish' in desc:
                    japanese_name = jp(label.description)
                    print(f"一般的な魚をラベル検出で発見: {label.description} -> {japanese_name}")
                    return japanese_name
        
        print("Vision API: 魚を識別できませんでした")
        return None
        
    except Exception as e:
        print(f"Vision API エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def identify_fish_vision_advanced(image_bytes: bytes) -> dict:
    try:
        client = get_vision_client()
        image = vision.Image(content=image_bytes)
        
        response = client.annotate_image({
            'image': image,
            'features': [
                {'type_': vision.Feature.Type.LABEL_DETECTION, 'max_results': 20},
                {'type_': vision.Feature.Type.WEB_DETECTION, 'max_results': 20},
                {'type_': vision.Feature.Type.OBJECT_LOCALIZATION, 'max_results': 10},
            ],
        })
        
        result = {
            'fishName': None,
            'confidence': 0.0,
            'labels': [],
            'webEntities': [],
            'objects': [],
            'isFish': False
        }
        
        for label in response.label_annotations:
            result['labels'].append({
                'name': label.description,
                'score': label.score,
                'nameJa': jp(label.description)
            })
        
        if response.web_detection:
            for entity in response.web_detection.web_entities:
                if entity.description:
                    result['webEntities'].append({
                        'name': entity.description,
                        'score': entity.score,
                        'nameJa': jp(entity.description)
                    })
        
        for obj in response.localized_object_annotations:
            result['objects'].append({
                'name': obj.name,
                'score': obj.score,
                'nameJa': jp(obj.name)
            })
        
        fish_name = identify_fish_vision(image_bytes)
        if fish_name:
            result['fishName'] = fish_name
            result['isFish'] = True
            if result['labels']:
                result['confidence'] = max(label['score'] for label in result['labels'])
        
        return result
        
    except Exception as e:
        print(f"Vision API 高度検出エラー: {e}")
        return {
            'fishName': None,
            'confidence': 0.0,
            'labels': [],
            'webEntities': [],
            'objects': [],
            'isFish': False,
            'error': str(e)
        }
