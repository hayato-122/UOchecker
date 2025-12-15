#!/usr/bin/env python3
"""
システム全体の設定確認スクリプト
全ての API キーと設定が正しく構成されているかチェックします
Streamlit secrets.toml を使用するバージョン
"""

import os
import sys
from pathlib import Path


def check_streamlit_secrets():
    """
    .streamlit/secrets.toml ファイルの存在と内容を確認
    """
    print("\n" + "="*60)
    print("1. Streamlit secrets.toml の確認")
    print("="*60)
    
    secrets_dir = Path(".streamlit")
    secrets_file = secrets_dir / "secrets.toml"
    
    if not secrets_dir.exists():
        print("エラー: .streamlit ディレクトリが見つかりません")
        print("解決方法: プロジェクトルートに .streamlit ディレクトリを作成してください")
        print("  mkdir .streamlit")
        return False
    
    if not secrets_file.exists():
        print("エラー: .streamlit/secrets.toml が見つかりません")
        print("解決方法: .streamlit/secrets.toml ファイルを作成してください")
        return False
    
    print("OK: .streamlit/secrets.toml が存在します")
    return True


def check_secrets_content():
    """
    secrets.toml の内容を確認（Streamlit経由）
    """
    print("\n" + "="*60)
    print("2. Secrets の内容確認")
    print("="*60)
    
    try:
        import streamlit as st
        
        # Anthropic API キーの確認
        if "ANTHROPIC_API_KEY" not in st.secrets:
            print("エラー: ANTHROPIC_API_KEY が secrets.toml に設定されていません")
            return False
        
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        if not api_key.startswith("sk-ant-"):
            print("警告: API キーの形式が正しくない可能性があります")
            print(f"  現在の値: {api_key[:10]}...")
            return False
        
        print(f"OK: ANTHROPIC_API_KEY が設定されています ({api_key[:15]}...)")
        
        # Google Cloud 認証情報の確認
        if "gcp_service_account" not in st.secrets:
            print("エラー: gcp_service_account が secrets.toml に設定されていません")
            return False
        
        gcp_config = st.secrets["gcp_service_account"]
        required_fields = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id"
        ]
        
        missing_fields = [field for field in required_fields if field not in gcp_config]
        
        if missing_fields:
            print(f"エラー: 必須フィールドが不足しています: {missing_fields}")
            return False
        
        if gcp_config["type"] != "service_account":
            print(f"警告: type が 'service_account' ではありません: {gcp_config['type']}")
            return False
        
        print(f"OK: GCP サービスアカウント設定が正しい形式です")
        print(f"  プロジェクトID: {gcp_config['project_id']}")
        print(f"  サービスアカウント: {gcp_config['client_email']}")
        
        return True
        
    except ImportError:
        print("エラー: streamlit パッケージがインストールされていません")
        print("実行: pip install streamlit")
        return False
    except Exception as e:
        print(f"エラー: secrets の読み込みに失敗しました: {e}")
        return False


def check_required_packages():
    """
    必須パッケージのインストール確認
    """
    print("\n" + "="*60)
    print("3. 必須パッケージの確認")
    print("="*60)
    
    required_packages = {
        "streamlit": "streamlit",
        "anthropic": "anthropic",
        "google.cloud.vision": "google-cloud-vision",
        "firebase_admin": "firebase-admin",
        "googletrans": "googletrans==3.1.0a0",
        "PIL": "Pillow"
    }
    
    all_installed = True
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print(f"OK: {package_name} がインストールされています")
        except ImportError:
            print(f"エラー: {package_name} がインストールされていません")
            print(f"  実行: pip install {package_name}")
            all_installed = False
    
    return all_installed


def check_file_structure():
    """
    プロジェクトのファイル構造を確認
    """
    print("\n" + "="*60)
    print("4. プロジェクトファイル構造の確認")
    print("="*60)
    
    required_files = {
        "backend.py": "バックエンドメインロジック",
        "frontend.py": "Streamlit フロントエンド",
        "utils/vision_api.py": "Vision API 統合",
        "utils/claude_api.py": "Claude API 統合",
        "utils/database.py": "Firebase データベース",
        "utils/location.py": "位置情報変換"
    }
    
    all_exist = True
    
    for file_path, description in required_files.items():
        path = Path(file_path)
        if path.exists():
            print(f"OK: {file_path} - {description}")
        else:
            print(f"エラー: {file_path} が見つかりません - {description}")
            all_exist = False
    
    return all_exist


def test_api_connections():
    """
    API 接続のテスト
    """
    print("\n" + "="*60)
    print("5. API 接続テスト")
    print("="*60)
    
    try:
        import streamlit as st
        from anthropic import Anthropic
        from google.cloud import vision
        from google.oauth2 import service_account
        
        # Claude API テスト
        print("\nClaude API テスト中...")
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        client = Anthropic(api_key=api_key)
        print("OK: Claude API クライアント作成成功")
        
        # Vision API テスト
        print("\nVision API テスト中...")
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        print("OK: Vision API クライアント作成成功")
        
        # Firebase テスト
        print("\nFirebase テスト中...")
        import firebase_admin
        from firebase_admin import credentials as fb_credentials
        
        if not firebase_admin._apps:
            key_dict = dict(st.secrets["gcp_service_account"])
            creds = fb_credentials.Certificate(key_dict)
            firebase_admin.initialize_app(creds)
        
        print("OK: Firebase 初期化成功")
        
        return True
        
    except Exception as e:
        print(f"エラー: API 接続テストに失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    メイン確認ルーチン
    """
    print("\n" + "="*60)
    print("UOチェッカー システム設定確認")
    print("Streamlit secrets.toml バージョン")
    print("="*60)
    
    checks = [
        ("Streamlit Secrets ファイル", check_streamlit_secrets),
        ("Secrets 内容", check_secrets_content),
        ("必須パッケージ", check_required_packages),
        ("ファイル構造", check_file_structure),
        ("API 接続", test_api_connections)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\nエラー: {check_name} の確認中に例外が発生しました: {e}")
            results[check_name] = False
    
    # 結果サマリー
    print("\n" + "="*60)
    print("確認結果サマリー")
    print("="*60)
    
    for check_name, passed in results.items():
        status = "OK" if passed else "NG"
        print(f"{check_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("全ての確認が完了しました！")
        print("システムは正常に動作する準備ができています。")
        print("\nアプリケーションを起動するには:")
        print("  streamlit run frontend.py")
    else:
        print("いくつかの問題が検出されました。")
        print("上記のエラーメッセージを確認して、必要な修正を行ってください。")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())