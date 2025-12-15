# utils/claude_api.py
# Claude API統合 - 修正版

import os
import json
from datetime import datetime
from anthropic import Anthropic
from typing import Dict


def generate_fish_info_claude(fish_name: str, prefecture: str, city: str = None) -> Dict:
    """
    Claude APIを使用して魚の完全な情報を生成
    
    Args:
        fish_name: 魚の名前 (英語または日本語)
        prefecture: 都道府県
        city: 市区町村 (オプション)
        
    Returns:
        魚の情報を含む辞書
    """
    
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    location = f"{city}, {prefecture}" if city else prefecture
    
    # より詳細で明確なプロンプト
    prompt = f"""あなたは日本の釣りと海洋生物の専門家です。{location}における"{fish_name}"という魚について、包括的な情報を日本語で提供してください。

必ず以下のJSON構造で、全てのフィールドを埋めて返してください：

{{
  "fishNameJa": "魚の日本語名（例：マサバ、クロマグロ）",
  "fishNameEn": "魚の英語名",
  "scientificName": "学名（ラテン語）",
  
  "isLegal": true,
  "canTakeHome": true,
  "status": "OK",
  "legalExplanation": "{prefecture}では、この魚は釣って持ち帰ることができます。ただし、サイズ制限や漁獲量制限を守ってください。",
  
  "minSize": 25,
  "maxSize": null,
  "dailyLimit": 10,
  "seasonalBan": ["6月", "7月"],
  "bannedMonths": [6, 7],
  
  "isEdible": true,
  "edibilityNotes": "新鮮なものは刺身で食べられます。寄生虫の心配がある場合は冷凍または加熱調理してください。",
  "toxicParts": [],
  "preparationWarnings": "内臓は早めに取り除いてください。",
  
  "description": "この魚は日本近海でよく見られる魚です。青魚の代表格で、脂がのった味わいが特徴です。",
  "season": ["春", "秋"],
  "peakSeason": "秋から冬にかけて",
  "habitat": "沿岸から沖合の表層",
  "averageSize": "30-40cm",
  
  "cookingMethods": ["刺身", "塩焼き", "煮付け", "フライ"],
  "taste": "脂がのっていて濃厚な味わい。青魚特有の風味があります。",
  "nutrition": "DHA、EPAなどのオメガ3脂肪酸が豊富。ビタミンB12、ビタミンDも含まれています。",
  
  "regulationSource": "{prefecture}の漁業調整規則",
  "confidence": "high",
  "sourceUrl": null
}}

重要な指示：
1. **全てのテキストは日本語で記述してください**（fishNameEn, scientificName以外）
2. legalExplanationは具体的に「○○県では～」という形で説明してください
3. statusは以下のルールで決定：
   - OK: 一般的に釣って持ち帰れる
   - RESTRICTED: サイズ制限や期間制限がある
   - PROHIBITED: 禁止されている、または絶滅危惧種
4. minSizeは0以上の数値、制限がない場合は0
5. dailyLimitは数値またはnull
6. seasonalBanは日本語の月名の配列（例：["6月", "7月"]）
7. bannedMonthsは数値の配列（例：[6, 7]）
8. cookingMethodsは日本語で最低3つ提供
9. 不明な情報は推測せず、"不明"または"情報なし"と記載
10. JSONのみを返し、他の説明文は含めないでください

{prefecture}の具体的な規制情報を考慮して回答してください。"""

    try:
        print(f"Claude APIに問い合わせ中: {fish_name} @ {location}")
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Claude 4.5 - 最新で最も賢いモデル
            max_tokens=4096,  # トークン数を増やす
            temperature=0.2,  # 事実情報生成のため低めに設定
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # レスポンスを取得
        response_text = message.content[0].text
        print(f"Claude応答を受信: {len(response_text)} 文字")
        
        # JSONを抽出（マークダウンのコードブロックを除去）
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # JSONをパース
        try:
            fish_data = json.loads(response_text)
            print("JSONパース成功")
        except json.JSONDecodeError as je:
            print(f"JSONパースエラー: {je}")
            print(f"受信したテキスト: {response_text[:500]}...")
            return create_fallback_response(fish_name, prefecture, f"JSON解析エラー: {str(je)}")
        
        # 必須フィールドの検証
        required_fields = ['fishNameJa', 'status', 'legalExplanation']
        missing_fields = [field for field in required_fields if field not in fish_data]
        
        if missing_fields:
            print(f"必須フィールドが不足: {missing_fields}")
            # 不足フィールドにデフォルト値を設定
            if 'fishNameJa' not in fish_data:
                fish_data['fishNameJa'] = fish_name
            if 'status' not in fish_data:
                fish_data['status'] = 'UNKNOWN'
            if 'legalExplanation' not in fish_data:
                fish_data['legalExplanation'] = '規制情報を確認できませんでした。'
        
        # メタデータを追加
        fish_data["prefecture"] = prefecture
        if city:
            fish_data["city"] = city
        fish_data["fishIdentified"] = fish_name
        fish_data["generatedBy"] = "claude"
        fish_data["generatedAt"] = datetime.utcnow().isoformat()
        
        print(f"生成完了: {fish_data.get('fishNameJa', fish_name)}")
        return fish_data
        
    except Exception as e:
        print(f"Claude APIエラー: {e}")
        import traceback
        traceback.print_exc()
        return create_fallback_response(fish_name, prefecture, str(e))


def create_fallback_response(fish_name: str, prefecture: str, error_msg: str = "") -> Dict:
    """
    AIが失敗した場合の安全なフォールバック
    """
    print(f"フォールバックレスポンスを生成: {error_msg}")
    
    return {
        "fishNameJa": fish_name,
        "fishNameEn": fish_name,
        "scientificName": "不明",
        "isLegal": False,
        "canTakeHome": False,
        "status": "UNKNOWN",
        "legalExplanation": f"{prefecture}でのこの魚の規制情報を取得できませんでした。現地の漁業協同組合または水産課にお問い合わせください。",
        "minSize": 0,
        "maxSize": None,
        "dailyLimit": None,
        "seasonalBan": [],
        "bannedMonths": [],
        "isEdible": None,
        "edibilityNotes": "食用可能かどうか不明です。専門家に確認してください。",
        "toxicParts": [],
        "preparationWarnings": "不明",
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
        "sourceUrl": None,
        "error": True,
        "errorMessage": error_msg,
        "prefecture": prefecture,
        "generatedAt": datetime.utcnow().isoformat()
    }