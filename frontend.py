# frontend.py

import streamlit as st  # GUI作成、サーバー作成
from PIL import Image, ImageOps  # 画像の取り扱い
import folium           # mapデータ
from streamlit_folium import st_folium # map表示
from geopy.geocoders import ArcGIS     # マップ情報から緯度経度を取得
import base64   # 画像の形式を変換
import requests # API使用
import io # bytes処理用

from backend import identify_and_check_fish # backedの関数呼び出し

# geolocatorインスタンス作成　update_addressの逆ジオコーディングを実行するため
geolocator = ArcGIS(user_agent="uochecker-app-v1.0",timeout=10)


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
    url = "	https://geoapi.heartrails.com/api/json?method=searchByGeoLocation"
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
        return None


# streamlitのページ設定
st.set_page_config(page_title="UOチェッカー", layout="wide")

# webサイト初回起動時の初期設定
if "center" not in st.session_state:                    # マップ表示の中央の初期設定
    st.session_state.center = [34.694659, 135.194954]   # 三ノ宮駅
if "marker_location" not in st.session_state:           # マーカーの初期位置の初期設定
    st.session_state.marker_location = [34.694659, 135.194954] # 三ノ宮駅
if "marker_address" not in st.session_state:            # マーカーの位置の住所の初期設定
    update_address(st.session_state.marker_location)    # 関数呼び出しで逆ジオコーディング
if "current_prefecture" not in st.session_state:        # 都道府県を保存するセッションの初期設定
    st.session_state.current_prefecture = ""
if "current_city" not in st.session_state:              # 市区町村を保存するセッションの初期設定
    st.session_state.current_city = ""
if "zoom" not in st.session_state:                      # マップのズーム倍率の初期設定
    st.session_state.zoom = 8
if "uploaded_file" not in st.session_state:             # アップロードファイルの初期設定
    st.session_state.uploaded_file = None
if "result" not in st.session_state:                    # 結果の初期設定
    st.session_state.result = None
if "search_map" not in st.session_state:
    st.session_state.search_map = None
if "search_error" not in st.session_state:              # 検索エラーメッセージの初期設定
    st.session_state.search_error = None
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
    
    /* ヘッダー削除 */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* フッター削除 */
    footer {
        visibility: hidden !important;
        height: 0px !important;
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
        background: linear-gradient(90deg, rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0.35));
        padding: 3rem 2rem;
        min-height: 102vh;
        margin-top: -2rem;
        user-select: none !important;
        -webkit-user-select: none !important;
    }

    /* カラム設定 右側（メイン） */
    [data-testid="stColumn"]:nth-of-type(2) {
        background: rgba(0, 0, 0, 0.76);
        padding: 3rem 2rem;
        min-height: 102vh;
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
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
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
        width: 30vw;
        height: 180px;
        color: transparent !important;
        background: transparent !important;
        border: 2px dashed rgba(255, 255, 255, 0.5);
        border-radius: 15px;
        font-size: 1.2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-left: -23%;
        margin-right: auto;
    }

    /* 携帯用 */
    @media (max-width: 600px) {
        /* 修正箇所 */
        [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
            width: 80vw;
            margin-top: -40px;
            margin-left: -2%;
            margin-right: auto;
        }
    }

    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-color: #ff7b00;
    }
    
    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]::before {
        content: '📷';
        font-size: 4rem;
        color: #ccc;
        display: block;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]::after {
        content: '画像を選択';
        font-size: 1.2rem;
        color: #fff;
        display: block;
        font-weight: bold;
        text-shadow: none;
    }
    
    /* ボタン共通スタイル */
    div.stButton > button {
        background-color: #ff7b00;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        padding: 0.5rem 1rem;
        width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #e06c00;
        color: white;
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

# メインレイアウト
col_main_left, col_main_right = st.columns([1, 1], gap="small") # 1:1の比率に設定

# 左カラム タイトル表示と画像プレビュー表示
with col_main_left:
    # タイトル表示
    #タイトルロゴ画像を読み込んでbase64形式に変換
    with open("image/title_logo.png", "rb") as title_logo_img:
        title_logo_data = title_logo_img.read()
        title_logo_base64 = base64.b64encode(title_logo_data).decode("utf-8")
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 0%; margin-bottom: 7%;">
            <img src="data:image/gif;base64,{title_logo_base64}" width="150">
            <h1 style="margin: 0; color: white; white-space: nowrap; ">UOチェッカー</h1>
            <p style="color: white">漁業権を確認しましょう</p>
        </div>
    """,
        unsafe_allow_html=True,
    )
    # 画像プレビュー表示
    if st.session_state.uploaded_file is None: # 画像がアップロードされていない場合
        uploaded_file = st.file_uploader("",type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            st.rerun()
    else: # 画像がアップロードされた場合
        try:
            image = Image.open(st.session_state.uploaded_file) # 画像を読み込み
            col_image_left, col_image_center, col_image_right = st.columns([1, 3, 1]) # 画像を中央に揃える
            with col_image_center: # 中央に画像を表示
                st.image(
                    image,
                    caption="",
                    width="stretch",
                )
                if st.button("別の画像を選択", use_container_width=True):
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
            <div style="margin-bottom: 7%; margin-top: 0%; border-bottom: 1px solid rgba(255,255,255,0.3);">
                <p style="text-align:center; margin:0; font-weight:bold; color: white; ">📍 場所を指定してください</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        with st.container():
            # マップ表示
            # 検索機能
            col_search_in, col_search_btn = st.columns([6, 2])
            with col_search_in:  # マップ検索入力欄表示
                search_map = st.text_input(
                    "地名検索", placeholder="例：明石市", label_visibility="collapsed"
                )
            with col_search_btn:  # 検索ボタン表示
                if st.button("検索") and search_map and search_map != st.session_state.search_map:
                    st.session_state.search_map = search_map
                    st.session_state.search_error = None
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
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-top: -10px; text-align: center;">
                        <span style="font-size: 0.9em; color: white;">現在選択中の位置:</span><br>
                        <strong style="color: white; font-size: 1.1em;">{marker_address}</strong>
                    </div>
                """,
                unsafe_allow_html=True,
            )
        if st.session_state.search_error:
            st.warning(st.session_state.search_error)

        if st.button("🐟 魚を判定する", use_container_width=True):
            if st.session_state.uploaded_file is None:
                st.warning("画像をアップロードしてください。")
            elif st.session_state.marker_location is None:
                st.warning("現在地を選択してください。")
            elif st.session_state.marker_address is None:
                st.warning("現在地が不明です。")
            else:
                # GIFのロード画面読み込み base64形式で読み込み
                with open("image/wave_load.gif", "rb") as wave_load_gif:
                    wave_load_data = wave_load_gif.read()
                    wave_load_base64 = base64.b64encode(wave_load_data).decode("utf-8")

                # ロード画面のHTML
                wave_load_html = f"""
                        <style>
                        .loader-overlay {{
                            position: fixed;
                            top: 0;
                            left: 0;
                            width: 100vw;
                            height: 98vh;
                            background-color: rgba(0, 0, 0, 0.85);
                            z-index: 999999;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            align-items: center;
                            backdrop-filter: blur(5px);
                        }}
                        .loader-text {{
                            color: white;
                            font-size: 24px;
                            font-weight: bold;
                            margin-top: 20px;
                            text-shadow: 0 0 10px rgba(255,255,255,0.5);
                        }}
                        </style>
                        <div class="loader-overlay">
                            <img src="data:image/gif;base64,{wave_load_base64}" width="150">
                            <div class="loader-text">魚を識別中...</div>
                        </div>
                        """

                # ローディング画面を表示
                loading_placeholder = st.empty()
                loading_placeholder.markdown(wave_load_html, unsafe_allow_html=True)

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

                    result = identify_and_check_fish(image_bytes, prefecture, city)
                    st.session_state.result = result

                except Exception as e:
                    st.error(f"予期せぬエラーが発生しました: {e}")

                finally:
                    #
                    loading_placeholder.empty()
                    st.rerun()
    else: # 結果表示
        result = st.session_state.result
        with st.container():
            if result.get("success"):
                st.success("解析完了！")
                data = result["data"]
                st.subheader(f"判定結果: {result.get('identifiedFish', '不明')}")
                st.write(data.get('legal_info', ''))
            else:
                st.error(f"エラー: {result.get('error')}")
                st.write(result.get("message"))

            if st.button("別の画像を選択",key="reset_result_btn",use_container_width=True):
                st.session_state.uploaded_file = None
                st.session_state.result = None
                st.rerun()

