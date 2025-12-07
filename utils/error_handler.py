# utils/location.py
# 位置情報変換と正規化

def get_prefecture_name(raw_prefecture: str) -> str:
    """
    生の都道府県文字列を正規化
    
    例:
    "兵庫" → "兵庫県"
    "Hyogo" → "兵庫県"
    "Hyōgo Prefecture" → "兵庫県"
    """
    
    # 既に正しい形式の場合
    if raw_prefecture.endswith(('県', '府', '都', '道')):
        return raw_prefecture
    
    # 英語名から日本語への変換
    prefecture_map = {
        # 関西
        'hyogo': '兵庫県',
        'hyōgo': '兵庫県',
        'osaka': '大阪府',
        'ōsaka': '大阪府',
        'kyoto': '京都府',
        'kyōto': '京都府',
        'nara': '奈良県',
        'wakayama': '和歌山県',
        'shiga': '滋賀県',
        
        # 関東
        'tokyo': '東京都',
        'tōkyō': '東京都',
        'kanagawa': '神奈川県',
        'saitama': '埼玉県',
        'chiba': '千葉県',
        'ibaraki': '茨城県',
        'tochigi': '栃木県',
        'gunma': '群馬県',
        
        # 中部
        'aichi': '愛知県',
        'shizuoka': '静岡県',
        'gifu': '岐阜県',
        'mie': '三重県',
        'nagano': '長野県',
        'yamanashi': '山梨県',
        'niigata': '新潟県',
        'toyama': '富山県',
        'ishikawa': '石川県',
        'fukui': '福井県',
        
        # 東北
        'miyagi': '宮城県',
        'fukushima': '福島県',
        'yamagata': '山形県',
        'akita': '秋田県',
        'iwate': '岩手県',
        'aomori': '青森県',
        
        # その他主要
        'hokkaido': '北海道',
        'hokkaidō': '北海道',
        'hiroshima': '広島県',
        'fukuoka': '福岡県',
        'okinawa': '沖縄県',
    }
    
    # 小文字に変換して検索
    raw_lower = raw_prefecture.lower().strip()
    
    # Prefecture, Prefectural などを削除
    raw_lower = raw_lower.replace(' prefecture', '').replace('prefecture', '')
    raw_lower = raw_lower.replace(' prefectural', '').replace('prefectural', '')
    raw_lower = raw_lower.strip()
    
    # マッピングから検索
    if raw_lower in prefecture_map:
        return prefecture_map[raw_lower]
    
    # 日本語のまま「県」を追加
    if not raw_prefecture.endswith(('県', '府', '都', '道')):
        # 特殊ケース
        if raw_prefecture in ['東京', 'Tokyo']:
            return '東京都'
        elif raw_prefecture in ['大阪', 'Osaka']:
            return '大阪府'
        elif raw_prefecture in ['京都', 'Kyoto']:
            return '京都府'
        elif raw_prefecture in ['北海道', 'Hokkaido']:
            return '北海道'
        else:
            return f"{raw_prefecture}県"
    
    return raw_prefecture


def prefecture_from_city(city: str) -> str:
    """
    市区町村名から都道府県名を推測（後方互換性のため残す）
    """
    city_to_prefecture = {
        "神戸": "兵庫県",
        "姫路": "兵庫県",
        "明石": "兵庫県",
        "大阪": "大阪府",
        "京都": "京都府",
        "奈良": "奈良県",
        "和歌山": "和歌山県",
        "滋賀": "滋賀県",
        "東京": "東京都",
        "横浜": "神奈川県",
        "名古屋": "愛知県",
    }
    
    return city_to_prefecture.get(city, f"{city}県")