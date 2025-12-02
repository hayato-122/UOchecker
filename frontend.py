# frontend.py
import time

import streamlit as st
from PIL import Image
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import base64

from backend import identify_and_check_fish


# streamlitのページ設定
st.set_page_config(page_title="UOチェッカー", layout="wide")

# webサイト初回起動時の初期設定
if "center" not in st.session_state:
    st.session_state.center = [34.694659, 135.194954]  # 三ノ宮駅
if "marker_location" not in st.session_state:
    st.session_state.marker_location = [34.694659, 135.194954]
if "zoom" not in st.session_state:
    st.session_state.zoom = 8
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "result" not in st.session_state:
    st.session_state.result = None

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

    /* 余白削除とフルワイド化 */

    /* メインコンテナのパディングを削除 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
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
        min-height: 98vh;
    }

    /* カラム設定 右側（メイン） */
    [data-testid="stColumn"]:nth-of-type(2) {
        background: rgba(0, 0, 0, 0.76);
        padding: 3rem 2rem;
        min-height: 98vh;
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
            margin-top: -20px;
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
col_main_left, col_main_right = st.columns([1, 1], gap="small")

# 左カラム
with col_main_left:
    with open("image/title_logo.png", "rb") as title_logo_img:
        title_logo_data = title_logo_img.read()
        title_logo_base64 = base64.b64encode(title_logo_data).decode("utf-8")
    st.markdown(
        f"""
        <div style="text-align: center; padding: 20px; margin-bottom: 20px;">
            <img src="data:image/gif;base64,{title_logo_base64}" width="150">
            <h1 style="margin: 0; color: white; white-space: nowrap; user-select: none; -webkit-user-select: none;">UOチェッカー</h1>
            <p style="color: white; user-select: none; -webkit-user-select: none;">漁業権を確認しましょう</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state.uploaded_file is None:
        uploaded_file = st.file_uploader("",type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            st.rerun()
    else:
        try:
            image = Image.open(st.session_state.uploaded_file)
            col_image_left, col_image_center, col_image_right = st.columns([1, 3, 1])
            with col_image_center:
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

# 右カラム
with col_main_right:
    if st.session_state.result is None:
        st.markdown(
            """
            <div style="padding: 10px; margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.3);">
                <p style="text-align:center; margin:0; font-weight:bold; color: white; user-select: none; -webkit-user-select: none;">📍 場所を指定してください</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        with st.container():
            # 検索機能
            geolocator = Nominatim(user_agent="streamlit-folium-app",timeout=5)

            col_search_in, col_search_btn = st.columns([6, 2])
            with col_search_in:  # マップ検索入力欄表示
                search_map = st.text_input(
                    "地名検索", placeholder="例：明石市", label_visibility="collapsed"
                )
            with col_search_btn:  # 検索ボタン表示
                if st.button("検索") and search_map:
                    try:
                        location = geolocator.geocode(search_map)
                        if location:
                            new_location = [location.latitude, location.longitude]
                            st.session_state.center = new_location
                            st.session_state.marker_location = new_location
                            st.session_state.zoom = 15
                            st.rerun()
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

            # マップ表示コンテナ
            with st.container():
                map_preview = folium.Map(
                    location=st.session_state.center,
                    zoom_start=st.session_state.zoom,
                    tiles="https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
                    attr="Google Maps",
                )

                folium.Marker(
                    location=st.session_state.marker_location,
                    popup=f"{st.session_state.marker_location}",
                    icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
                ).add_to(map_preview)

                output = st_folium(
                    map_preview,
                    height=400,
                    use_container_width=True,
                    returned_objects=["last_clicked"],
                )

                if output and output.get("last_clicked"):
                    clicked_loc = [
                        output["last_clicked"]["lat"],
                        output["last_clicked"]["lng"],
                    ]
                    if clicked_loc != st.session_state.marker_location:
                        st.session_state.marker_location = clicked_loc
                        st.session_state.center = clicked_loc
                        st.session_state.zoom = 15
                        st.rerun()

            marker_address = geolocator.reverse(st.session_state.marker_location, language="ja",timeout=5)

            st.markdown(
                f"""
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-top: 3px; text-align: center;">
                        <span style="font-size: 0.9em; color: white;user-select: none; -webkit-user-select: none;">現在選択中の位置:</span><br>
                        <strong style="color: white; font-size: 1.1em;">{marker_address.address if hasattr(marker_address, 'address') else '不明'}</strong>
                    </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("🐟 魚を判定する", use_container_width=True):
            if st.session_state.uploaded_file is None:
                st.warning("画像をアップロードしてください。")
            elif st.session_state.marker_location is None:
                st.warning("現在地を選択してください。")
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
                    image_bytes = st.session_state.uploaded_file.getvalue()
                    address_data = marker_address.raw.get("address", {})

                    prefecture = address_data.get(
                        "province", address_data.get("region", "")
                    )
                    city = address_data.get(
                        "city",
                        address_data.get(
                            "town",
                            address_data.get("village", address_data.get("county", "")),
                        ),
                    )

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
                st.json(result["data"])
            else:
                st.error(f"エラー: {result.get('error')}")
                st.write(result.get("message"))

            if st.button("別の画像を選択",key="reset_result_btn",use_container_width=True):
                st.session_state.uploaded_file = None
                st.session_state.result = None
                st.rerun()

