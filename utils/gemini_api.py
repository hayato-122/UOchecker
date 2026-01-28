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
        # Advanced Fish Identification & Safety Analysis Prompt

    ## Background
    You are a world-renowned Ichthyologist and a specialist in Food Safety and Marine Resource Management.
    Your task is to analyze an input image of a fish, identify the species with high precision, and determine its edibility, toxicity, and legal restrictions.
    **You excel at distinguishing look-alike species by analyzing body shape (aspect ratio) and specific color markers.**

    ## Instructions
    Analyze the input and perform the following steps. Output ONLY the raw JSON object based on your analysis.

    1.  **Species Identification (Discriminative Analysis)**: 
        -   Identify the fish species.

        -   **CRITICAL CHECK 1: Pufferfish (*Takifugu*)**:
            -   **Target**: *Takifugu poecilonotus* (Komon-fugu) vs *Takifugu niphobles* (Kusa-fugu).
            -   **Visual Rule**:
                -   **Komon**: Spots are **irregular, varying in size, and often vermiculated (worm-eaten shape/fused)**. White edges on fins may be present.
                -   **Kusa**: Spots are **small, uniform, distinct, and perfectly round**.
            -   **Bias Correction**: **Do NOT default to Kusa-fugu.** If you see ANY spot fusion or irregularity, identify as *Takifugu poecilonotus*.

        -   **CRITICAL CHECK 2: Blue/Green Fish Complex (Trevally vs Jobfish)**:
            -   **Target**: Distinguish *Caranx* (Trevally) from *Aprion* (Jobfish).
            -   **Step A: Check Body Shape (Crucial)**:
                -   **Elongated/Torpedo-shaped**: Likely **Aochibiki** (*Aprion virescens*). Look for a deep groove in front of the eyes.
                -   **Compressed/Flat/High-body**: Likely **Trevally** (*Caranx*).
            -   **Step B: Check Color Markers**:
                -   **Aochibiki**: Solid greenish-grey or blue-grey. **NO distinct electric blue speckles.**
                -   **Kasumi-aji**: **Electric blue spots/speckles** on body and bright blue fins.
                -   **Gingame-aji**: Small distinct black spot on operculum + NO blue spots.
            -   **Decision**: 
                -   If torpedo-shaped + no blue spots -> **Aochibiki**.
                -   If flat body + blue spots -> **Kasumi-aji**.
                -   If flat body + gill spot -> **Gingame-aji**.

        -   **CRITICAL CHECK 3: Shellfish (Abalone vs Tokobushi)**:
            -   **Target**: *Haliotis* spp.
            -   **Rule**: Priority on structure. **Raised/Chimney-like pores** = Awabi. **Flat/Flush pores** = Tokobushi.

    2.  **Name Extraction**: Provide the following names:
        -   `fishNameJa`: Standard Japanese name (Standard Wamei).
        -   `fishNameHira`: Japanese name in Hiragana (for pronunciation).
        -   `fishNameEn`: Common English name.
        -   `scientificName`: Scientific binomial name.

    3.  **Safety Assessment**:
        -   Determine if the fish is generally considered edible (`isEdible`).
        -   Strictly check for poison (`isPoisonous`).
            -   *Note*: Pufferfish are poisonous (TTX).
            -   *Note*: Large Aochibiki and Trevally in tropical waters *can* carry Ciguatera, but are generally edible in main Japanese markets. Follow "Safety First" if uncertain.
        -   **Safety Protocol**: If uncertain, err on the side of caution.

    4.  **Regulatory Check (CRITICAL)**:
        -   **LOCAL REGULATION CHECK**: Verify if the identified species corresponds to any name in this restricted list: [{protected_species_str}].
        -   **General Check**: Check if the fish is restricted under CITES, the IUCN Red List, or Japanese Fishery Laws.
        -   **Action**: If the species (or its family/aliases) matches the list or general laws, set `isRestricted` to `true`. Otherwise `false`.

    5.  **Formatting**: Output the result strictly as a valid JSON object matching the defined schema. Do not include markdown formatting (like ```json ... ```) or explanatory text.

    ## Parameters
    -   **Geographic Context**: Japanese waters and markets.
    -   **Toxicity Threshold**: Strict.
    -   **Output Language**: Values for names must correspond to the specific language requested.

    ## Output Format
    ```json
    {{
      "fishNameJa": "String (Standard Japanese Name)",
      "fishNameHira": "String (Hiragana)",
      "fishNameEn": "String (English Name)",
      "scientificName": "String (Scientific Name)",
      "isEdible": true,
      "isPoisonous": false,
      "isRestricted": false
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