# utils/claude_api.py

import os
import json
from anthropic import Anthropic
from typing import Dict
from .fishery_rights_api import get_fishery_rights_by_location


def get_claude_client():
    try:
        api_key = None

        if 'ANTHROPIC_API_KEY' in os.environ:
            api_key = os.environ['ANTHROPIC_API_KEY']
            print("環境変数からAPI Key取得")
        elif os.path.exists('anthropic_key.txt'):
            with open('anthropic_key.txt', 'r', encoding='utf-8') as f:
                api_key = f.read().strip().split('\n')[0].strip()
            print("ファイルからAPI Key取得")

        if not api_key:
            raise Exception("ANTHROPIC_API_KEY not found!")

        if not api_key.startswith('sk-ant-'):
            raise Exception(f"Invalid API key format: {api_key[:15]}...")

        print(f"API Key確認: {api_key[:20]}...")
        return Anthropic(api_key=api_key)

    except Exception as e:
        print(f"Claude API エラー: {e}")
        raise


def identify_and_analyze_fish(image_base64: str, prefecture: str, city: str = None, latitude: float = None,
                              longitude: float = None) -> Dict:
    client = get_claude_client()
    location = f"{city}, {prefecture}" if city else prefecture

    print("漁業権情報取得中...")
    fishery_rights_data = get_fishery_rights_by_location(latitude, longitude) if latitude and longitude else {
        'hasFisheryRights': False,
        'requiresLicense': False,
        'licenseType': 'なし',
        'fishingRightsArea': '自由漁業区域',
        'restrictions': '特になし',
        'cooperativeInfo': '制限なし'
    }

    fishery_info = f"""漁業権情報:
- 漁業権: {"あり" if fishery_rights_data['hasFisheryRights'] else "なし"}
- 遊漁券: {"必要" if fishery_rights_data['requiresLicense'] else "不要"}
- 区域: {fishery_rights_data['fishingRightsArea']}
- 制限: {fishery_rights_data['restrictions']}
- 漁協: {fishery_rights_data['cooperativeInfo']}"""

    prompt = f"""画像の魚を識別し、{location}で持ち帰りが可能かを判定してください。

{fishery_info}

**重要**: 
- 持ち帰り不可の魚は識別結果に含めないでください
- 持ち帰り可能な魚のみ返してください
- 全て日本語で記述

以下のJSON形式で返してください:

{{
  "fishNameJa": "魚の日本語名",
  "isLegal": true,
  "gyogyoken": "{fishery_rights_data['licenseType']}",
  "isEdible": true
}}

持ち帰り不可の場合は:
{{
  "fishNameJa": null,
  "isLegal": false,
  "message": "この魚は持ち帰り禁止です"
}}"""

    try:
        print(f"Claude APIに送信中: {location}")

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0,
            messages=[{
                "role": "user",
                "content": [
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
            }]
        )

        response_text = message.content[0].text.strip()
        print(f"Claude応答受信: {len(response_text)}文字")

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
            print(f"JSON解析成功")
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            print(f"受信データ: {response_text[:200]}")
            return {
                "success": False,
                "error": "解析エラー",
                "message": "魚を識別できませんでした"
            }

        if not data.get('fishNameJa') or not data.get('isLegal'):
            return {
                "success": False,
                "isLegal": False,
                "message": data.get('message', 'この魚は持ち帰り禁止です')
            }

        print(f"識別成功: {data.get('fishNameJa')}")

        return {
            "success": True,
            "fishNameJa": data.get('fishNameJa'),
            "isLegal": data.get('isLegal'),
            "gyogyoken": data.get('gyogyoken'),
            "isEdible": data.get('isEdible')
        }

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": "システムエラー",
            "message": "処理中にエラーが発生しました"
        }