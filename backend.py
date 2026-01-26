# backend.py
import os
import json
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path

firebase_config_path = Path('firebase_config.json')
gemini_api_key_path = Path('gemini_api_key.txt')
ocp_api_key_path = Path('ocp_api_key.txt')
gemini_api_key_txt = os.environ.get('GEMINI_API_KEY_TXT')
ocp_api_key_txt = os.environ.get('OCP_API_KEY_TXT')

if gemini_api_key_txt:
    os.environ['GEMINI_API_KEY_TXT'] = gemini_api_key_txt
    print("gemini_api_key loaded from huggingface")
elif gemini_api_key_path.exists():
    with open('gemini_api_key.txt', 'r') as f:
        api_key = f.read().strip().split('\n')[0].strip()
        os.environ['GEMINI_API_KEY_TXT'] = api_key
    print("gemini_api_key.txt found")
elif 'GEMINI_API_KEY_TXT' not in os.environ:
    print("GEMINI_API_KEY not found")

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

from utils.gemini_api import identify_and_analyze_fish

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

        print("Gemini APIで魚を識別・分析中...")

        result = identify_and_analyze_fish(
            image_bytes=image_bytes,
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