# utils/fishery_rights_api_file.py

import requests
from typing import Dict, Optional, List


class FisheryRightsAPI:
    
    BASE_URL = "https://api.msil.go.jp"
    API_ENDPOINT = "/msil/v1/commonFisheryRight2024"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'UOChecker/1.0'
        })
    
    def search_by_location(self, latitude: float, longitude: float, radius: int = 5000) -> Optional[List[Dict]]:
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'radius': radius
            }
            
            url = f"{self.BASE_URL}{self.API_ENDPOINT}"
            print(f"共同漁業権API呼び出し: lat={latitude}, lon={longitude}, radius={radius}m")
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    features = data.get('features', [])
                    print(f"✅ 共同漁業権API: {len(features)}件の漁業権を発見")
                    return features
                elif isinstance(data, list):
                    print(f"✅ 共同漁業権API: {len(data)}件の漁業権を発見")
                    return data
                else:
                    print("⚠️ 共同漁業権API: データ形式が不正")
                    return None
            elif response.status_code == 404:
                print("📍 共同漁業権API: この地点には漁業権が設定されていません")
                return []
            else:
                print(f"⚠️ 共同漁業権API エラー: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("⚠️ 共同漁業権API: タイムアウト")
            return None
        except Exception as e:
            print(f"⚠️ 共同漁業権API エラー: {e}")
            return None
    
    def search_by_prefecture(self, prefecture: str) -> Optional[List[Dict]]:
        try:
            clean_pref = prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', '')
            
            params = {
                'prefecture': clean_pref
            }
            
            url = f"{self.BASE_URL}{self.API_ENDPOINT}"
            print(f"共同漁業権API呼び出し: prefecture={clean_pref}")
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    features = data.get('features', [])
                    print(f"✅ 共同漁業権API: {prefecture}で{len(features)}件の漁業権を発見")
                    return features
                elif isinstance(data, list):
                    print(f"✅ 共同漁業権API: {prefecture}で{len(data)}件の漁業権を発見")
                    return data
                else:
                    print("⚠️ 共同漁業権API: データ形式が不正")
                    return None
            else:
                print(f"⚠️ 共同漁業権API エラー: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ 共同漁業権API エラー: {e}")
            return None
    
    def extract_fishery_info(self, fishery_data: List[Dict]) -> Dict:
        if not fishery_data:
            return {
                'hasFisheryRights': False,
                'requiresLicense': False,
                'licenseType': 'なし',
                'fishingRightsArea': '自由漁業区域',
                'restrictions': '特になし',
                'cooperativeInfo': '地元漁業協同組合に確認することを推奨します',
                'details': []
            }
        
        details = []
        cooperatives = set()
        restricted_species = set()
        
        for feature in fishery_data:
            properties = feature.get('properties', {}) if isinstance(feature, dict) else {}
            
            right_number = properties.get('rightNumber') or properties.get('免許番号') or properties.get('漁業権番号')
            cooperative = properties.get('cooperative') or properties.get('漁協名') or properties.get('組合名')
            
            if cooperative:
                cooperatives.add(cooperative)
            
            species = properties.get('species') or properties.get('対象魚種') or properties.get('漁業種類')
            if species:
                if isinstance(species, str):
                    restricted_species.add(species)
                elif isinstance(species, list):
                    restricted_species.update(species)
            
            expiry = properties.get('expiryDate') or properties.get('有効期限')
            
            detail = {
                'rightNumber': right_number or '不明',
                'cooperative': cooperative or '不明',
                'species': species or '不明',
                'expiryDate': expiry or '不明'
            }
            details.append(detail)
        
        coop_info = '、'.join(cooperatives) if cooperatives else '地元漁業協同組合'
        
        restrictions = []
        if restricted_species:
            species_list = '、'.join(list(restricted_species)[:5])
            restrictions.append(f"対象魚種: {species_list}")
        
        restrictions.append("遊漁の場合は事前に地元漁協に確認してください")
        
        return {
            'hasFisheryRights': True,
            'requiresLicense': True,
            'licenseType': '共同漁業権区域(遊漁券が必要な場合があります)',
            'fishingRightsArea': f'共同漁業権設定区域({len(fishery_data)}件)',
            'restrictions': '、'.join(restrictions),
            'cooperativeInfo': f'{coop_info}に事前確認を推奨',
            'details': details[:3]
        }


def get_fishery_rights_by_location(latitude: float, longitude: float) -> Dict:
    api = FisheryRightsAPI()
    fishery_data = api.search_by_location(latitude, longitude)
    return api.extract_fishery_info(fishery_data)


def get_fishery_rights_by_prefecture(prefecture: str) -> Dict:
    api = FisheryRightsAPI()
    fishery_data = api.search_by_prefecture(prefecture)
    return api.extract_fishery_info(fishery_data)
