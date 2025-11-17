import streamlit as st
from PIL import Image

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

suggestions = [  # selectboxの候補リスト
    "神戸",
    "姫路",
    "大阪",
    "京都",
    "奈良",
    "和歌山",
    "滋賀",
    "福井",
    "石川",
    "富山",
    "名古屋",
    "岐阜",
    "静岡",
    "浜松",
    "三重",
    "東京",
    "横浜",
    "川崎",
    "埼玉",
    "千葉",
    "茨城",
    "栃木",
    "群馬",
    "宇都宮",
    "水戸",
    "高崎",
    "仙台",
    "福島",
    "山形",
    "秋田",
    "盛岡",
    "青森",
    "弘前",
    "八戸",
    "新潟",
    "長野",
    "松本",
    "甲府",
    "山梨",
    "富士吉田",
    "静岡市",
]
st.write("\n\n")
st.divider()
selected = st.selectbox(
    "現在地を入力", [""] + suggestions
)  # 現在地検索、選択セレクトボックス作成

# 決定ボタンを中央揃えで配置
col_decide_left, col_decide_button, col_decide_right = st.columns([3, 4, 3])
with col_decide_button:
    if st.button("決定", width="stretch"):
        if selected == "":
            st.warning("現在地を選択してください。")
        else:
            st.success(f"現在地が「{selected}」に設定されました。")

# ↓をコマンドラインに入力してサーバー作成
# streamlit run main.py --server.port 8501
