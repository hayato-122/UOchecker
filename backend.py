# backend.py
# メインバックエンドロジック
import os
import sys
from dotenv import load_dotenv

# Load .env file FIRST
load_dotenv()

# Set Google credentials explicitly
credentials_path = os.path.join(os.path.dirname(__file__), 'firebase_config.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

print(f"🔑 Loading credentials from: {credentials_path}")
print(f"🔑 File exists: {os.path.exists(credentials_path)}")

# NOW import everything else
import json
from datetime import datetime
from typing import Dict, Optional
import anthropic
from google.cloud import vision
from utils.vision_api import identify_fish_vision
from utils.claude_api import generate_fish_info_claude
from utils.database import get_from_cache, save_to_cache, create_cache_key
from utils.location import prefecture_from_city




def identify_and_check_fish(image_bytes: bytes, prefecture: str, city: str = None) -> dict:
    """
    メイン関数：画像と位置情報から魚の情報を取得
    
    Args:
        image_bytes: 画像データ (bytes)
        prefecture: 都道府県 (例: "兵庫県")
        city: 市区町村 (例: "神戸") - オプション
        
    Returns:
        魚の情報と法的ステータスを含む辞書
    """
    
    print(f"🎣 識別開始: {prefecture}")
    
    # STEP 1: Google Vision APIで魚を識別
    print("📸 ステップ1: Vision API呼び出し中...")
    fish_name = identify_fish_vision(image_bytes)
    
    if not fish_name:
        return {
            "success": False,
            "error": "魚を特定できませんでした",
            "message": "画像が不鮮明か、魚が写っていない可能性があります"
        }
    
    print(f"✅ 識別結果: {fish_name}")
    
    # STEP 2: データベースキャッシュをチェック
    print("🔍 ステップ2: データベース確認中...")
    cache_key = create_cache_key(prefecture, fish_name)
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        print("⚡ キャッシュHIT! キャッシュデータを返します")
        return {
            "success": True,
            "fromCache": True,
            "data": cached_data
        }
    
    # STEP 3: Claude APIで情報生成
    print("🤖 ステップ3: キャッシュなし。Claude APIで生成中...")
    fish_info = generate_fish_info_claude(fish_name, prefecture, city)
    
    # STEP 4: データベースに保存
    print("💾 ステップ4: データベースに保存中...")
    save_to_cache(cache_key, fish_info)
    
    print("✅ 完了!")
    return {
        "success": True,
        "fromCache": False,
        "data": fish_info
    }
