import os
from typing import Optional
from google.cloud import vision

def identify_fish_vision(image_bytes: bytes) -> Optional[str]:
    """
    Google Cloud Vision APIを使用して画像から魚を識別

    Args:
        image_bytes: 画像データ

    Returns:
        魚の名前 (英語) または None
    """
    try:
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if creds_path and os.path.exists(creds_path):
            # 認証ファイルを直接指定してクライアントを作成
            client = vision.ImageAnnotatorClient.from_service_account_json(creds_path)
        else:
            # 万が一パスがない場合はデフォルト（Hugging Face環境など）
            client = vision.ImageAnnotatorClient()

        image = vision.Image(content=image_bytes)

        # ラベル検出
        response = client.label_detection(image=image)
        labels = response.label_annotations

        # Web検出（より正確な識別のため）
        web_response = client.web_detection(image=image)
        web_entities = web_response.web_detection.web_entities

        print(f"  🏷️ ラベル: {[l.description for l in labels[:5]]}")
        print(f"  🌐 Webエンティティ: {[e.description for e in web_entities[:3] if e.description]}")

        # 魚の種類（具体的な名前を優先）
        specific_fish = [
            'mackerel', 'tuna', 'salmon', 'sardine', 'bass',
            'bream', 'flounder', 'cod', 'trout', 'snapper',
            'saba', 'maguro', 'sake', 'iwashi', 'aji'
        ]

        # Webエンティティを先にチェック（より具体的）
        for entity in web_entities:
            if entity.description:
                desc = entity.description.lower()
                for fish in specific_fish:
                    if fish in desc:
                        print(f"  ✅ 具体的な魚種(Web): {entity.description}")
                        return entity.description

        # ラベルをチェック
        for label in labels:
            desc = label.description.lower()
            for fish in specific_fish:
                if fish in desc:
                    print(f"  ✅ 具体的な魚種(ラベル): {label.description}")
                    return label.description

        # 一般的な「魚」でもOK
        for label in labels:
            if 'fish' in label.description.lower() and label.score > 0.7:
                print(f"  ⚠️ 一般的な魚: {label.description}")
                return label.description

        print("  ❌ 魚が見つかりませんでした")
        return None

    except Exception as e:
        print(f"  ❌ Vision APIエラー: {e}")
        import traceback
        traceback.print_exc()
        return None