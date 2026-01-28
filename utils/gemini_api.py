# utils/gemini_api.py

import os
import json
import google.generativeai as genai
from typing import Dict
from .fishery_rights_api import get_fishery_rights_by_location


def get_gemini_client():
    try:
        api_key = None

        if 'GEMINI_API_KEY_TXT' in os.environ:
            api_key = os.environ['GEMINI_API_KEY_TXT']
        elif os.path.exists('gemini_api_key.txt'):
            with open('gemini_api_key.txt', 'r', encoding='utf-8') as f:
                api_key = f.read().strip().split('\n')[0].strip()

        if not api_key:
            raise Exception("GEMINI_API_KEY_TXT not found!")
        if not api_key:
            raise Exception("GOOGLE_API_KEY not found! 環境変数またはgoogle_api_key.txtを設定してください。")

        genai.configure(api_key=api_key)

    except Exception as e:
        print(f"Gemini API Config error: {e}")
        raise


def identify_and_analyze_fish(image_bytes: bytes, prefecture: str, city: str = None, latitude: float = None,
longitude: float = None) -> Dict:
    get_gemini_client()
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

    prompt = f"""
    Act as a forensic ichthyologist.
    The user believes this fish might be **Takifugu poecilonotus (Komonfugu)**, but it is often confused with **Takifugu alboplumbeus (Kusafugu)**.
    Your task is to verify this hypothesis with extreme skepticism towards "Kusafugu".

    **CRITICAL DIFFERENTIATION LOGIC**:

    1. **The "Humeral Spot" Verification (The Shadow Trap)**:
       - Locate the area strictly behind the pectoral fin.
       - **Kusafugu**: MUST have a **distinct, deep black, round spot** usually edged in white.
       - **Komonfugu**: Has NO spot, or only a vague, irregular gray blur.
       - **WARNING**: Do NOT confuse a shadow, a fold in the skin, or dirt with a biological "spot".
       - **Rule**: If the spot is not 100% distinct and clearly pigmented (not just a dark area), you MUST rule out Kusafugu based on this feature.

    2. **Dorsal Pattern Analysis (The Tie-Breaker)**:
       - Look at the white spots on the back.
       - **Kusafugu**: Spots are distinct, separate, round dots (like a starry sky). They do NOT touch each other.
       - **Komonfugu**: Spots are **irregular, variable in size, and often merge/connect** (vermicular/worm-eaten shape).
       - **Instruction**: If you see ANY spots connecting or varying wildly in size, it is Komonfugu.

    3. **Final Verdict Formulation**:
       - If the humeral spot is missing/ambiguous AND the back spots are irregular -> **Identify as Takifugu poecilonotus (Komonfugu)**.
       - Only identify as Kusafugu if there is a undeniable humeral spot AND separate round dorsal dots.

    **Legal & Safety**:
    - Check against: [{protected_species_str}]
    - Note: Both species are poisonous (Tetrodotoxin).

    Respond ONLY with this JSON object:
    {{
      "morphologicalAnalysis": "Explain your reasoning aggressively. (e.g., 'Identified as Komonfugu because the area behind the pectoral fin lacks a distinct white-edged black spot (likely just a shadow), and the white spots on the back are irregular in size/shape, which is characteristic of T. poecilonotus.')",
      "fishNameJa": "Japanese fish name",
      "fishNameHira": "Japanese hiragana name",
      "fishNameEn": "English fish name",
      "scientificName": "Scientific name",
      "isEdible": true,
      "isPoisonous": true,
      "isRestricted": boolean,
      "restrictedMatch": "The word from the list that matched or null"
    }}
    """
    safety_settings = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    }
    try:
        print(f"Sending to Gemini API: {location}")

        model = genai.GenerativeModel("gemini-3-flash-preview")

        response = model.generate_content(
            contents=[
                prompt,{
            "mime_type": "image/jpeg",
            "data": image_bytes
            }
                ],
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
            safety_settings = safety_settings
        )

        try:
            data = json.loads(response.text)
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
        is_poisonous = data.get('isPoisonous', False)

        is_protected = data.get('isRestricted', False)

        if not fish_name_hira:
            print("No fish name found")
            return {
                "success": False,
                "isLegal": False,
                "message": "Failed to identify fish"
            }

        print(f"Identified fish: {fish_name_ja} ({fish_name_en})")
        print(f"Poisonous: {is_poisonous}")

        if has_fishing_rights and is_protected:
            print(f"ILLEGAL: Fishing rights exist in this area")
            return {
                "success": False,
                "isLegal": False,
                "fishNameJa": fish_name_ja,
                "fishNameEn": fish_name_en,
                "scientificName": scientific_name,
                "isEdible": is_edible,
                "isPoisonous": is_poisonous,
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
                "isPoisonous": is_poisonous,
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