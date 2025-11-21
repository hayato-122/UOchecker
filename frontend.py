# frontend.py

import streamlit as st
from PIL import Image
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from backend import identify_and_check_fish

# webサイト初回起動時の初期設定
if "center" not in st.session_state:                  # マップの初期位置設定
    st.session_state.center = [34.694659,135.194954]  # 三ノ宮駅
if "marker_location" not in st.session_state:         #マーカーの初期位置設定　三ノ宮駅
    st.session_state.marker_location = [34.694659,135.194954]
if "zoom" not in st.session_state: # ズームの初期設定
    st.session_state.zoom = 8

# 日本語の記事として登録するhtml 意味ない可能性あり
st.markdown(
    """
    <meta charset="UTF-8">
    <meta http-equiv="Content-Language" content="ja">
    """,
    unsafe_allow_html=True,
)

# streamlitのサイトのタイトルとレイアウトの設定
st.set_page_config(page_title="UOチェッカー", layout="centered")

# タイトルを中央揃えで表示
title = "UOチェッカー"

st.markdown(
    f"""<h1 style='text-align: center; 
            font-size: clamp(30px, 8vw, 100px); /* フォントサイズの最小値、最大値を設置 */
            font-weight: bold;                  /* 太字 */
            white-space: nowrap;'>{title}</h1>""",  # タイトルを改行なしに設定
    unsafe_allow_html=True,
)

st.button("設定", width="stretch", key="settings_button")  # 設定ボタンを追加

st.markdown("---")  # 区切り線

# CSSスタイル
custom_css = """
    <style>
    [data-testid="stFileUploader"] section {
        visibility: hidden /* 元のfile uploaderを非表示にする */
    }
    /* CSSでボタンを作成 */
    [data-testid="stFileUploader"] button {
        visibility: visible;
        width:30vw;
        height: 180px;
        color: transparent !important;
        background-color: #ffffff;
        border: 2px dashed #cccccc;
        border-radius: 10px;
        font-size: 1.2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-left: -17%;
        margin-right: auto;
    }

    @media (max-width: 600px) {
        [data-testid="stFileUploader"] button {
            width: 80vw;
            margin-top: -20px;
            margin-left: 0;
            margin-right: auto;
        }
    }

    [data-testid="stFileUploader"] button:hover {
        background-color: #f7f7f7;
        border-color: #aaaaaa;
    }

    [data-testid="stFileUploader"] button::before {
        content: '📷';
        font-size: 4rem;
        color: #555;
        display: block;
        margin-bottom: 0.5rem;
    }

    [data-testid="stFileUploader"] button::after {
        content: '画像を選択';
        font-size: 1.2rem;
        color: #333;
        display: block;
    }

    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .stImage {
        text-align: center;
    }

    </style>
"""

st.html(custom_css)

# ファイルがアップロードされていない場合のみアップローダーを表示
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if st.session_state.uploaded_file is None:  # ファイル未アップロード時

    # アップローダー表示
    col_uploader_left, col_uploader, col_uploader_right = st.columns([2, 5, 2])

    with col_uploader:  # 中央カラムにアップローダーを配置 png jpg jpeg対応
        uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])

        if uploaded_file is not None:  # ファイルがアップロードされた場合
            st.session_state.uploaded_file = uploaded_file  # セッションに保存
            st.rerun()  # ページをリロードしてプレビュー表示へ
else:
    # プレビュー表示
    col_preview_left, col_preview_center, col_preview_right = st.columns([2, 5, 2])

    with col_preview_center:  # 中央カラムにプレビューを配置
        try:
            image = Image.open(st.session_state.uploaded_file)  # 画像を開く
            st.image(
                image,
                caption=st.session_state.uploaded_file.name,
                width="stretch",
            )

        except Exception as e:
            st.error(f"読み込みエラー: {e}")
            st.session_state.uploaded_file = None

    # 別の画像を選択ボタンを中央揃えで配置
    col_btn_picture_left, col_btn_picture, col_btn_picture_right = st.columns([2, 5, 2])

    with col_btn_picture:
        if st.button("別の画像を選択", width="stretch"):
            st.session_state.uploaded_file = None
            st.rerun()

# 検索機能
st.write("\n\n")
st.divider()
geolocator = Nominatim(user_agent="streamlit-folium-app")
search_map = st.text_input("地名を入力して検索")

if st.button("検索") and search_map:
    try:
        location = geolocator.geocode(search_map)
        if location:
            new_location = [location.latitude, location.longitude]
            st.session_state.center = new_location
            st.session_state.marker_location = new_location
            st.session_state.zoom = 15
            st.rerun()  # 検索時に全体を更新
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# マップ表示コンテナ作成
with st.container(height=600, border=False):

    # マップ作成
    map_preview = folium.Map(
        location=st.session_state.center,
        zoom_start=st.session_state.zoom,
        tiles = "https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
        attr = "Google Maps"
    )

    # マーカー配置
    folium.Marker(
        location=st.session_state.marker_location,
        popup=f"{st.session_state.marker_location}",
        icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
        tooltip="選択位置",
    ).add_to(map_preview)

    # マップ表示
    output = st_folium(
        map_preview,
        width=700,
        height=500,  # コンテナより少し小さく設定
        use_container_width=True,
        returned_objects=["last_clicked"],
    )

    # クリック判定と更新
    if output and output.get("last_clicked"):
        clicked_loc = [output["last_clicked"]["lat"], output["last_clicked"]["lng"]]

        if clicked_loc != st.session_state.marker_location:
            st.session_state.marker_location = clicked_loc
            st.session_state.center = clicked_loc
            st.session_state.zoom = 15
            st.rerun()  # ここでスクリプト全体を再実行します

# 座標を住所に変換
marker_address = geolocator.reverse(st.session_state.marker_location,language='ja')

# 座標表示（コンテナの外に配置）
st.write(f"📍 現在のマーカー位置: {marker_address}")

# 検索ボタンを中央揃えで配置
col_search_fish_left, col_search_fish_button, col_search_fish_right = st.columns([3, 4, 3])
with col_search_fish_button:
    if st.button("検索", width="stretch"):
        if st.session_state.uploaded_file is None:
            st.warning("画像をアップロードしてください。")
        elif st.session_state.marker_location is None:
            st.warning("現在地を選択してください。")
        else: # 魚判別開始
            with st.spinner("魚を識別中..."):
                # 画像データをbytesに変換
                image_bytes = st.session_state.uploaded_file.getvalue()

                # 住所情報から都道府県と市区町村を抽出
                address_data = marker_address.raw.get('address', {})

                # 都道府県 Nominatimでは 'province' や 'region' などに入ることがある
                prefecture = address_data.get('province', address_data.get('region', ''))

                # 市区町村 city, town, village, countyなどを順に探す
                city = address_data.get('city',
                address_data.get('town',
                address_data.get('village',
                address_data.get('county', ''))))

                # デバッグ用に抽出結果を表示（必要なければ削除可）
                st.info(f"抽出された位置情報: {prefecture} {city}")

                # backend関数を実行
                result = identify_and_check_fish(
                    image_bytes=image_bytes,
                    prefecture=prefecture,
                    city=city
                )

                # 結果の表示
                if result.get("success"):
                    st.success("解析完了！")
                    st.json(result["data"])  # 結果をJSONで表示（適宜きれいなUIに変更してください）
                else:
                    st.error(f"エラー: {result.get('error')}")
                    st.write(result.get('message'))

# ↓をコマンドラインに入力してサーバー作成
# streamlit run frontend.py --server.port 8501
