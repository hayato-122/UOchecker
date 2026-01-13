# backend.py
import os
import json
import base64
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path

# Pathを設定
firebase_config_path = Path('firebase_config.json')
anthropic_key_path = Path('anthropic_key.txt')
firebase_json = os.environ.get('FIREBASE_CONFIG_JSON')
anthropic_txt = os.environ.get('ANTHROPIC_KEY_TXT')


if firebase_json: # huggingfaceでsecretsが設定されている場合
    with open('firebase_config.json', 'w') as f:
        f.write(firebase_json)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase_config.json'
    print("firebase_configをhuggingfaceから読み込みました。")

elif firebase_config_path.exists(): # ローカルのjsonファイルから設定する場合
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase_config.json'
    print("firebase_config.jsonが見つかりました。")
else:
    print("firebase_config.jsonが見つかりません。")

if anthropic_txt:
    os.environ['ANTHROPIC_API_KEY'] = anthropic_txt
    print("anthropic_keyをhuggingfaceから読み込みました。")

if anthropic_key_path.exists():
    with open('anthropic_key.txt', 'r') as f:
        api_key = f.read().strip().split('\n')[0].strip()
        os.environ['ANTHROPIC_API_KEY'] = api_key
    print("anthropic_key.txtが見つかりました。")
elif 'ANTHROPIC_API_KEY' not in os.environ:
    print("ANTHROPIC_API_KEYが見つかりません")

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
                "message": error_msg
            }
        
        prefecture = clean_prefecture_name(prefecture)
        
        print(f"\n{'='*60}")
        print(f"識別開始: {prefecture}")
        if city:
            print(f"市区町村: {city}")
        if latitude and longitude:
            print(f"座標: ({latitude}, {longitude})")
        print(f"{'='*60}\n")
        
        print("Claude APIで魚を識別・分析中...")
        
        try:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            print(f"画像をbase64に変換しました ({len(image_base64)} 文字)")
        except Exception as e:
            print(f"Base64変換エラー: {e}")
            return {
                "success": False,
                "error": "画像変換エラー",
                "message": "画像の処理中にエラーが発生しました。"
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
        
        fish_name = result.get('fishNameJa', '不明')
        fish_data = result.get('data', {})
        
        print(f"識別結果: {fish_name}\n")
        
        print("🔍 データベース確認中...")
        cache_key = create_cache_key(prefecture, fish_name)
        cached_data = get_from_cache(cache_key)
        
        if cached_data and not result.get('fromImage'):
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
        
        print("データベースに保存中...")
        save_to_cache(cache_key, fish_data)
        
        print(f"\n完了!\n{'='*60}\n")
        
        return {
            "success": True,
            "fromCache": False,
            "data": fish_data,
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
