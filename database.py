# utils/database.py
# Firebase Firestore統合

import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Optional


# Firebase初期化
if not firebase_admin._apps:
    # TODO: サービスアカウントキーのパスを設定
    cred = credentials.Certificate('firebase_config.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()


def create_cache_key(prefecture: str, fish_name: str) -> str:
    """
    データベース用のユニークなキャッシュキーを作成
    """
    normalized_fish = fish_name.lower().replace(' ', '-')
    normalized_prefecture = prefecture.replace('県', '').replace('府', '').replace('都', '')
    return f"{normalized_prefecture}-{normalized_fish}"


def get_from_cache(cache_key: str) -> Optional[Dict]:
    """
    Firestoreキャッシュから魚のデータを取得
    """
    try:
        doc_ref = db.collection('fish_regulations_cache').document(cache_key)
        doc = doc_ref.get()
        
        if doc.exists:
            # アクセス統計を更新
            doc_ref.update({
                'lastAccessed': firestore.SERVER_TIMESTAMP,
                'accessCount': firestore.Increment(1)
            })
            
            data = doc.to_dict()
            print(f"  ✅ キャッシュで見つかりました（アクセス数: {data.get('accessCount', 0)}回）")
            return data
        
        print("  ❌ キャッシュに見つかりませんでした")
        return None
        
    except Exception as e:
        print(f"  ⚠️ キャッシュ読み取りエラー: {e}")
        return None


def save_to_cache(cache_key: str, fish_info: Dict) -> bool:
    """
    魚のデータをFirestoreキャッシュに保存
    """
    try:
        doc_ref = db.collection('fish_regulations_cache').document(cache_key)
        
        fish_info['id'] = cache_key
        fish_info['createdAt'] = firestore.SERVER_TIMESTAMP
        fish_info['lastAccessed'] = firestore.SERVER_TIMESTAMP
        fish_info['accessCount'] = 1
        
        doc_ref.set(fish_info)
        print(f"  ✅ キャッシュに保存しました: {cache_key}")
        return True
        
    except Exception as e:
        print(f"  ⚠️ キャッシュ保存エラー: {e}")
        return False