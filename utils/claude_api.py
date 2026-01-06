# utils/claude_api.py

import streamlit as st
import json
from datetime import datetime
from anthropic import Anthropic
from typing import Dict
from utils.fishery_rights_api_file import get_fishery_rights_by_prefecture, get_fishery_rights_by_location


def get_claude_client():
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        return Anthropic(api_key=api_key)
    except Exception as e:
        print(f"Claude API クライアント作成エラー: {e}")
        raise


def generate_fish_info_claude(fish_name: str, prefecture: str, city: str = None, latitude: float = None,
                              longitude: float = None) -> Dict:
    client = get_claude_client()
    location = f"{city}, {prefecture}" if city else prefecture

    print("📍 共同漁業権APIから情報取得中...")

    if latitude and longitude:
        fishery_rights_data = get_fishery_rights_by_location(latitude, longitude)
    else:
        fishery_rights_data = get_fishery_rights_by_prefecture(prefecture)

    fishery_context = f"""
## 実際の共同漁業権情報(海しるAPIより取得):
- 漁業権設定: {"あり" if fishery_rights_data['hasFisheryRights'] else "なし"}
- 遊漁券必要性: {"必要な可能性あり" if fishery_rights_data['requiresLicense'] else "不要"}
- 区域: {fishery_rights_data['fishingRightsArea']}
- 制限事項: {fishery_rights_data['restrictions']}
- 漁協情報: {fishery_rights_data['cooperativeInfo']}
"""

    if fishery_rights_data.get('details'):
        fishery_context += "\n詳細な漁業権情報:\n"
        for detail in fishery_rights_data['details']:
            fishery_context += f"  - 漁業権番号: {detail['rightNumber']}, 漁協: {detail['cooperative']}, 対象: {detail['species']}\n"

    prompt = f"""あなたは日本の釣りと海洋生物の専門家です。{location}における"{fish_name}"という魚について、包括的な情報を日本語で提供してください。

{fishery_context}

上記の実際の共同漁業権情報を必ず考慮して、fishingRightsセクションに正確に反映してください。

必ず以下のJSON構造で、全てのフィールドを埋めて返してください:

{{
  "fishNameJa": "魚の日本語名",
  "fishNameEn": "魚の英語名",
  "scientificName": "学名",
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
  "edibilityNotes": "新鮮なものは刺身で食べられます。",
  "toxicParts": [],
  "preparationWarnings": "内臓は早めに取り除いてください。",
  "description": "この魚は日本近海でよく見られる魚です。",
  "season": ["春", "秋"],
  "peakSeason": "秋から冬にかけて",
  "habitat": "沿岸から沖合の表層",
  "averageSize": "30-40cm",
  "cookingMethods": ["刺身", "塩焼き", "煮付け"],
  "taste": "脂がのっていて濃厚な味わい。",
  "nutrition": "DHA、EPAなどのオメガ3脂肪酸が豊富。",
  "regulationSource": "{prefecture}の漁業調整規則",
  "confidence": "high",
  "sourceUrl": null,
  "fishingRights": {{
    "requiresLicense": {str(fishery_rights_data['requiresLicense']).lower()},
    "licenseType": "{fishery_rights_data['licenseType']}",
    "fishingRightsArea": "{fishery_rights_data['fishingRightsArea']}",
    "restrictions": "{fishery_rights_data['restrictions']}",
    "cooperativeInfo": "{fishery_rights_data['cooperativeInfo']}"
  }}
}}

重要な指示:
1. 全てのテキストは日本語で記述(fishNameEn, scientificName以外)
2. statusは以下のルールで決定: OK(一般的に釣って持ち帰れる), RESTRICTED(サイズ制限や期間制限), PROHIBITED(禁止または絶滅危惧種)
3. minSizeは0以上の数値、制限がない場合は0
4. seasonalBanは日本語の月名の配列
5. bannedMonthsは数値の配列
6. 不明な情報は"不明"または"情報なし"と記載
7. JSONのみを返し、他の説明文は含めない
8. fishingRightsセクションは上記の実際のAPIデータを必ず使用"""

    try:
        print(f"Claude APIに問い合わせ中: {fish_name} @ {location}")

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = message.content[0].text
        print(f"Claude応答を受信: {len(response_text)} 文字")

        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            fish_data = json.loads(response_text)
            print("JSONパース成功")
        except json.JSONDecodeError as je:
            print(f"JSONパースエラー: {je}")
            print(f"受信したテキスト: {response_text[:500]}...")
            return create_fallback_response(fish_name, prefecture, f"JSON解析エラー: {str(je)}")

        required_fields = ['fishNameJa', 'status', 'legalExplanation']
        missing_fields = [field for field in required_fields if field not in fish_data]

        if missing_fields:
            print(f"必須フィールドが不足: {missing_fields}")
            if 'fishNameJa' not in fish_data:
                fish_data['fishNameJa'] = fish_name
            if 'status' not in fish_data:
                fish_data['status'] = 'UNKNOWN'
            if 'legalExplanation' not in fish_data:
                fish_data['legalExplanation'] = '規制情報を確認できませんでした。'

        fish_data["prefecture"] = prefecture
        if city:
            fish_data["city"] = city
        fish_data["fishIdentified"] = fish_name
        fish_data["generatedBy"] = "claude"
        fish_data["generatedAt"] = datetime.utcnow().isoformat()

        if 'fishingRights' in fish_data:
            fish_data['fishingRights'].update({
                'requiresLicense': fishery_rights_data['requiresLicense'],
                'licenseType': fishery_rights_data['licenseType'],
                'fishingRightsArea': fishery_rights_data['fishingRightsArea'],
                'restrictions': fishery_rights_data['restrictions'],
                'cooperativeInfo': fishery_rights_data['cooperativeInfo']
            })
        else:
            fish_data['fishingRights'] = {
                'requiresLicense': fishery_rights_data['requiresLicense'],
                'licenseType': fishery_rights_data['licenseType'],
                'fishingRightsArea': fishery_rights_data['fishingRightsArea'],
                'restrictions': fishery_rights_data['restrictions'],
                'cooperativeInfo': fishery_rights_data['cooperativeInfo']
            }

        print(f"生成完了: {fish_data.get('fishNameJa', fish_name)}")
        return fish_data

    except Exception as e:
        print(f"Claude APIエラー: {e}")
        import traceback
        traceback.print_exc()
        return create_fallback_response(fish_name, prefecture, str(e))


def create_fallback_response(fish_name: str, prefecture: str, error_msg: str = "") -> Dict:
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
        "fishingRights": {
            "requiresLicense": None,
            "licenseType": "不明",
            "fishingRightsArea": "不明",
            "restrictions": "不明",
            "cooperativeInfo": "地元の漁業協同組合にお問い合わせください"
        },
        "error": True,
        "errorMessage": error_msg,
        "prefecture": prefecture,
        "generatedAt": datetime.utcnow().isoformat()
    }