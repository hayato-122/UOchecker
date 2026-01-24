# frontend.py
# 実行コマンド　streamlit run frontend.py
import streamlit as st  # GUI作成、サーバー作成
from PIL import Image, ImageOps  # 画像の取り扱い
import folium  # mapデータ
from streamlit_folium import st_folium  # map表示
from folium.plugins import LocateControl # 現在地取得用
from geopy.geocoders import ArcGIS  # マップ情報から緯度経度を取得
import base64  # 画像の形式を変換
import requests  # API使用
import io  # bytes処理用
import time

from backend import identify_and_check_fish  # backedの関数呼び出し

# geolocatorインスタンス作成　update_addressの逆ジオコーディングを実行するため
geolocator = ArcGIS(user_agent="uochecker-app-v1.0", timeout=10)


def update_address(location_list):
    """
    Args:
        location_list: 緯度 軽度

    Returns:
        緯度 経度の座標の県、街

    """
    # 緯度経度に分割
    lat, lng = location_list

    # HeartRails GeoAPIのための設定
    url = " https://geoapi.heartrails.com/api/json?method=searchByGeoLocation"
    params = {
        "method": "searchByGeoLocation",
        "x": lng,  # 経度
        "y": lat  # 緯度
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        # データ構造の確認
        if "response" in data and "location" in data["response"]:
            loc = data["response"]["location"][0]  # 最も近い住所を取得

            # 日本語住所を結合
            address_text = f"{loc['prefecture']}{loc['city']}{loc['town']}"

            # 住所を保存
            st.session_state.marker_address = address_text
            st.session_state.current_prefecture = loc['prefecture']
            st.session_state.current_city = loc['city']
            return address_text

        else:
            st.session_state.marker_address = "住所不明（海上など）"
            st.session_state.current_prefecture = ""
            st.session_state.current_city = ""
            return "住所不明"
    except Exception as e:
        print(f"HeartRails Error: {e}")
        st.session_state.marker_address = "住所取得エラー"
        st.session_state.current_prefecture = ""
        st.session_state.current_city = ""
        return None

def load_history(load_history):
    # マーカーの位置を表示
    load_location = [load_history["lat"], load_history["lng"]]
    st.session_state.center = load_location
    st.session_state.marker_location = load_location
    st.session_state.zoom = 15

    # 住所情報の更新
    st.session_state.marker_address = load_history["address"]
    st.session_state.current_prefecture = load_history["prefecture"]
    st.session_state.current_city = load_history["city"]

    st.session_state.search_error = None
    st.rerun()

@st.cache_resource# 動画をキャッシュ化
def get_base64_video(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# streamlitのページ設定
st.set_page_config(page_title="UOチェッカー", layout="wide")

# webサイト初回起動時の初期設定
if "center" not in st.session_state:  # マップ表示の中央の初期設定
    st.session_state.center = [34.694659, 135.194954]  # 三ノ宮駅
if "marker_location" not in st.session_state:  # マーカーの初期位置の初期設定
    st.session_state.marker_location = [34.694659, 135.194954]  # 三ノ宮駅
if "marker_auto" not in st.session_state: # マーカーの自動取得のフラグ設定
    st.session_state.marker_auto = True
if "marker_address" not in st.session_state:  # マーカーの位置の住所の初期設定
    update_address(st.session_state.marker_location)  # 関数呼び出しで逆ジオコーディング
if "current_prefecture" not in st.session_state:  # 都道府県を保存するセッションの初期設定
    st.session_state.current_prefecture = ""
if "current_city" not in st.session_state:  # 市区町村を保存するセッションの初期設定
    st.session_state.current_city = ""
if "zoom" not in st.session_state:  # マップのズーム倍率の初期設定
    st.session_state.zoom = 8
if "uploaded_file" not in st.session_state:  # アップロードファイルの初期設定
    st.session_state.uploaded_file = None
if "result" not in st.session_state:  # 結果の初期設定
    st.session_state.result = None
if "search_map" not in st.session_state:
    st.session_state.search_map = None
if "search_error" not in st.session_state:  # 検索エラーメッセージの初期設定
    st.session_state.search_error = None
if "search_history" not in st.session_state:  # 検索履歴リストの初期化
    st.session_state.search_history = []
if "run_process" not in st.session_state:
    st.session_state.run_process = False

# 画像を選択画像の読み込み
with open("image/img_preview_text.png", "rb") as img_preview_text_img:
    img_preview_text_data = img_preview_text_img.read()
    img_preview_text_base64 = base64.b64encode(img_preview_text_data).decode("utf-8")

# ロード画面用の事前読み込み
wave_load_base64 = get_base64_video("image/wave_load.mp4")

wave_load_html = f"""
                    <style>
                    .loader-overlay {{
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100vw;
                        height: 100vh;
                        background-color: rgba(0, 0, 0, 0.85);
                        z-index: 999999;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        backdrop-filter: blur(0.3rem);
                    }}
                    .loader-text {{
                        color: white;
                        font-size: 1.5rem;
                        font-weight: bold;
                        margin-top: 1.25rem;
                        text-shadow: 0 0 0.625rem rgba(255,255,255,0.5);
                    }}
                    </style>
                    <div class="loader-overlay">
                        <video autoplay loop muted playsinline style="width: 9.375rem; height: auto;">
                            <source src="data:video/mp4;base64,{wave_load_base64}" type="video/mp4">
                            お使いのブラウザは動画タグをサポートしていません。
                        </video>
                        <div class="loader-text">魚を識別中...</div>
                    </div>
                    """

# ページ全体のCSS設定
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

    /* 全体の背景画像設定 */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* スクロールバーを非表示にする */
    * {
        scrollbar-width: none;
    }
    
    /* ヘッダーを非表示 */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    /* 右上のツールバーを非表示 */
    div[data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 上部の色付きラインを非表示 */
    div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    /* "Running" や "Stop" を非表示 */
    div[data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* フッター削除 */
    footer {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    /* メインコンテンツの位置調整 */
    .block-container {
        padding-top: 0rem !important;
    }

    /* 余白削除とフルワイド化 */

    /* メインコンテナのパディングを削除 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
    }

    /* カラム間の隙間をに0にする */
    [data-testid="stHorizontalBlock"] {
        gap: 0rem !important;
    }

    /* 検索ボタン等には隙間を戻す */
    [data-testid="stColumn"] [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }

    /* カラム設定 左側（メイン） */
    [data-testid="stColumn"]:nth-of-type(1) {
        background: linear-gradient(90deg, rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.35));
        padding: 3rem 2rem;
        min-height: 100vh;
        margin-top: -2rem;
        user-select: none !important;
        -webkit-user-select: none !important;
    }

    /* カラム設定 右側（メイン） */
    [data-testid="stColumn"]:nth-of-type(2) {
        background: rgba(0, 0, 0, 0.76);
        padding: 3rem 2rem;
        min-height: 100vh;
        margin-top: -2rem;
        user-select: none !important;
        -webkit-user-select: none !important;
    }

    /* 内部カラムのデザインリセット */
    [data-testid="stColumn"] [data-testid="stColumn"] {
        background: transparent !important;
        padding: 0 !important;
        min-height: 0 !important;
    }


    /* 文字色を白に統一 */
    h1, h2, h3, p, div, label, span {
        font-family: 'Noto Sans JP', sans-serif !important;
        text-shadow: 0.06rem 0.06rem 0.125rem rgba(0,0,0,0.5);
    }

    /* ファイルアップローダーのCSS */

    [data-testid="stFileUploader"] section {
        visibility: hidden;
    }

    [data-testid="stFileUploader"] ul {
        display: none !important;
    }

    [data-testid="stFileUploader"] small {
        display: none !important;
    }

    /* CSSで画像選択ボタンを作成 */
    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
        visibility: visible;
        position: relative;
        width: 30vw;
        height: 10rem;
        color: transparent !important;
        background-color: transparent !important;
        
        border: none !important; 
        background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='15' ry='15' stroke='rgba(255, 255, 255, 0.5)' stroke-width='6' stroke-dasharray='25' stroke-dashoffset='0' stroke-linecap='square'%3e%3canimate attributeName='stroke-dashoffset' from='100' to='0' dur='4s' repeatCount='indefinite' /%3e%3c/rect%3e%3c/svg%3e");
        background-size: 100% 100%;
        background-repeat: no-repeat;

        border-radius: 1rem;
        font-size: 1.2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin: 0.5vw auto 0 auto;
        transform: translateX(-7.5vw);
        transition: 0.3s;
    }

    /* ホバー時に色を変える場合 */
    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        /* ホバー時に枠の色をオレンジに */
        background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='15' ry='15' stroke='%23ff7b00' stroke-width='6' stroke-dasharray='25' stroke-dashoffset='0' stroke-linecap='square'%3e%3canimate attributeName='stroke-dashoffset' from='100' to='0' dur='2s' repeatCount='indefinite' /%3e%3c/rect%3e%3c/svg%3e");
    }

    /* 携帯用 */
    @media (max-width: 600px) {
        [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
            width: 80vw;
            transform: translateX(-3vw);
        }

        /* 右カラムのマージン削除 */
        [data-testid="stColumn"]:nth-of-type(2) {
            margin-top: 0 !important;
        }
        
        iframe[title="streamlit_folium.st_folium"] {
        height: 250px !important;
    }
}

    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-color: #ff7b00;
    }

    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]::before {
    content: '📷';
    position: absolute;
    top: 35%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 4rem;
    color: #ccc !important;
}

    /* ボタン全体の基本設定 */
    div.stButton > button {
        border-radius: 0.625rem;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
    }

    /* Primaryボタン */
    div.stButton > button[kind="primary"] {
        background-color: #ff7b00;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #e06c00;
        color: white;
    }

    /* Secondaryボタン */
    div.stButton > button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.05); /* うっすら背景 */
        color: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.2); /* 薄い枠線 */
        padding: 0.4rem 1rem;
        text-align: left; /* 文字を左寄せ */
        display: flex;
        justify-content: flex-start; /* アイコンと文字を左側に */
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.2); /* ホバー時は少し明るく */
        border-color: rgba(255, 255, 255, 0.5);
        color: #ff7b00; /* 文字色をアクセントカラーに */
        padding-left: 1.5rem !important;
    }

    /* テキスト入力フォーム */
    div[data-baseweb="input"] {
        background-color: rgba(0, 0, 0, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    input {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <style>
    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]::after {{
    content: "";
    position: absolute;
    top: 80%;
    left:55%;
    transform: translate(-50%, -50%);
    
    width: 90%;
    height: 50%;
    
    background-image: url("data:image/png;base64,{img_preview_text_base64}");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    z-index: 2;
}}
    </style>
    """,
    unsafe_allow_html=True
)

# メインレイアウト
col_main_left, col_main_right = st.columns([1, 1], gap="small")  # 1:1の比率に設定

# 左カラム タイトル表示と画像プレビュー表示
with col_main_left:
    # タイトル表示
    # タイトルロゴ画像を読み込んでbase64形式に変換
    with open("image/title_logo.png", "rb") as title_logo_img:
        title_logo_data = title_logo_img.read()
        title_logo_base64 = base64.b64encode(title_logo_data).decode("utf-8")
    # サブタイトル画像を読み込んでbase64形式に変換
    with open("image/title_sub.png", "rb") as title_sub_img:
        title_sub_data = title_sub_img.read()
        title_sub_base64 = base64.b64encode(title_sub_data).decode("utf-8")

    st.markdown(
        f"""
    <div style="text-align: center; margin-top: 0rem; margin-bottom: 2rem; display: flex; flex-direction: column; align-items: center; gap: 1rem;">
        <img src="data:image/gif;base64,{title_logo_base64}" style="width: 50rem;pointer-events: none; -webkit-user-drag: none;">
        <img src="data:image/gif;base64,{title_sub_base64}" style="width: 30rem;pointer-events: none; -webkit-user-drag: none;">
    </div>
        """,
        unsafe_allow_html=True,
    )
    # 画像プレビュー表示
    if st.session_state.uploaded_file is None:  # 画像がアップロードされていない場合
        col_up_left, col_up_center, col_up_right = st.columns([1, 3, 1])
        with col_up_center:
            # 画像プレビュー表示
            if st.session_state.uploaded_file is None:  # 画像がアップロードされていない場合
                col_up_left, col_up_center, col_up_right = st.columns([1, 3, 1])
                with col_up_center:
                    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])
                    if uploaded_file is not None:
                        st.session_state.uploaded_file = uploaded_file
                        st.rerun()
    else:  # 画像がアップロードされた場合
        try:
            image = Image.open(st.session_state.uploaded_file)  # 画像を読み込み
            col_image_left, col_image_center, col_image_right = st.columns([1, 3, 1])  # 画像を中央に揃える
            with col_image_center:  # 中央に画像を表示
                st.image(
                    image,
                    caption="",
                    width="stretch",
                )
                if st.button("別の画像を選択", use_container_width=True,type="primary"):
                    st.session_state.uploaded_file = None
                    st.session_state.result = None
                    st.rerun()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
            st.session_state.uploaded_file = None

# 右カラム マップ表示　結果表示
with col_main_right:
    if st.session_state.result is None:
        st.markdown(
            """
            <div style="padding: 1.5rem; margin-bottom: 3rem; margin-top: -2.5rem; border-bottom: 0.06rem solid rgba(255,255,255,0.3);">
                <p style="text-align:center; margin:0; font-weight:bold; color: white;font-size:1.2rem; ">📍 場所を指定してください</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        with st.container():
            # マップ表示
            # 検索機能
            col_search_in, col_search_btn = st.columns([6, 2])
            with col_search_in:  # マップ検索入力欄表示
                st.markdown(
                    """
                    <style>                
                    div[data-testid="stTextInput"] {
                        margin-top: -1rem;
                    }
                    
                    div[data-testid="stTextInput"] input {
                        background-color: 262730;
                        color: #FFFFFF;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                search_map = st.text_input(
                    "地名検索", placeholder="例：西宮駅", label_visibility="collapsed"
                )
            with col_search_btn:  # 検索ボタン表示
                search_clicked = st.button("検索", type="primary")
                if (search_clicked or search_map) and search_map and search_map != st.session_state.search_map:
                    st.session_state.search_map = search_map
                    st.session_state.search_error = None

                    # 重複チェック
                    search_location = next((item for item in st.session_state.search_history if item["name"] == search_map), None)
                    if search_location: # 履歴にある場合呼び出し
                        load_history(search_location)
                    else: # 履歴にない場合登録
                        location = None
                        try:
                            location = geolocator.geocode(search_map)
                        except Exception as e:
                            st.error(f"エラーが発生しました: {e}")
                        if location:
                            new_location = [location.latitude, location.longitude]
                            st.session_state.center = new_location
                            st.session_state.marker_location = new_location
                            st.session_state.zoom = 15
                            update_address(st.session_state.marker_location)

                            # 履歴登録
                            if search_map:
                                # 履歴を住所名、緯度、経度で保存
                                new_history = {
                                    "name": search_map,
                                    "lat": location.latitude,
                                    "lng": location.longitude,
                                    "address": st.session_state.marker_address,
                                    "prefecture": st.session_state.current_prefecture,
                                    "city": st.session_state.current_city
                                }

                                # 履歴をセッションに保存
                                st.session_state.search_history.insert(0, new_history)
                                # 履歴が3件を超えたら古い履歴から削除
                                if len(st.session_state.search_history) > 3:
                                    st.session_state.search_history.pop()
                            st.rerun()
                        else:
                            st.session_state.search_error = f"「{search_map}」は見つかりませんでした。別の地名で試してください。"

            # マップ表示コンテナ
            with st.container():
                map_preview = folium.Map(
                    location=st.session_state.center,
                    zoom_start=st.session_state.zoom,
                    tiles="https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
                    attr="Google Maps",
                )
                if st.session_state.marker_auto:
                    st.session_state.marker_auto = False
                    # マップが読み込み時にGPS情報を取得
                    LocateControl(
                        auto_start=True,  # 自動的に現在地を取得
                        strings={"title": "現在地を表示", "popup": "現在地"},
                        locateOptions={
                            "enableHighAccuracy": True,
                            "maxZoom": 15
                        }
                    ).add_to(map_preview)
                    st.session_state.marker_location = [map_preview.location[0], map_preview.location[1]]
                    st.session_state.center = st.session_state.marker_location
                    st.session_state.zoom = 15

                # マーカー表示
                folium.Marker(
                    location=st.session_state.marker_location,
                    popup=f"{st.session_state.marker_location}",
                    icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
                ).add_to(map_preview)

                # マップ表示
                map_folium = st_folium(
                    map_preview,
                    height=400,
                    use_container_width=True,
                    returned_objects=["last_clicked"],
                )

                # マップがクリックされたら緯度経度を取得してマーカーを更新
                if map_folium and map_folium.get("last_clicked"):
                    clicked_loc = [
                        map_folium["last_clicked"]["lat"],
                        map_folium["last_clicked"]["lng"],
                    ]
                    if clicked_loc != st.session_state.marker_location:
                        st.session_state.marker_location = clicked_loc
                        st.session_state.center = clicked_loc
                        st.session_state.zoom = 15
                        update_address(st.session_state.marker_location)
                        st.rerun()

            # sessionを変数に変換
            marker_address = st.session_state.marker_address

            # 現在選択中の位置の表示
            st.markdown(
                f"""
                    <div style="background: rgba(255,255,255,0.1); padding: 0.94rem; border-radius: 0.5rem; margin-top: -0.625rem; margin-bottom: 0.625rem; text-align: center;"> <span style="font-size: 0.9em; color: white;">現在選択中の位置:</span><br>
                        <strong style="color: white; font-size: 1.1em;">{marker_address}</strong>
                    </div>
                """,
                unsafe_allow_html=True,
            )
        if st.session_state.search_error:
            st.warning(st.session_state.search_error)

        if st.button("🐟 魚を判定する", use_container_width=True,type="primary"):
            if st.session_state.uploaded_file is None:
                st.warning("画像をアップロードしてください。")
            elif st.session_state.marker_location is None:
                st.warning("現在地を選択してください。")
            elif st.session_state.marker_address is None:
                st.warning("現在地が不明です。")
            else:
                st.session_state.run_process = True
                st.rerun()

        if st.session_state.run_process:
            # ローディング画面を表示
            loading_placeholder = st.empty()
            loading_placeholder.markdown(wave_load_html, unsafe_allow_html=True)

            time.sleep(0.5)
            try:
                # 魚種判別処理
                # 画像データ取得

                # 画像を開く
                image = Image.open(st.session_state.uploaded_file)

                # exifの修正 スマホ画像の向きを直す
                image = ImageOps.exif_transpose(image)

                # カラーモードをRGBに統一
                if image.mode != "RGB":
                    image = image.convert("RGB")

                # 画像をリサイズ
                image.thumbnail((1568, 1568))

                # バイトデータに変換
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="JPEG", quality=95)
                image_bytes = img_buffer.getvalue()

                prefecture = st.session_state.get("current_prefecture", "")
                city = st.session_state.get("current_city", "")

                # 漁業権比較処理 引数の値を緯度　経度に変える必要あり
                result = identify_and_check_fish(image_bytes, prefecture, city,st.session_state.marker_location[0],st.session_state.marker_location[1])
                st.session_state.result = result

            except Exception as e:
                st.error(f"予期せぬエラーが発生しました: {e}")
            finally:
                st.session_state.run_process = False
                st.rerun()

        # 履歴表示
        if st.session_state.search_history:
            st.markdown("""
                        <div style="margin-top: 1.5rem; margin-bottom: 0.5rem; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 1rem;">
                            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">検索履歴</p>
                        </div>
                    """, unsafe_allow_html=True)

            # 履歴をボタンとして表示
            for history_list in st.session_state.search_history:
                history_name = history_list["name"]

                if st.button(f"📍 {history_name}", use_container_width=True,type="secondary"):
                    load_history(history_list)



    else:  # 結果表示

        result = st.session_state.result

        is_legal = result.get("isLegal")
        print(f"漁業権照会結果：{is_legal}")

        # 判定結果に基づいたスタイル設定

        if is_legal:

            status_color = "#28a745"

            status_bg = "rgba(40, 167, 69, 0.2)"

            status_icon = "◯"

            status_label = "持ち帰りOK"

            sub_text = "この魚は現在の位置で採捕が許可されています。"

        else:

            status_color = "#dc3545"

            status_bg = "rgba(220, 53, 69, 0.2)"

            status_icon = "×"

            status_label = "持ち帰りNG"

            sub_text = "漁業権により採捕が禁止されています。"

        # HTML文字列を作成（行頭のスペースを消すのがポイントです）

        result_html = f"""

    <div style="background:{status_bg};border:2px solid {status_color};border-radius:1rem;padding:0.5rem;text-align:center;margin-bottom:2rem;">

    <div style="font-size:5rem;line-height:1;color:{status_color};margin-bottom:1rem;font-weight:bold;text-shadow:0 0 20px {status_color}44;">

    {status_icon}

    </div>

    <p style="color:white;margin:0;font-size:2rem;text-align: center;font-weight: bold;">{status_label}</p>

    <p style="color:rgba(255,255,255,0.8);margin-top:0.5rem;text-align:center;">{sub_text}</p>

    </div>

    """

        # HTMLとして表示

        st.markdown(result_html, unsafe_allow_html=True)


        if result.get("fishNameJa"):
            # 毒・危険情報の表示
            danger_type = result.get("danger_type", "none")
            poison_text = result.get("poison_info")

            if danger_type != "none" and poison_text:
                # 触ると危険
                if danger_type == "touch":
                    danger_color = "#ff2a2a"
                    danger_bg = "rgba(216, 50, 255, 0.2)"
                    danger_title = "触ると危険"

                # 食べると危険
                elif danger_type == "eat":
                    danger_color = "#ff8c00"
                    danger_bg = "rgba(216, 50, 255, 0.2)"
                    danger_title = "食べると危険"

                # HTML生成
                poison_info_html = f"""
                                <div style="
                                    background: {danger_bg}; 
                                    padding: 1rem; 
                                    border-radius: 0.8rem; 
                                    border: 2px solid {danger_color}; 
                                    margin-bottom: 1.5rem;
                                    display: flex;
                                    flex-direction: column;
                                    align-items: center;
                                    gap: 0.5rem;
                                ">
                                    <div style="
                                        color: {danger_color};
                                        font-size: 2rem;
                                        font-weight: bold;
                                        display: flex;
                                        align-items: center;
                                        gap: 0.5rem;
                                    ">{danger_title}
                                    </div>
                                    <p style="
                                        color: white; 
                                        margin: 0; 
                                        text-align: center; 
                                        font-size: 1rem;
                                        line-height: 1.5;
                                    ">
                                        {poison_text}
                                    </p>
                                </div>
                                """

                st.markdown(poison_info_html, unsafe_allow_html=True)
            fish_info_html = f"""
            <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
                <p style="color: white; margin: 0 0 0.5rem 0; text-align: center;font-size: 2rem;">{result.get('fishNameJa')}</p>
                <p style="color: rgba(255,255,255,0.8); margin: 0; text-align: center; font-size: 1.1rem;">{result.get('fishNameEn')}</p>
                <p style="color: rgba(255,255,255,0.6); margin: 0.5rem 0 0 0; text-align: center; font-style: italic;">学名: {result.get('scientificName', '不明')}</p>
            </div>
            """
            st.markdown(fish_info_html, unsafe_allow_html=True)

        # 漁業権の情報を表示
        if result.get("gyogyoken"):
            gyogyoken_html = f"""
            <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff7b00; margin-bottom: 1.5rem;">
                <p style="color: white; margin: 0; font-size: 0.9rem;"><strong>漁業権情報:</strong></p>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">{result.get('gyogyoken')}</p>
            </div>
            """
            st.markdown(gyogyoken_html, unsafe_allow_html=True)




        if st.button("別の画像を選択", key="reset_result_btn", use_container_width=True, type="primary"):
            st.session_state.uploaded_file = None

            st.session_state.result = None

            st.rerun()