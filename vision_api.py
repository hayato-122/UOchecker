# utils/vision_api.py
# Google Vision API統合

from typing import Optional
from google.cloud import vision
from googletrans import Translator

# グローバル翻訳インスタンス
translator = Translator()


def jp(text: str) -> str:
    """
    英語テキストを日本語に翻訳
    
    Args:
        text: 翻訳する英語テキスト
        
    Returns:
        日本語に翻訳されたテキスト
    """
    try:
        result = translator.translate(text, dest="ja")
        return result.text
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return text  # 翻訳失敗時は元のテキストを返す


def identify_fish_vision(image_bytes: bytes) -> Optional[str]:
    """
    Google Vision APIを使用して画像から魚を識別
    
    Args:
        image_bytes: 画像データ (bytes)
        
    Returns:
        識別された魚の名前（日本語）、または None
    """
    try:
        print("Vision API: クライアント初期化中...")
        client = vision.ImageAnnotatorClient()
        
        # 画像オブジェクト作成
        image = vision.Image(content=image_bytes)
        
        # ラベル検出
        print("Vision API: ラベル検出実行中...")
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        # Web検出（より具体的な魚種の特定に有効）
        print("Vision API: Web検出実行中...")
        web_response = client.web_detection(image=image)
        web_entities = web_response.web_detection.web_entities
        
        # デバッグ出力
        print(f"検出されたラベル: {[l.description for l in labels[:10]]}")
        print(f"Web エンティティ: {[e.description for e in web_entities[:10] if e.description]}")
        
        # 具体的な魚の種類リスト（優先度高）
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
        
        # 戦略1: Web検出から具体的な魚種を探す（最も精度が高い）
        print("戦略1: Web検出から具体的な魚種を検索中...")
        for entity in web_entities:
            if entity.description and entity.score > 0.5:  # スコアが高いものを優先
                desc = entity.description.lower()
                for fish in specific_fish:
                    if fish in desc:
                        japanese_name = jp(entity.description)
                        print(f"具体的な魚種をWeb検出で発見: {entity.description} -> {japanese_name}")
                        return japanese_name
        
        # 戦略2: ラベル検出から具体的な魚種を探す
        print("戦略2: ラベル検出から具体的な魚種を検索中...")
        for label in labels:
            if label.score > 0.7:  # 信頼度が高いラベルのみ
                desc = label.description.lower()
                for fish in specific_fish:
                    if fish in desc:
                        japanese_name = jp(label.description)
                        print(f"具体的な魚種をラベル検出で発見: {label.description} -> {japanese_name}")
                        return japanese_name
        
        # 戦略3: Web検出から一般的な"fish"を含むエンティティを探す
        print("戦略3: Web検出から一般的な魚を検索中...")
        for entity in web_entities:
            if entity.description and entity.score > 0.6:
                desc = entity.description.lower()
                if 'fish' in desc and desc != 'fish':  # "fish"単体は除外
                    japanese_name = jp(entity.description)
                    print(f"一般的な魚種をWeb検出で発見: {entity.description} -> {japanese_name}")
                    return japanese_name
        
        # 戦略4: ラベル検出から一般的な"fish"を探す（最後の手段）
        print("戦略4: ラベル検出から一般的な魚を検索中...")
        for label in labels:
            if label.score > 0.6:
                desc = label.description.lower()
                if 'fish' in desc:
                    japanese_name = jp(label.description)
                    print(f"一般的な魚をラベル検出で発見: {label.description} -> {japanese_name}")
                    return japanese_name
        
        # 何も見つからなかった
        print("Vision API: 魚を識別できませんでした")
        return None
        
    except Exception as e:
        print(f"Vision API エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def identify_fish_vision_advanced(image_bytes: bytes) -> dict:
    """
    より詳細な情報を返す高度な魚識別関数
    
    Args:
        image_bytes: 画像データ (bytes)
        
    Returns:
        識別結果の詳細情報を含む辞書
    """
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        
        # 複数の検出を同時実行
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
        
        # ラベル情報
        for label in response.label_annotations:
            result['labels'].append({
                'name': label.description,
                'score': label.score,
                'nameJa': jp(label.description)
            })
        
        # Web検出情報
        if response.web_detection:
            for entity in response.web_detection.web_entities:
                if entity.description:
                    result['webEntities'].append({
                        'name': entity.description,
                        'score': entity.score,
                        'nameJa': jp(entity.description)
                    })
        
        # オブジェクト検出情報
        for obj in response.localized_object_annotations:
            result['objects'].append({
                'name': obj.name,
                'score': obj.score,
                'nameJa': jp(obj.name)
            })
        
        # 魚を識別
        fish_name = identify_fish_vision(image_bytes)
        if fish_name:
            result['fishName'] = fish_name
            result['isFish'] = True
            # 信頼度を推定（最高スコアのラベルから）
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