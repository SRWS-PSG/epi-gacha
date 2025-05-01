"""
Tavily APIとの直接連携用モジュール
"""
import os
import json
import requests
import time
from dotenv import load_dotenv

# 環境変数から設定を読み込む
load_dotenv()

# Tavily API設定
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_API_BASE_URL = "https://api.tavily.com"

# エラー処理用の設定
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒

class TavilyAPIError(Exception):
    """Tavily API呼び出し中のエラーを表す例外"""
    pass

def validate_api_key():
    """APIキーが設定されているか検証"""
    if not TAVILY_API_KEY:
        raise TavilyAPIError("TAVILY_API_KEYが設定されていません。.envファイルまたは環境変数で設定してください。")

def search(query, search_depth="basic", max_results=5, include_answer=True, **kwargs):
    """
    Tavily APIを使用して検索を実行
    
    Args:
        query: 検索クエリ
        search_depth: 検索の深さ ("basic" または "advanced")
        max_results: 取得する最大結果数
        include_answer: LLMによる回答要約を含めるかどうか
        **kwargs: その他のTavily API検索パラメータ
        
    Returns:
        検索結果の辞書
    """
    validate_api_key()
    
    # エンドポイントとヘッダーの設定
    endpoint = f"{TAVILY_API_BASE_URL}/search"
    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    
    # デバッグ情報
    print(f"API URL: {endpoint}")
    print(f"認証ヘッダー: Authorization: Bearer {TAVILY_API_KEY[:5]}...{TAVILY_API_KEY[-5:]}")
    
    # リクエストペイロードの作成
    payload = {
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": include_answer
    }
    
    # 追加のパラメーターを追加
    payload.update(kwargs)
    
    # リクエスト実行（リトライロジック付き）
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            # レート制限に引っかかった場合
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", RETRY_DELAY * (attempt + 1)))
                print(f"レート制限に達しました。{wait_time}秒待機します...")
                time.sleep(wait_time)
                continue
                
            # その他のエラー
            if response.status_code != 200:
                error_msg = f"Tavily API エラー: {response.status_code} - {response.text}"
                print(error_msg)
                
                # 500系エラーはリトライ
                if 500 <= response.status_code < 600:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    raise TavilyAPIError(error_msg)
            
            # 成功した場合は結果を返す
            return response.json()
            
        except requests.RequestException as e:
            print(f"リクエスト例外: {e}")
            
            # 最後の試行でない場合はリトライ
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise TavilyAPIError(f"Tavily APIへのリクエストに失敗しました: {e}")
    
    # ここに到達した場合はすべての再試行が失敗
    raise TavilyAPIError("すべての再試行が失敗しました")

def extract(urls, include_images=False, extract_depth="basic"):
    """
    Tavily APIを使用してURLから内容を抽出
    
    Args:
        urls: 抽出するURL（単一の文字列または文字列のリスト）
        include_images: 画像を含めるかどうか
        extract_depth: 抽出の深さ ("basic" または "advanced")
        
    Returns:
        抽出結果の辞書
    """
    validate_api_key()
    
    # エンドポイントとヘッダーの設定
    endpoint = f"{TAVILY_API_BASE_URL}/extract"
    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    
    # デバッグ情報
    print(f"API URL: {endpoint}")
    print(f"認証ヘッダー: Authorization: Bearer {TAVILY_API_KEY[:5]}...{TAVILY_API_KEY[-5:]}")
    
    # URLsを適切な形式に変換
    if isinstance(urls, str):
        urls = [urls]
    
    # リクエストペイロードの作成
    payload = {
        "urls": urls,
        "include_images": include_images,
        "extract_depth": extract_depth
    }
    
    # リクエスト実行（リトライロジック付き）
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            # レート制限に引っかかった場合
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", RETRY_DELAY * (attempt + 1)))
                print(f"レート制限に達しました。{wait_time}秒待機します...")
                time.sleep(wait_time)
                continue
                
            # その他のエラー
            if response.status_code != 200:
                error_msg = f"Tavily API エラー: {response.status_code} - {response.text}"
                print(error_msg)
                
                # 500系エラーはリトライ
                if 500 <= response.status_code < 600:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    raise TavilyAPIError(error_msg)
            
            # 成功した場合は結果を返す
            return response.json()
            
        except requests.RequestException as e:
            print(f"リクエスト例外: {e}")
            
            # 最後の試行でない場合はリトライ
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise TavilyAPIError(f"Tavily APIへのリクエストに失敗しました: {e}")
    
    # ここに到達した場合はすべての再試行が失敗
    raise TavilyAPIError("すべての再試行が失敗しました")
