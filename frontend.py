# frontend.py

import streamlit as st
from PIL import Image, ImageOps
import folium
from streamlit_folium import st_folium
from geopy.geocoders import ArcGIS
import base64
import requests
import io
import streamlit.components.v1 as components

from backend import identify_and_check_fish

geolocator = ArcGIS(user_agent="uochecker-app-v1.0", timeout=10)


def update_address(location_list):
    lat, lng = location_list
    url = " https://geoapi.heartrails.com/api/json?method=searchByGeoLocation"
    params = {
        "method": "searchByGeoLocation",
        "x": lng,
        "y": lat
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if "response" in data and "location" in data["response"]:
            loc = data["response"]["location"][0]
            address_text = f"{loc['prefecture']}{loc['city']}{loc['town']}"
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


st.set_page_config(page_title="UOチェッカー", layout="wide")

components.html("""
    <script>
        window.parent.document.documentElement.lang = 'ja';
    </script>
""", height=0, width=0)

if "center" not in st.session_state:
    st.session_state.center = [34.694659, 135.194954]
if "marker_location" not in st.session_state:
    st.session_state.marker_location = [34.694659, 135.194954]
if "marker_address" not in st.session_state:
    update_address(st.session_state.marker_location)
if "current_prefecture" not in st.session_state:
    st.session_state.current_prefecture = ""
if "current_city" not in st.session_state:
    st.session_state.current_city = ""
if "zoom" not in st.session_state:
    st.session_state.zoom = 8
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "result" not in st.session_state:
    st.session_state.result = None
if "search_map" not in st.session_state:
    st.session_state.search_map = None
if "search_error" not in st.session_state:
    st.session_state.search_error = None
if "search_history" not in st.session_state:
    st.session_state.search_history = []

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

    .stApp {
        background-image: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    * {
        scrollbar-width: none;
    }

    [data-testid="stHeader"] {
        display: none !important;
    }

    footer {
        visibility: hidden !important;
        height: 0 !important;
    }

    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0rem !important;
    }

    [data-testid="stColumn"] [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }

    [data-testid="stColumn"]:nth-of-type(1) {
        background: linear-gradient(90deg, rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0.35));
        padding: 3rem 2rem;
        min-height: 102vh;
        margin-top: -2rem;
        user-select: none !important;
        -webkit-user-select: none !important;
    }

    [data-testid="stColumn"]:nth-of-type(2) {
        background: rgba(0, 0, 0, 0.76);
        padding: 3rem 2rem;
        min-height: 102vh;
        margin-top: -2rem;
        user-select: none !important;
        -webkit-user-select: none !important;
    }

    [data-testid="stColumn"] [data-testid="stColumn"] {
        background: transparent !important;
        padding: 0 !important;
        min-height: 0 !important;
    }

    h1, h2, h3, p, div, label, span {
        font-family: 'Noto Sans JP', sans-serif !important;
        text-shadow: 0.06rem 0.06rem 0.125rem rgba(0,0,0,0.5);
    }

    [data-testid="stFileUploader"] section {
        visibility: hidden;
    }

    [data-testid="stFileUploader"] ul {
        display: none !important;
    }

    [data-testid="stFileUploader"] small {
        display: none !important;
    }

    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
        visibility: visible;
        width: 30vw;
        height: 11.25rem;
        color: transparent !important;
        background: transparent !important;
        border: 0.125rem dashed rgba(255, 255, 255, 0.5);
        border-radius: 0.94rem;
        font-size: 1.2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-left: -23%;
        margin-right: auto;
    }

    @media (max-width: 600px) {
        [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
            width: 80vw;
            margin-left: -2%;
            margin-right: auto;
        }

        [data-testid="stColumn"]:nth-of-type(2) {
            margin-top: 0 !important;
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

    div.stButton > button {
        border-radius: 0.625rem;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
    }

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

    div.stButton > button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 0.4rem 1rem;
        text-align: left;
        display: flex;
        justify-content: flex-start;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.5);
        color: #ff7b00;
        padding-left: 1.5rem !important;
    }

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

col_main_left, col_main_right = st.columns([1, 1], gap="small")

with col_main_left:
    with open("image/title_logo.png", "rb") as title_logo_img:
        title_logo_data = title_logo_img.read()
        title_logo_base64 = base64.b64encode(title_logo_data).decode("utf-8")
    st.markdown(
        f"""
            <div style="text-align: center; margin-top: 0rem; margin-bottom: 2rem;">
                <img src="data:image/gif;base64,{title_logo_base64}" style="width: 9.375rem;pointer-events: none; -webkit-user-drag: none;">
                <div style="margin: 0; color: white; white-space: nowrap; font-size: 3rem; font-weight: bold; line-height: 1.2;">UOチェッカー</div>
                <p style="color: white; font-size: 1.8rem; font-weight: bold; margin-top: 0.5rem;">漁業権を確認しましょう</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.uploaded_file is None:
        uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])
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
                if st.button("別の画像を選択", use_container_width=True,type="primary"):
                    st.session_state.uploaded_file = None
                    st.session_state.result = None
                    st.rerun()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
            st.session_state.uploaded_file = None

with col_main_right:
    if st.session_state.result is None:
        st.markdown(
            """
            <div style="padding: 1.5rem; margin-bottom: 3rem; margin-top: -2.5rem; border-bottom: 0.06rem solid rgba(255,255,255,0.3);">
                <p style="text-align:center; margin:0; font-weight:bold; color: white; ">📍 場所を指定してください</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        with st.container():
            col_search_in, col_search_btn = st.columns([6, 2])
            with col_search_in:
                search_map = st.text_input(
                    "地名検索", placeholder="例：明石市", label_visibility="collapsed"
                )
            with col_search_btn:
                if st.button("検索",type="primary") and search_map and search_map != st.session_state.search_map:
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

                        if search_map not in st.session_state.search_history:
                            new_history = {
                                "name": search_map,
                                "lat": location.latitude,
                                "lng": location.longitude,
                                "address": st.session_state.marker_address,
                                "prefecture": st.session_state.current_prefecture,
                                "city": st.session_state.current_city
                            }
                            st.session_state.search_history.insert(0, new_history)
                            if len(st.session_state.search_history) > 3:
                                st.session_state.search_history.pop()
                        st.rerun()
                    else:
                        st.session_state.search_error = f"「{search_map}」は見つかりませんでした。別の地名で試してください。"

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

                map_folium = st_folium(
                    map_preview,
                    height=400,
                    use_container_width=True,
                    returned_objects=["last_clicked"],
                )

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

            marker_address = st.session_state.marker_address

            st.markdown(
                f"""
                    <div style="background: rgba(255,255,255,0.1); padding: 0.94rem; border-radius: 0.5rem; margin-top: -0.625rem; text-align: center;"> <span style="font-size: 0.9em; color: white;">現在選択中の位置:</span><br>
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
                with open("image/wave_load.gif", "rb") as wave_load_gif:
                    wave_load_data = wave_load_gif.read()
                    wave_load_base64 = base64.b64encode(wave_load_data).decode("utf-8")

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
                            <img src="data:image/gif;base64,{wave_load_base64}" style="width: 9.375rem;"> <div class="loader-text">魚を識別中...</div>
                        </div>
                        """

                loading_placeholder = st.empty()
                loading_placeholder.markdown(wave_load_html, unsafe_allow_html=True)

                try:
                    image = Image.open(st.session_state.uploaded_file)
                    image = ImageOps.exif_transpose(image)
                    if image.mode != "RGB":
                        image = image.convert("RGB")
                    image.thumbnail((1568, 1568))
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
                    loading_placeholder.empty()
                    st.rerun()

        if st.session_state.search_history:
            st.markdown("""
                        <div style="margin-top: 1.5rem; margin-bottom: 0.5rem; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 1rem;">
                            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">検索履歴</p>
                        </div>
                    """, unsafe_allow_html=True)

            for history_list in st.session_state.search_history:
                history_name = history_list["name"]

                if st.button(f"📍 {history_name}", use_container_width=True,type="secondary"):
                    new_location = [history_list["lat"], history_list["lng"]]
                    st.session_state.center = new_location
                    st.session_state.marker_location = new_location
                    st.session_state.zoom = 15
                    st.session_state.marker_address = history_list["address"]
                    st.session_state.current_prefecture = history_list["prefecture"]
                    st.session_state.current_city = history_list["city"]
                    st.session_state.search_error = None
                    st.rerun()

    else:
        result = st.session_state.result
        
        st.markdown(
            """
            <div style="padding: 1.5rem; margin-bottom: 1.5rem; margin-top: -2.5rem; border-bottom: 0.06rem solid rgba(255,255,255,0.3);">
                <p style="text-align:center; margin:0; font-weight:bold; color: white;">🐟 識別結果</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        with st.container():
            if not result.get("success"):
                st.error(result.get("error", "魚を特定できませんでした"))
                if "message" in result:
                    st.info(result["message"])
            else:
                data = result.get("data", {})
                
                if result.get("fromCache"):
                    st.info("⚡ キャッシュから取得（高速）")
                else:
                    st.info("🤖 AIが新しく生成しました")
                
                st.subheader(f"{data.get('fishNameJa', '不明')} ({data.get('fishNameEn', 'Unknown')})")
                if data.get("scientificName"):
                    st.caption(f"学名: {data['scientificName']}")
                
                status = data.get("status", "UNKNOWN")
                legal_explanation = data.get("legalExplanation", "情報なし")
                
                if status == "OK":
                    st.success(legal_explanation)
                elif status == "RESTRICTED":
                    st.warning(legal_explanation)
                elif status == "PROHIBITED":
                    st.error(legal_explanation)
                else:
                    st.info(legal_explanation)
                
                st.markdown("### 📋 規制情報")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    min_size = data.get("minSize", 0)
                    if min_size > 0:
                        st.metric("最小サイズ", f"{min_size}cm")
                    else:
                        st.metric("最小サイズ", "制限なし")
                
                with col2:
                    daily_limit = data.get("dailyLimit")
                    if daily_limit:
                        st.metric("1日の漁獲量", f"{daily_limit}尾")
                    else:
                        st.metric("1日の漁獲量", "制限なし")
                
                with col3:
                    seasonal_ban = data.get("seasonalBan", [])
                    if seasonal_ban:
                        st.metric("禁漁期", ", ".join(seasonal_ban))
                    else:
                        st.metric("禁漁期", "なし")
                
                with col4:
                    is_edible = data.get("isEdible")
                    if is_edible is True:
                        st.metric("食用", "✅ 可能")
                    elif is_edible is False:
                        st.metric("食用", "❌ 不可")
                    else:
                        st.metric("食用", "不明")
                
                fishing_rights = data.get("fishingRights", {})
                if fishing_rights:
                    st.markdown("### 🎣 漁業権情報")
                    
                    requires_license = fishing_rights.get("requiresLicense", False)
                    if requires_license:
                        st.warning("⚠️ 注意: この魚種・地域では許可が必要な場合があります")
                    else:
                        st.success("✓ 一般的に自由に釣ることができます")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        license_type = fishing_rights.get("licenseType", "なし")
                        if license_type != "なし":
                            st.info(f"**必要な許可:** {license_type}")
                        
                        fishing_area = fishing_rights.get("fishingRightsArea", "不明")
                        if fishing_area != "不明":
                            st.info(f"**漁業権区域:** {fishing_area}")
                    
                    with col2:
                        restrictions = fishing_rights.get("restrictions", "特になし")
                        if restrictions != "特になし":
                            st.warning(f"**制限事項:** {restrictions}")
                        
                        coop_info = fishing_rights.get("cooperativeInfo", "")
                        if coop_info:
                            st.info(f"**漁協情報:** {coop_info}")
                
                with st.expander("📖 詳細情報を見る"):
                    if data.get("description"):
                        st.write("**説明:**")
                        st.write(data["description"])
                    
                    if data.get("cookingMethods"):
                        st.write("**調理法:**")
                        st.write(", ".join(data["cookingMethods"]))
                    
                    if data.get("taste"):
                        st.write("**味:**")
                        st.write(data["taste"])
                    
                    if data.get("nutrition"):
                        st.write("**栄養:**")
                        st.write(data["nutrition"])
                    
                    if data.get("peakSeason"):
                        st.write("**旬:**")
                        st.write(data["peakSeason"])
                    
                    if data.get("habitat"):
                        st.write("**生息地:**")
                        st.write(data["habitat"])
                    
                    if data.get("edibilityNotes"):
                        st.write("**食用に関する注意:**")
                        st.write(data["edibilityNotes"])
                    
                    if data.get("preparationWarnings"):
                        st.write("**調理時の注意:**")
                        st.warning(data["preparationWarnings"])
                
                st.markdown("---")
                st.caption(f"📚 情報源: {data.get('regulationSource', '不明')}")
                st.caption(f"🎯 信頼度: {data.get('confidence', '不明')}")
                
                if data.get("sourceUrl"):
                    st.caption(f"[公式サイトで確認]({data['sourceUrl']})")

            if st.button("別の画像を選択", key="reset_result_btn", use_container_width=True,type="primary"):
                st.session_state.uploaded_file = None
                st.session_state.result = None
                st.rerun()
