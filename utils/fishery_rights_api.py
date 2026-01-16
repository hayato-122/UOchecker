import requests
from typing import Dict, Optional, List
import os

class FisheryRightsAPI:
    BASE_URL = "https://api.msil.go.jp/common-fishery-right2024/v2/MapServer/3/query"

    def __init__(self):
        api_key = os.environ.get('OCP_API_KEY_TXT')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'UOChecker/1.0',
            'Ocp-Apim-Subscription-Key': api_key
        })

    def search_by_location(self, latitude: float, longitude: float, radius: int = 3000) -> Optional[List[Dict]]:
        try:
            # distance=経度,緯度,距離
            params = {
                'f': 'json',
                'distance': f"{longitude},{latitude},{radius}",
                'units': 'esriSRUnit_Meter',
                'geometry': f"{longitude},{latitude}",
                'geometryType': 'esriGeometryPoint',
                'inSR': '4326',
                'spatialRel': 'esriSpatialRelIntersects',
                'outFields': '第一種共同漁業権',
                'where': "第一種共同漁業権 IS NOT NULL AND 第一種共同漁業権 <> ' '",
                'returnGeometry': 'false'
            }

            print(f"共同漁業権API(v2)呼び出し: {longitude}, {latitude}")
            response = self.session.get(self.BASE_URL, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                print(f"✅ 共同漁業権API: {len(features)}件の漁業権を発見")
                return features
            else:
                print(f"⚠️ APIエラー: {response.status_code} {response.text}")
                return None
        except Exception as e:
            print(f"⚠️ 例外発生: {e}")
            return None

    def extract_fishery_info(self, fishery_data: List[Dict]) -> Dict:
        """
        APIから取得した周辺の漁業権データの最も近い情報から、
        第一種共同漁業権の保護魚種ををまとめる関数。
        """

        # 漁業権データが見つけられなかった場合空データを返す
        if not fishery_data:
            return {
                'hasFisheryRights': False,
                'protectedSpecies': [],
                'restrictions': '特になし',
                'details': []
            }

        closest_feature = fishery_data[0]

        # ArcGIS形式のデータ構造から属性情報を取得
        attr = closest_feature.get('attributes', {})
        # 第一種共同漁業権の項目を取得
        val = attr.get('第一種共同漁業権')

        protected_species_list = []
        if val and val.strip():
            # 全角「、」を半角「,」に置換して分割して前後の空白を削除
            raw_species = val.replace('、', ',').split(',')
            # 空文字を除去してあいうえお順に並び替える
            protected_species_list = sorted([s.strip() for s in raw_species if s.strip()])

        details = [{
            'species': val.strip() if val else "種別不明"
        }]

        # 漁業権の魚種一覧表示　デバッグ用
        print(f"発見された保護魚種 ({protected_species_list})")

        if protected_species_list:
            restrictions = f"最も近い漁業権の対象: {'、'.join(protected_species_list)}"
        else:
            restrictions = "最も近い場所に漁業権はありますが、対象種が記載されていません。"

        return {
            # 保護されている魚種が1つ以上あれば「漁業権あり(True)」と判定
            'hasFisheryRights': len(protected_species_list) > 0,
            # AI（Claude）に渡すための、最も近い漁業権の魚種一覧
            'protectedSpecies': protected_species_list,
            # 画面表示用の日本語テキスト
            'restrictions': restrictions,
            # 詳細データ（1件分）
            'details': details
        }


def get_fishery_rights_by_location(latitude: float, longitude: float) -> Dict:
    api = FisheryRightsAPI()
    fishery_data = api.search_by_location(latitude, longitude)
    return api.extract_fishery_info(fishery_data)