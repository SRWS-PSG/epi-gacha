def use_mcp_tool(server_name, tool_name, arguments):
    """
    MCPツールを使用する関数。
    特定のサーバー/ツールの場合は直接APIを呼び出し、
    それ以外はMCPプロトコルを使用します。
    
    Args:
        server_name: MCPサーバー名
        tool_name: 使用するツール名
        arguments: ツールに渡す引数（JSON文字列）
    
    Returns:
        ツールの実行結果
    """
    import json
    import os
    
    # 引数をデコード
    args = json.loads(arguments) if isinstance(arguments, str) else arguments
    
    # Tavilyサーバーとtavily_search_toolの場合の処理
    if server_name == "Tavily Expert" and tool_name == "tavily_search_tool":
        # 環境変数 USE_MOCK_TAVILY が設定されている場合はモックデータを使用
        if os.getenv("USE_MOCK_TAVILY", "").lower() in ("true", "1", "yes"):
            return _use_mock_tavily_search(args)
        else:
            # 実際のTavily APIを使用
            try:
                from tavily_api import search
                query = args.get("query", "")
                search_depth = args.get("search_depth", "basic")
                include_answer = args.get("include_answer", True)
                max_results = args.get("max_results", 5)
                
                # その他のパラメータを抽出
                tavily_args = {k: v for k, v in args.items() 
                               if k not in ("what_is_your_intent", "query", "search_depth", 
                                           "include_answer", "max_results")}
                
                print(f"Tavily APIで検索: {query}")
                return search(
                    query=query,
                    search_depth=search_depth,
                    include_answer=include_answer,
                    max_results=max_results,
                    **tavily_args
                )
            except ImportError:
                print("警告: tavily_api モジュールが見つかりません。モックデータを使用します。")
                return _use_mock_tavily_search(args)
            except Exception as e:
                print(f"Tavily API エラー: {e}")
                print("警告: Tavily API呼び出しに失敗しました。モックデータを使用します。")
                return _use_mock_tavily_search(args)
    
    # Tavilyサーバーとtavily_extract_toolの場合の処理
    elif server_name == "Tavily Expert" and tool_name == "tavily_extract_tool":
        # 環境変数 USE_MOCK_TAVILY が設定されている場合はモックデータを使用
        if os.getenv("USE_MOCK_TAVILY", "").lower() in ("true", "1", "yes"):
            return _use_mock_tavily_extract(args)
        else:
            # 実際のTavily APIを使用
            try:
                from tavily_api import extract
                urls = args.get("urls", [])
                include_images = args.get("include_images", False)
                extract_depth = args.get("extract_depth", "basic")
                
                print(f"Tavily APIで抽出: {urls}")
                return extract(
                    urls=urls,
                    include_images=include_images,
                    extract_depth=extract_depth
                )
            except ImportError:
                print("警告: tavily_api モジュールが見つかりません。モックデータを使用します。")
                return _use_mock_tavily_extract(args)
            except Exception as e:
                print(f"Tavily API エラー: {e}")
                print("警告: Tavily API呼び出しに失敗しました。モックデータを使用します。")
                return _use_mock_tavily_extract(args)
    
    # その他のMCPツールの場合（未実装）
    print(f"警告: {server_name}の{tool_name}は未実装です。空の結果を返します。")
    return {}

def _use_mock_tavily_search(args):
    """Tavily検索のモックデータを返す内部関数"""
    query = args.get("query", "")
    print(f"Tavily Expertサーバーで検索（モック）: {query}")
    
    # 模擬検索結果
    mock_results = {
        "results": [
            {
                "url": "https://example.com/scholar1",
                "title": f"About {query.split()[0]}",
                "content": f"{query.split()[0]}は統計学において重要な貢献をした。主な業績には確率論の研究があり、特に...",
                "score": 0.95
            },
            {
                "url": "https://example.com/scholar2",
                "title": f"{query.split()[0]}の生涯と業績",
                "content": f"{query.split()[0]}は1900年に生まれ、大学で数学を学んだ後、統計学の分野で革新的な理論を展開した。個人的には音楽を愛し、ピアノを演奏することが趣味だった。",
                "score": 0.85
            },
            {
                "url": "https://example.com/scholar3",
                "title": f"{query.split()[0]}に関する豆知識",
                "content": f"あまり知られていないが、{query.split()[0]}は料理の腕前も良く、特に伝統的なパイ作りを得意としていた。",
                "score": 0.75
            }
        ],
        "answer": f"{query.split()[0]}は統計学・疫学分野で重要な貢献をした学者で、主に確率論と統計的推論の分野で革新的な理論を展開した。個人的な側面では音楽を愛し、料理も得意だったという。"
    }
    
    return mock_results

def _use_mock_tavily_extract(args):
    """Tavily抽出のモックデータを返す内部関数"""
    urls = args.get("urls", [])
    if isinstance(urls, str):
        urls = [urls]
    
    print(f"Tavily Expertサーバーで抽出（モック）: {urls}")
    
    # 模擬抽出結果
    mock_results = {
        "extracted_content": [
            {
                "url": url,
                "content": f"このページは{url}からの抽出コンテンツです。実際のAPIでは、ページの本文が抽出されます。",
                "title": f"{url.split('/')[-1].capitalize()} Page Title"
            } for url in urls
        ]
    }
    
    return mock_results
