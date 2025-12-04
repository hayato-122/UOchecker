# utils/claude_api.py
import os
import json
from datetime import datetime
from typing import Dict

# Check if running in Streamlit
try:
    import streamlit as st
    # API key already set in backend.py
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
except:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))



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
    
    client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    
    location = f"{city}, {prefecture}" if city else prefecture
    
    prompt = f"""あなたは日本の釣りと海洋生物の専門家です。{location}における"{fish_name}"という魚について、包括的な情報を提供してください。

以下の正確なJSON構造で返してください：

{{
  "fishNameJa": "日本語名",
  "fishNameEn": "{fish_name}",
  "scientificName": "学名",
  
  "isLegal": true または false,
  "canTakeHome": true または false,
  "status": "OK" または "RESTRICTED" または "PROHIBITED",
  "legalExplanation": "日本語での説明",
  
  "minSize": cm単位の数値 または 0,
  "maxSize": cm単位の数値 または null,
  "dailyLimit": 数値 または null,
  "seasonalBan": ["月1", "月2"],
  "bannedMonths": [6, 7],
  
  "isEdible": true または false,
  "edibilityNotes": "日本語での注意事項",
  "toxicParts": ["部位1", "部位2"],
  "preparationWarnings": "日本語での警告",
  
  "description": "日本語での説明（2-3文）",
  "season": ["季節1", "季節2"],
  "peakSeason": "旬の時期",
  "habitat": "生息地",
  "averageSize": "サイズ範囲",
  
  "cookingMethods": ["調理法1", "調理法2", "調理法3"],
  "taste": "味の説明",
  "nutrition": "栄養情報",
  
  "regulationSource": "情報源",
  "confidence": "high" または "medium" または "low"
}}

重要なルール：
1. 法的ステータスは保守的に - 不明な場合はRESTRICTEDにする
2. サイズ制限、1日の漁獲量制限、禁漁期を含める
3. 魚が食用可能か、毒のある部位があるかを明記
4. 正確な調理と準備情報を提供
5. 絶滅危惧種や保護対象の場合はPROHIBITEDにする"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # JSONレスポンスを抽出
        response_text = message.content[0].text
        fish_data = json.loads(response_text)
        
        # メタデータを追加
        fish_data["prefecture"] = prefecture
        if city:
            fish_data["city"] = city
        fish_data["fishIdentified"] = fish_name
        fish_data["generatedBy"] = "claude"
        fish_data["generatedAt"] = datetime.utcnow().isoformat()
        
        return fish_data
        
    except Exception as e:
        print(f"❌ Claude APIエラー: {e}")
        return create_fallback_response(fish_name, prefecture)


def create_fallback_response(fish_name: str, prefecture: str) -> Dict:
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
        "legalExplanation": "データを生成できませんでした。現地の規則を確認してください。",
        "minSize": 0,
        "maxSize": None,
        "dailyLimit": None,
        "seasonalBan": [],
        "bannedMonths": [],
        "isEdible": None,
        "edibilityNotes": "不明",
        "description": "魚の情報を取得できませんでした。",
        "cookingMethods": [],
        "regulationSource": "取得失敗",
        "confidence": "low",
        "error": True,
        "prefecture": prefecture
    }