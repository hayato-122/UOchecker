# backend.py
import os
import json
from datetime import datetime
from typing import Dict, Optional

# Load Streamlit secrets if available

import streamlit as st
if hasattr(st, 'secrets'):
        os.environ['ANTHROPIC_API_KEY'] = st.secrets.get('ANTHROPIC_API_KEY', '')
        # For Firebase, we'll create the JSON file from secrets
        firebase_config = dict(st.secrets.get('firebase', {}))
        if firebase_config:
            with open('firebase_config_temp.json', 'w') as f:
                json.dump(firebase_config, f)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase_config_temp.json'

# NOW import everything else
from utils.vision_api import identify_fish_vision
from utils.claude_api import generate_fish_info_claude
from utils.database import get_from_cache, save_to_cache, create_cache_key


def identify_and_check_fish(image_bytes: bytes, prefecture: str, city: str = None) -> Dict:
    """
    メイン関数：画像と位置情報から魚の情報を取得
    
    Args:
        image_bytes: 画像データ (bytes)
        prefecture: 都道府県 (例: "兵庫県")
        city: 市区町村 (例: "神戸市") - オプション
        
    Returns:
        魚の情報と法的ステータスを含む辞書
    """
    
    try:
        # Clean up prefecture name (remove extra words)
        
        print(f"\n{'='*60}")
        print(f"🎣 識別開始: {prefecture}")
        if city:
            print(f"📍 市区町村: {city}")
        print(f"{'='*60}\n")
        
        # STEP 1: Identify fish with Vision API
        print("📸 ステップ1: Vision API呼び出し中...")
        fish_name = identify_fish_vision(image_bytes)
        
        if not fish_name:
            return {
                "success": False,
                "error": "魚を特定できませんでした",
                "message": "画像が不鮮明か、魚が写っていない可能性があります。別の角度から撮影してみてください。"
            }
        
        print(f"✅ 識別結果: {fish_name}\n")
        
        # STEP 2: Check database cache
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
                    "city": city
                }
            }
        
        print("❌ キャッシュに見つかりませんでした\n")
        
        # STEP 3: Generate with Claude API
        print("🤖 ステップ3: キャッシュなし。Claude APIで生成中...")
        fish_info = generate_fish_info_claude(fish_name, prefecture, city)
        
        # STEP 4: Save to database
        print("\n💾 ステップ4: データベースに保存中...")
        save_to_cache(cache_key, fish_info)
        
        print(f"\n✅ 完了!\n{'='*60}\n")
        
        return {
            "success": True,
            "fromCache": False,
            "data": fish_info,
            "identifiedFish": fish_name,
            "location": {
                "prefecture": prefecture,
                "city": city
            }
        }
        
    except Exception as e:
        print(f"\n❌ エラー発生: {str(e)}\n")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": "処理中にエラーが発生しました",
            "message": str(e),
            "debug": traceback.format_exc()
        }
