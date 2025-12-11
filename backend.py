# backend.py
import os
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import streamlit as st

# ANTHROPIC_API_KEY の設定
# huggingの場合secretで環境変数に入れられている
if "ANTHROPIC_API_KEY" not in os.environ:
    # 環境変数にない場合st.secretsから取得
    try:
        if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
            os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass # secretsが見つからない場合は無視

# Firebase設定
firebase_config = {}
raw_firebase_env = os.getenv("firebase")

if raw_firebase_env:
    # Docker環境の場合環境変数(文字列)からJSONを取得 huggingのsecret
    try:
        firebase_config = json.loads(raw_firebase_env)
    except json.JSONDecodeError:
        print("Error: 環境変数 'firebase' の取得に失敗しました")
else:
    # ローカル環境: st.secrets(辞書)から取得を試みる
    try:
        if hasattr(st, "secrets") and "firebase" in st.secrets:
            raw_config = st.secrets["firebase"]
            # 辞書ならそのまま、文字列ならパース
            if isinstance(raw_config, str):
                firebase_config = json.loads(raw_config)
            else:
                firebase_config = dict(raw_config)
    except Exception:
        pass # secretsが見つからない場合は無視

    if firebase_config:
        config_path = 'firebase_config_temp.json'
        with open(config_path, 'w') as f:
            json.dump(firebase_config, f)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config_path

# Import utilities after environment setup
from utils.vision_api import identify_fish_vision
from utils.claude_api import generate_fish_info_claude
from utils.database import get_from_cache, save_to_cache, create_cache_key


def validate_input(image_bytes: bytes, prefecture: str, city: str = None) -> Tuple[bool, str]:
    """
    入力データの検証
    
    Returns:
        (valid: bool, error_message: str)
    """
    if not image_bytes or len(image_bytes) == 0:
        return False, "画像データが空です"
    
    if not prefecture or len(prefecture.strip()) == 0:
        return False, "都道府県が指定されていません"
    
    # 画像サイズの確認（10MB制限）
    if len(image_bytes) > 10 * 1024 * 1024:
        return False, "画像サイズが大きすぎます（10MB以下にしてください）"
    
    return True, ""


def clean_prefecture_name(prefecture: str) -> str:
    """
    都道府県名の正規化
    """
    # Remove suffixes
    for suffix in ['県', '府', '都', '道']:
        if prefecture.endswith(suffix) and len(prefecture) > 1:
            return prefecture[:-1]
    return prefecture


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
        # 入力検証
        is_valid, error_msg = validate_input(image_bytes, prefecture, city)
        if not is_valid:
            return {
                "success": False,
                "error": "入力エラー",
                "message": error_msg
            }
        
        # Clean prefecture name
        prefecture = clean_prefecture_name(prefecture)
        
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
                "message": "画像が不鮮明か、魚が写っていない可能性があります。\n別の角度から撮影してみてください。",
                "suggestions": [
                    "魚全体がはっきり写っている画像を使用してください",
                    "明るい場所で撮影してください",
                    "魚に近づいて撮影してください"
                ]
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
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        print("キャッシュに見つかりませんでした\n")
        
        # STEP 3: Generate with Claude API
        print("ステップ3: Claude APIで生成中...")
        fish_info = generate_fish_info_claude(fish_name, prefecture, city)
        
        if not fish_info or fish_info.get('error'):
            return {
                "success": False,
                "error": "情報生成エラー",
                "message": "魚の情報を生成できませんでした。もう一度お試しください。",
                "identifiedFish": fish_name
            }
        
        # STEP 4: Save to database
        print("\nステップ4: データベースに保存中...")
        save_success = save_to_cache(cache_key, fish_info)
        
        if not save_success:
            print("データベース保存に失敗しましたが、結果は返します")
        
        print(f"\n 完了!\n{'='*60}\n")
        
        return {
            "success": True,
            "fromCache": False,
            "data": fish_info,
            "identifiedFish": fish_name,
            "location": {
                "prefecture": prefecture,
                "city": city
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
