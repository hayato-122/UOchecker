# backend.py
import os
import json
import base64
from typing import Dict, Tuple

print("🔧 環境設定中...")

if os.path.exists('firebase_config.json'):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase_config.json'
    print("Firebase設定完了")

if os.path.exists('anthropic_key.txt'):
    with open('anthropic_key.txt', 'r', encoding='utf-8') as f:
        api_key = f.read().strip().split('\n')[0].strip()
        os.environ['ANTHROPIC_API_KEY'] = api_key
        print(f"Anthropic API Key設定完了: {api_key[:20]}...")
else:
    print("anthropic_key.txt が見つかりません!")

from utils.claude_api import identify_and_analyze_fish


def validate_input(image_bytes: bytes, prefecture: str) -> Tuple[bool, str]:
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
        is_valid, error_msg = validate_input(image_bytes, prefecture)
        if not is_valid:
            return {
                "success": False,
                "error": "入力エラー",
                "message": error_msg,
                "isLegal": False
            }

        prefecture = clean_prefecture_name(prefecture)

        print(f"\n{'=' * 60}")
        print(f"🎣 識別開始: {prefecture}")
        if city:
            print(f"市区町村: {city}")
        if latitude and longitude:
            print(f"座標: ({latitude}, {longitude})")
        print(f"{'=' * 60}\n")

        try:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            print(f"画像をbase64に変換しました")
        except Exception as e:
            print(f"Base64変換エラー: {e}")
            return {
                "success": False,
                "error": "画像変換エラー",
                "message": "画像の処理中にエラーが発生しました。",
                "isLegal": False
            }

        result = identify_and_analyze_fish(
            image_base64=image_base64,
            prefecture=prefecture,
            city=city,
            latitude=latitude,
            longitude=longitude
        )

        if not result.get('success'):
            print(f"判定結果: 持ち帰りNG")
            return result

        print(f"判定結果: 持ち帰りOK - {result.get('fishNameJa')}")
        print(f"完了!\n{'=' * 60}\n")

        return {
            "success": True,
            "isLegal": result.get('isLegal', True),
            "fishNameJa": result.get('fishNameJa'),
            "gyogyoken": result.get('gyogyoken'),
            "isEdible": result.get('isEdible')
        }

    except Exception as e:
        print(f"\n予期せぬエラー発生: {str(e)}\n")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": "システムエラー",
            "message": "処理中にエラーが発生しました。もう一度お試しください。",
            "isLegal": False
        }