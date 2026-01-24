# utils/claude_api.py

import os
import json
from anthropic import Anthropic
from typing import Dict
from .fishery_rights_api import get_fishery_rights_by_location


def get_claude_client():
    try:
        api_key = None

        if 'ANTHROPIC_API_KEY_TXT' in os.environ:
            api_key = os.environ['ANTHROPIC_API_KEY_TXT']
        elif os.path.exists('anthropic_key.txt'):
            with open('anthropic_key.txt', 'r', encoding='utf-8') as f:
                api_key = f.read().strip().split('\n')[0].strip()

        if not api_key:
            raise Exception("ANTHROPIC_API_KEY_TXT not found!")

        if not api_key.startswith('sk-ant-'):
            raise Exception(f"Invalid API key format: {api_key[:15]}...")

        return Anthropic(api_key=api_key)

    except Exception as e:
        print(f"Claude API error: {e}")
        raise


def identify_and_analyze_fish(image_base64: str, prefecture: str, city: str = None, latitude: float = None,
                              longitude: float = None) -> Dict:
    client = get_claude_client()
    location = f"{city}, {prefecture}" if city else prefecture

    print("Getting fishery rights data...")
    fishery_rights_data = get_fishery_rights_by_location(latitude, longitude) if latitude and longitude else {
        'hasFisheryRights': False,
        'protectedSpecies': [],
        'restrictions': 'None',
        'details': []
    }

    has_fishing_rights = fishery_rights_data.get('hasFisheryRights', False)
    protected_species = fishery_rights_data.get('protectedSpecies', [])
    restrictions = fishery_rights_data.get('restrictions', 'None')

    print(f"Fishing rights: {has_fishing_rights}")
    print(f"Protected species: {protected_species}")
    print(f"Restrictions: {restrictions}")
    protected_species_str = ", ".join(protected_species)
    prompt = f"""Identify the fish in this image. Location: {location}

    Based on your identification, strictly check if the fish belongs to (or is a type of) any of the following restricted categories:
    [{protected_species_str}]

    (Example: If the image is 'Madako' and the list contains 'Tako', set isRestricted to true)

    Return ONLY this JSON format:

    {{
      "fishNameJa": "Japanese fish name",
      "fishNameHira": "Japanese hiragana name",
      "fishNameEn": "English fish name",
      "scientificName": "Scientific name",
      "isEdible": true,
      "isRestricted": boolean,
      "restrictedMatch": "The word from the list that matched (e.g. 'たこ') or null"
    }}

    Important: Always provide fishNameJa, fishNameHira, fishNameEn, scientificName, and isRestricted status."""

    try:
        print(f"Sending to Claude API: {location}")

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

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {
                "success": False,
                "isLegal": False,
                "message": "Failed to identify fish"
            }

        fish_name_ja = data.get('fishNameJa', '')
        fish_name_hira = data.get('fishNameHira', '')
        fish_name_en = data.get('fishNameEn', '')
        scientific_name = data.get('scientificName', '')
        is_edible = data.get('isEdible', True)

        is_protected = data.get('isRestricted', False)

        if not fish_name_hira:
            print("No fish name found")
            return {
                "success": False,
                "isLegal": False,
                "message": "Failed to identify fish"
            }

        print(f"Identified fish: {fish_name_ja} ({fish_name_en})")

        if has_fishing_rights and is_protected:
            print(f"ILLEGAL: Fishing rights exist in this area")
            return {
                "success": False,
                "isLegal": False,
                "fishNameJa": fish_name_ja,
                "fishNameEn": fish_name_en,
                "scientificName": scientific_name,
                "isEdible": is_edible,
                "gyogyoken": restrictions,
                "message": f"Fishing rights area. Taking home prohibited."
            }
        else:
            print(f"LEGAL: No fishing rights in this area")
            return {
                "success": True,
                "isLegal": True,
                "fishNameJa": fish_name_ja,
                "fishNameEn": fish_name_en,
                "scientificName": scientific_name,
                "isEdible": is_edible,
            }

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "isLegal": False,
            "message": "Error occurred during processing"
        }