# backend.py
import os
import json
import base64
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path

firebase_config_path = Path('firebase_config.json')
anthropic_key_path = Path('anthropic_key.txt')
ocp_api_key_path = Path('ocp_api_key.txt')
firebase_json = os.environ.get('FIREBASE_CONFIG_JSON')
anthropic_txt = os.environ.get('ANTHROPIC_KEY_TXT')
ocp_api_key_txt = os.environ.get('OCP_API_KEY_TXT')

if firebase_json:
    with open('firebase_config.json', 'w') as f:
        f.write(firebase_json)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase_config.json'
    print("firebase_config loaded from huggingface")
elif firebase_config_path.exists():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase_config.json'
    print("firebase_config.json found")
else:
    print("firebase_config.json not found")

if anthropic_txt:
    os.environ['ANTHROPIC_API_KEY_TXT'] = anthropic_txt
    print("anthropic_key loaded from huggingface")
elif anthropic_key_path.exists():
    with open('anthropic_key.txt', 'r') as f:
        api_key = f.read().strip().split('\n')[0].strip()
        os.environ['ANTHROPIC_API_KEY_TXT'] = api_key
    print("anthropic_key.txt found")
elif 'ANTHROPIC_API_KEY_TXT' not in os.environ:
    print("ANTHROPIC_API_KEY not found")

if ocp_api_key_txt:
    os.environ['OCP_API_KEY_TXT'] = ocp_api_key_txt
    print("ocp_api_key_txt loaded from huggingface")
elif ocp_api_key_path.exists():
    with open('ocp_api_key.txt', 'r') as f:
        api_key = f.read().strip().split('\n')[0].strip()
        os.environ['OCP_API_KEY_TXT'] = api_key
    print("ocp_api_key_txt found")
elif 'OCP_API_KEY_TXT' not in os.environ:
    print("OCP_API_KEY not found")

from utils.claude_api import identify_and_analyze_fish
from utils.database import get_from_cache, save_to_cache, create_cache_key


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


def identify_and_check_fish(image_bytes: bytes, prefecture: str, city: str = None, latitude: float = None, longitude: float = None) -> Dict:
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
        print(f"識別開始: {prefecture}")
        if city:
            print(f"市区町村: {city}")
        if latitude and longitude:
            print(f"座標: ({latitude}, {longitude})")
        print(f"{'=' * 60}\n")

        print("Claude APIで魚を識別・分析中...")

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
            return result

        fish_name_ja = result.get('fishNameJa', '不明')
        fish_name_en = result.get('fishNameEn', '')
        scientific_name = result.get('scientificName', '')

        print(f"識別結果: {fish_name_ja} ({fish_name_en})")
        print(f"学名: {scientific_name}")
        print(f"持ち帰り: {'OK' if result.get('isLegal') else 'NG'}")

        cache_key = create_cache_key(prefecture, fish_name_ja)
        cached_data = get_from_cache(cache_key)

        if cached_data:
            print("キャッシュHIT")
            return {
                "success": True,
                "fromCache": True,
                "isLegal": cached_data.get('isLegal'),
                "fishNameJa": cached_data.get('fishNameJa'),
                "fishNameEn": cached_data.get('fishNameEn'),
                "scientificName": cached_data.get('scientificName'),
                "gyogyoken": cached_data.get('gyogyoken'),
                "isEdible": cached_data.get('isEdible'),
                "timestamp": datetime.utcnow().isoformat()
            }

        save_data = {
            'isLegal': result.get('isLegal'),
            'fishNameJa': fish_name_ja,
            'fishNameEn': fish_name_en,
            'scientificName': scientific_name,
            'gyogyoken': result.get('gyogyoken'),
            'isEdible': result.get('isEdible')
        }
        save_to_cache(cache_key, save_data)

        print(f"完了\n{'=' * 60}\n")

        return {
            "success": True,
            "fromCache": False,
            "isLegal": result.get('isLegal'),
            "fishNameJa": fish_name_ja,
            "fishNameEn": fish_name_en,
            "scientificName": scientific_name,
            "gyogyoken": result.get('gyogyoken'),
            "isEdible": result.get('isEdible'),
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
            "isLegal": False,
            "debug": str(e) if os.getenv('DEBUG') else None
        }