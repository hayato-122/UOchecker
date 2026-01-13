# utils/claude_api.py

import os
import json
from datetime import datetime
from anthropic import Anthropic
from typing import Dict
import streamlit as st
from .fishery_rights_api import get_fishery_rights_by_prefecture, get_fishery_rights_by_location


def get_claude_client():
    try:
        if 'ANTHROPIC_API_KEY' in os.environ:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
        else:
            raise Exception("ANTHROPIC_API_KEYが見つかりません。")
        
        api_key = api_key.strip()
        
        if not api_key.startswith('sk-ant-'):
            raise Exception(f"Invalid API key format: {api_key[:20]}...")
        
        return Anthropic(api_key=api_key)
    except Exception as e:
        print(f"Claude API クライアント作成エラー: {e}")
        raise


def identify_and_analyze_fish(image_base64: str, prefecture: str, city: str = None, latitude: float = None, longitude: float = None) -> Dict:
    
    if not isinstance(image_base64, str):
        print(f"エラー: image_base64 は文字列である必要があります。受け取った型: {type(image_base64)}")
        return {
            "success": False,
            "error": "画像データエラー",
            "message": "画像データの形式が正しくありません。"
        }
    
    client = get_claude_client()
    location = f"{city}, {prefecture}" if city else prefecture
    
    print("共同漁業権APIから情報取得中...")
    
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
    
    prompt = f"""あなたは日本の釣りと海洋生物の専門家です。

この画像に写っている魚を識別し、{location}における法的規制と詳細情報を日本語で提供してください。

{fishery_context}

**重要**: 全ての回答は日本語で記述してください（fishNameEn, scientificName以外）。

必ず以下のJSON構造で返してください:

{{
  "fishNameJa": "魚の日本語名（例：マサバ、クロマグロ、スズキ）",
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
  "description": "この魚は日本近海でよく見られる魚です。",
  "season": ["春", "秋"],
  "peakSeason": "秋から冬にかけて",
  "habitat": "沿岸から沖合の表層",
  "averageSize": "30-40cm",
  "cookingMethods": ["刺身", "塩焼き", "煮付け", "フライ"],
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

指示:
1. 画像の魚を正確に識別してfishNameJaに記載
2. 魚が識別できない場合は明確にエラーを返す
3. statusの決定: OK（釣って持ち帰れる）、RESTRICTED（制限あり）、PROHIBITED（禁止）
4. 全ての説明文は日本語で記述
5. minSizeは0以上、制限なしなら0
6. 不明な情報は「不明」または「情報なし」
7. JSONのみを返し、説明文は含めない
8. fishingRightsは上記の実際のAPIデータを使用"""

    try:
        print(f"Claude APIに画像を送信中: {location}")
        print(f"画像データ長: {len(image_base64)} 文字")
        
        message_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_base64
                }
            },
            {
                "type": "text",
                "text": prompt
            }
        ]
        
        print("メッセージコンテンツを構築しました")
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": message_content
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
            return {
                "success": False,
                "error": "魚を特定できませんでした",
                "message": "画像が不鮮明か、魚が写っていない可能性があります。\n別の角度から撮影してみてください。"
            }
        
        if 'fishNameJa' not in fish_data or not fish_data['fishNameJa']:
            return {
                "success": False,
                "error": "魚を特定できませんでした",
                "message": "画像から魚を識別できませんでした。\nより鮮明な画像をお試しください。"
            }
        
        required_fields = ['fishNameJa', 'status', 'legalExplanation']
        for field in required_fields:
            if field not in fish_data:
                if field == 'fishNameJa':
                    fish_data['fishNameJa'] = '不明な魚'
                elif field == 'status':
                    fish_data['status'] = 'UNKNOWN'
                elif field == 'legalExplanation':
                    fish_data['legalExplanation'] = '規制情報を確認できませんでした。'
        
        fish_data["prefecture"] = prefecture
        if city:
            fish_data["city"] = city
        fish_data["generatedBy"] = "claude-vision"
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
        
        print(f"生成完了: {fish_data.get('fishNameJa', '不明')}")
        
        return {
            "success": True,
            "fromImage": True,
            "data": fish_data,
            "fishNameJa": fish_data.get('fishNameJa', '不明')
        }
        
    except Exception as e:
        print(f"Claude APIエラー: {e}")
        print(f"エラー型: {type(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": "システムエラー",
            "message": "魚の識別中にエラーが発生しました。もう一度お試しください。"
        }
