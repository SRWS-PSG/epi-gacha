"""
Tavily API接続のテスト用スクリプト
"""
import os
import json
import argparse
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

def test_direct_api():
    """直接APIモジュールを使用してテスト"""
    try:
        import tavily_api
        
        # APIキーが設定されているか確認
        if not os.getenv("TAVILY_API_KEY"):
            print("警告: TAVILY_API_KEYが設定されていません。")
            print("テストを実行するには、.envファイルまたは環境変数でAPIキーを設定してください。")
            return False
        
        # 簡単な検索を実行
        print("直接APIモジュールを使用してテスト中...")
        result = tavily_api.search("統計学 基礎 歴史", max_results=2)
        
        # 結果を出力
        print("\n=== 検索結果 ===")
        print(f"結果件数: {len(result.get('results', []))}")
        for i, item in enumerate(result.get("results", [])[:2]):
            print(f"\n結果 {i+1}:")
            print(f"タイトル: {item.get('title', 'タイトルなし')}")
            print(f"URL: {item.get('url', 'URLなし')}")
            print(f"スコア: {item.get('score', 'スコアなし')}")
            content = item.get('content', '')
            print(f"内容: {content[:100]}..." if len(content) > 100 else f"内容: {content}")
        
        if "answer" in result:
            print("\n=== 要約回答 ===")
            print(result["answer"])
        
        return True
    
    except ImportError:
        print("エラー: tavily_apiモジュールをインポートできません。")
        return False
    
    except Exception as e:
        print(f"エラー: {e}")
        return False

def test_mcp_interface():
    """MCPインターフェース経由でテスト"""
    try:
        from use_mcp_tool import use_mcp_tool
        import json
        
        # MCPインターフェースを使用して検索
        print("\nMCPインターフェースを使用してテスト中...")
        
        arguments = {
            "what_is_your_intent": "統計学の基礎と歴史に関する情報を調査するため",
            "query": "統計学 基礎 歴史",
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 2
        }
        
        # APIキーが設定されていない場合はUSE_MOCK_TAVILYを設定してモックモードで実行
        if not os.getenv("TAVILY_API_KEY"):
            print("警告: TAVILY_API_KEYが設定されていないため、モックモードでテストします。")
            os.environ["USE_MOCK_TAVILY"] = "true"
        
        result = use_mcp_tool("Tavily Expert", "tavily_search_tool", json.dumps(arguments))
        
        # 結果を出力
        print("\n=== MCP経由の検索結果 ===")
        print(f"結果件数: {len(result.get('results', []))}")
        for i, item in enumerate(result.get("results", [])[:2]):
            print(f"\n結果 {i+1}:")
            print(f"タイトル: {item.get('title', 'タイトルなし')}")
            print(f"URL: {item.get('url', 'URLなし')}")
            print(f"スコア: {item.get('score', 'スコアなし')}")
            content = item.get('content', '')
            print(f"内容: {content[:100]}..." if len(content) > 100 else f"内容: {content}")
        
        if "answer" in result:
            print("\n=== 要約回答 ===")
            print(result["answer"])
        
        # 抽出機能もテスト
        if "results" in result and len(result["results"]) > 0:
            url = result["results"][0]["url"]
            print(f"\n抽出テスト URL: {url}")
            
            extract_args = {
                "what_is_your_intent": "特定のURLからのコンテンツ抽出テスト",
                "urls": [url],
                "include_images": False,
                "extract_depth": "basic"
            }
            
            extract_result = use_mcp_tool("Tavily Expert", "tavily_extract_tool", json.dumps(extract_args))
            print("\n=== 抽出結果 ===")
            if "extracted_content" in extract_result and len(extract_result["extracted_content"]) > 0:
                content = extract_result["extracted_content"][0].get("content", "")
                print(f"内容: {content[:150]}..." if len(content) > 150 else f"内容: {content}")
            else:
                print("抽出コンテンツがありません")
        
        return True
    
    except ImportError:
        print("エラー: use_mcp_toolモジュールをインポートできません。")
        return False
    
    except Exception as e:
        print(f"エラー: {e}")
        return False

def save_sample_env():
    """サンプルの.envファイルを保存"""
    env_path = ".env.sample"
    
    # ファイルの内容
    content = """# Tavily API設定
TAVILY_API_KEY=your_api_key_here

# モック設定（本番環境では削除または'false'に設定）
# USE_MOCK_TAVILY=true

# OpenAI API設定（データ抽出用）
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    # ファイルを書き込み
    with open(env_path, "w") as f:
        f.write(content)
    
    print(f"\nサンプル環境変数ファイル '{env_path}' を保存しました。")
    print("実際の使用時には、このファイルを '.env' にリネームし、APIキーを設定してください。")

def main():
    parser = argparse.ArgumentParser(description="Tavily API接続テスト")
    parser.add_argument("--mode", choices=["direct", "mcp", "both"], default="both",
                        help="テストモード: direct=直接API, mcp=MCPインターフェース, both=両方")
    parser.add_argument("--save-env", action="store_true",
                        help="サンプル.envファイルを保存")
    
    args = parser.parse_args()
    
    # テスト実行
    if args.mode in ["direct", "both"]:
        direct_result = test_direct_api()
    
    if args.mode in ["mcp", "both"]:
        mcp_result = test_mcp_interface()
    
    # サンプル.envファイルの保存
    if args.save_env:
        save_sample_env()
    
    # 結果の要約
    print("\n=== テスト結果の要約 ===")
    if args.mode in ["direct", "both"]:
        print(f"直接APIテスト: {'成功' if direct_result else '失敗'}")
    
    if args.mode in ["mcp", "both"]:
        print(f"MCPインターフェーステスト: {'成功' if mcp_result else '失敗'}")
    
    # APIキーが設定されていない場合の注意
    if not os.getenv("TAVILY_API_KEY"):
        print("\n注意: Tavily APIキーが設定されていません。")
        print("本番運用のためには、.envファイルまたは環境変数でTAVILY_API_KEYを設定してください。")

if __name__ == "__main__":
    main()
