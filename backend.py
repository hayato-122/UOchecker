# backend.py
import os
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Firebase設定
local_json_path = 'firebase_config.json'
firebase_config = None
raw_firebase_env = os.getenv("firebase")

if os.path.exists(local_json_path):
    with open(local_json_path, "r", encoding="utf-8") as f:
        firebase_config = json.load(f)
elif raw_firebase_env:
    # Docker環境の場合環境変数(文字列)からJSONを取得 huggingのsecret
    try:
        firebase_config = json.loads(raw_firebase_env)
    except json.JSONDecodeError:
        print("Error: 環境変数 'firebase' の取得に失敗しました")

if firebase_config:
    # GoogleVisionAPI用の設定
    if "firebase" in firebase_config:
        config_path = os.path.abspath('firebase_config_temp.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(firebase_config["firebase"], f) # firebaseの中身だけを書き出す
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config_path
        print("GOOGLE_APPLICATION_CREDENTIALSを設定しました")

    # ClaudeAPI用の設定
    if "anthropic" in firebase_config:
        os.environ['ANTHROPIC_API_KEY'] = firebase_config["anthropic"]
        print("ANTHROPIC_API_KEYを設定しました")
else:
    print("認証情報が見つかりません")


from utils.vision_api import identify_fish_vision
from utils.claude_api import generate_fish_info_claude
from utils.database import get_from_cache, save_to_cache, create_cache_key

def validate_input(image_bytes: bytes, prefecture: str, city: str = None) -> Tuple[bool, str]:
    if not image_bytes or len(image_bytes) == 0:
        return False, "画像データが空です"

    if not prefecture or len(prefecture.strip()) == 0:
        return False, "都道府県が指定されていません"

    if len(image_bytes) > 10 * 1024 * 1024:
        return False, "画像サイズが大きすぎます(10MB以下にしてください)"

    return True, ""


def clean_prefecture_name(prefecture: str) -> str:
    for suffix in ['県', '府', '都', '道']:
        if prefecture.endswith(suffix) and len(prefecture) > 1:
            return prefecture[:-1]
    return prefecture


def identify_and_check_fish(image_bytes: bytes, prefecture: str, city: str = None, latitude: float = None,
                            longitude: float = None) -> Dict:
    try:
        is_valid, error_msg = validate_input(image_bytes, prefecture, city)
        if not is_valid:
            return {
                "success": False,
                "error": "入力エラー",
                "message": error_msg
            }

        prefecture = clean_prefecture_name(prefecture)

        print(f"\n{'=' * 60}")
        print(f"🎣 識別開始: {prefecture}")
        if city:
            print(f"📍 市区町村: {city}")
        if latitude and longitude:
            print(f"🌐 座標: ({latitude}, {longitude})")
        print(f"{'=' * 60}\n")

        print("📸 ステップ1: Vision API呼び出し中...")
        fish_name = identify_fish_vision(image_bytes)

        if not fish_name:
            return {
                "success": False,
                "error": "魚を特定できませんでした",
                "message": "画像が不鮮明か、魚が写っていない可能性があります。\n別の角度から撮影してみてください。",
                "suggestions": [
                    "魚全体がはっきり写っている画像を使用してください",
                    "明るい場所で撮影してください",
                    "魚に近づいて撮影してください"
                ]
            }

        print(f"✅ 識別結果: {fish_name}\n")

        print("🔍 ステップ2: データベース確認中...")
        cache_key = create_cache_key(prefecture, fish_name)
        cached_data = get_from_cache(cache_key)

        if cached_data:
            print("⚡ キャッシュHIT! キャッシュデータを返します\n")
            return {
                "success": True,
                "fromCache": True,
                "data": cached_data,
                "identifiedFish": fish_name,
                "location": {
                    "prefecture": prefecture,
                    "city": city,
                    "latitude": latitude,
                    "longitude": longitude
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        print("キャッシュに見つかりませんでした\n")

        print("ステップ3: Claude APIで生成中...")
        fish_info = generate_fish_info_claude(fish_name, prefecture, city, latitude, longitude)

        if not fish_info or fish_info.get('error'):
            return {
                "success": False,
                "error": "情報生成エラー",
                "message": "魚の情報を生成できませんでした。もう一度お試しください。",
                "identifiedFish": fish_name
            }

        print("\nステップ4: データベースに保存中...")
        save_success = save_to_cache(cache_key, fish_info)

        if not save_success:
            print("データベース保存に失敗しましたが、結果は返します")

        print(f"\n✅ 完了!\n{'=' * 60}\n")

        return {
            "success": True,
            "fromCache": False,
            "data": fish_info,
            "identifiedFish": fish_name,
            "location": {
                "prefecture": prefecture,
                "city": city,
                "latitude": latitude,
                "longitude": longitude
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"\n予期せぬエラー発生: {str(e)}\n")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": "システムエラー",
            "message": "処理中にエラーが発生しました。もう一度お試しください。",
            "debug": str(e) if os.getenv('DEBUG') else None
        }