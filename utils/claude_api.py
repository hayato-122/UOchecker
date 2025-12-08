# utils/claude_api.py
import json
import os
from datetime import datetime
from typing import Dict, Optional
import streamlit as st
from anthropic import Anthropic

# Singleton client instance
_client = None

def get_anthropic_client() -> Anthropic:
    """Get or create Anthropic client singleton"""
    global _client
    if _client is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key and hasattr(st, 'secrets'):
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY が設定されていません")
        
        _client = Anthropic(api_key=api_key)
    
    return _client


def generate_fish_info_claude(fish_name: str, prefecture: str, city: str = None) -> Dict:
    """
    Claude APIを使用して魚の完全な情報を生成
    
    Args:
        fish_name: 魚の名前 (英語)
        prefecture: 都道府県
        city: 市区町村 (オプション)
        
    Returns:
        魚の情報を含む辞書
    """
    
    try:
        client = get_anthropic_client()
        
        location = f"{city}, {prefecture}" if city else prefecture
        
        prompt = f"""あなたは日本の釣りと海洋生物の専門家です。{location}における"{fish_name}"という魚について、包括的な情報を提供してください。

以下の正確なJSON構造で返してください（JSONのみを返し、他の説明文は含めないでください）：

{{
  "fishNameJa": "日本語名",
  "fishNameEn": "{fish_name}",
  "scientificName": "学名",
  
  "isLegal": true または false,
  "canTakeHome": true または false,
  "status": "OK" または "RESTRICTED" または "PROHIBITED",
  "legalExplanation": "わかりやすい日本語での説明（2-3文で簡潔に）",
  
  "minSize": cm単位の数値 または 0,
  "maxSize": cm単位の数値 または null,
  "dailyLimit": 数値 または null,
  "seasonalBan": ["禁漁期間の説明"],
  "bannedMonths": [数値の配列],
  
  "isEdible": true または false,
  "edibilityNotes": "食用に関する注意事項",
  "toxicParts": ["毒のある部位"],
  "preparationWarnings": "調理時の警告",
  
  "description": "魚の特徴説明（2-3文）",
  "season": ["春", "夏", "秋", "冬"],
  "peakSeason": "旬の時期",
  "habitat": "生息地",
  "averageSize": "一般的なサイズ範囲",
  
  "cookingMethods": ["刺身", "焼き魚", "煮付け"],
  "taste": "味の特徴",
  "nutrition": "栄養的特徴",
  
  "regulationSource": "情報源（都道府県の漁業規則等）",
  "confidence": "high" または "medium" または "low"
}}

重要なルール：
1. {location}の具体的な漁業規則を考慮してください
2. 不確実な場合は保守的に判断し、confidenceを"medium"または"low"に設定
3. 絶滅危惧種や保護対象の場合は必ず"PROHIBITED"に
4. サイズ制限は最小サイズのみの場合が多い（maxSizeはnullでOK）
5. 必ずJSON形式のみを返し、前後に説明文を付けないでください"""

        message = client.messages.create(
            model="claude-4-sonnet-20250514",
            max_tokens=2048,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # JSONレスポンスを抽出
        response_text = message.content[0].text.strip()
        
        # JSONブロックの抽出（```json ... ``` で囲まれている場合）
        if response_text.startswith("```"):
            # Remove code block markers
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
        
        # JSONパース
        fish_data = json.loads(response_text)
        
        # メタデータを追加
        fish_data["prefecture"] = prefecture
        if city:
            fish_data["city"] = city
        fish_data["fishIdentified"] = fish_name
        fish_data["generatedBy"] = "claude"
        fish_data["generatedAt"] = datetime.utcnow().isoformat()
        
        print(f"   Claude APIで情報を生成しました")
        print(f"   ステータス: {fish_data.get('status', 'UNKNOWN')}")
        print(f"   信頼度: {fish_data.get('confidence', 'unknown')}")
        
        return fish_data
        
    except json.JSONDecodeError as e:
        print(f"   JSON解析エラー: {e}")
        print(f"   レスポンス: {response_text[:200]}...")
        return create_fallback_response(fish_name, prefecture, "JSON解析に失敗しました")
        
    except Exception as e:
        print(f"  Claude APIエラー: {e}")
        import traceback
        traceback.print_exc()
        return create_fallback_response(fish_name, prefecture, str(e))


def create_fallback_response(fish_name: str, prefecture: str, error_detail: str = "") -> Dict:
    """
    AIが失敗した場合の安全なフォールバック
    """
    return {
        "fishNameJa": fish_name,
        "fishNameEn": fish_name,
        "scientificName": "不明",
        "isLegal": False,
        "canTakeHome": False,
        "status": "UNKNOWN",
        "legalExplanation": f"申し訳ございません。この魚の情報を自動で取得できませんでした。\n{prefecture}の漁業協同組合または水産課にお問い合わせください。",
        "minSize": 0,
        "maxSize": None,
        "dailyLimit": None,
        "seasonalBan": [],
        "bannedMonths": [],
        "isEdible": None,
        "edibilityNotes": "食用可能かどうか確認が必要です",
        "toxicParts": [],
        "preparationWarnings": "専門家に確認してから調理してください",
        "description": "魚の詳細情報を取得できませんでした。",
        "season": [],
        "peakSeason": "不明",
        "habitat": "不明",
        "averageSize": "不明",
        "cookingMethods": [],
        "taste": "不明",
        "nutrition": "不明",
        "regulationSource": "取得失敗",
        "confidence": "low",
        "error": True,
        "errorDetail": error_detail,
        "prefecture": prefecture
    }
