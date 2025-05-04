import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from use_mcp_tool import use_mcp_tool

# .envファイルから環境変数をロード
load_dotenv()

# OpenAI APIキーを環境変数から取得
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_scholars_data(file_path):
    """Scholarデータをロードする"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def tavily_search(scholar_name, lang="ja"):
    """Tavily APIを使用して学者に関する情報を検索する"""
    # 検索クエリの構築
    if lang == "ja":
        query = f"{scholar_name} 統計学 疫学 公衆衛生学 業績 貢献 豆知識"
    else:
        query = f"{scholar_name} statistics epidemiology public health contributions achievements facts"
    
    what_is_your_intent = f"{scholar_name}に関する統計学・疫学・公衆衛生学への貢献と豆知識を調査するため"
    
    try:
        print(f"Tavilyで検索中: {query}")
        
        # Tavily APIのMCP Tool呼び出し
        arguments = {
            "what_is_your_intent": what_is_your_intent,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": 5
        }
        
        # JSON文字列に変換
        args_json = json.dumps(arguments)
        
        # MCP Toolを使用してTavily API呼び出し
        result = use_mcp_tool("Tavily Expert", "tavily_search_tool", args_json)
        
        # 結果をJSONデコード
        if isinstance(result, str):
            result = json.loads(result)
        
        return result
    except Exception as e:
        print(f"Tavily検索エラー: {e}")
        return {"results": []}

def extract_scholar_info_from_tavily(search_results, scholar_name, current_data):
    """Tavily検索結果から学者情報を抽出する"""
    # 検索結果のテキストを統合
    combined_text = ""
    if "results" in search_results:
        combined_text = "\n\n".join([
            f"ソース: {result.get('url', 'URL不明')}\n{result.get('content', '')}"
            for result in search_results.get("results", [])
        ])
    
    # OpenAI APIに送信するテキストの長さを制限
    max_text_length = 15000
    if len(combined_text) > max_text_length:
        combined_text = combined_text[:max_text_length]
    
    # ツール定義 (スキーマに基づく情報抽出用)
    tools = [{
        "type": "function",
        "function": {
            "name": "extract_scholar_info",
            "description": "Extract scholar information from search results",
            "parameters": {
                "type": "object",
                "properties": {
                    "contribution": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string", 
                                "description": "学者の統計学・疫学・公衆衛生学への貢献の詳細な説明"
                            },
                            "source": {
                                "type": "string",
                                "description": "この情報の最も信頼性の高いソースURL"
                            }
                        },
                        "description": "学者の主な学術的貢献"
                    },
                    "trivia": {
                        "type": "string",
                        "description": "学者に関する興味深い豆知識や逸話（学術的貢献とは別の、個人的な側面を示す情報）"
                    },
                    "triviaSource": {
                        "type": "string",
                        "description": "豆知識の情報源URL"
                    }
                },
                "required": []
            }
        }
    }]
    
    # システムプロンプト
    system_prompt = f"""
    あなたは学者に関する情報を抽出する専門家です。提供された検索結果から学者の統計・公衆衛生・疫学に関連した詳細情報を抽出してください。
    
    特に以下の2つの異なる種類の情報を区別して抽出してください：
    1. 貢献情報（contribution）: 学者の学術的・専門的業績、理論、発見などに関する客観的な説明
    2. 豆知識（trivia）: 学者の個人的なエピソード、あまり知られていない事実、興味深い逸話など
    
    日本語で回答を作成し、可能な限り信頼性の高い情報を抽出してください。
    存在しない情報については推測せず、空欄のままにしてください。
    """
    
    # ユーザープロンプト
    user_prompt = f"""
    以下の検索結果から学者 "{scholar_name}" に関する情報を抽出してください：
    
    {combined_text}
    """
    
    try:
        # 検索結果が空でないか確認
        if not combined_text:
            print(f"警告: {scholar_name}の検索結果が空です")
            return current_data
        
        # OpenAI APIリクエスト
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "extract_scholar_info"}}
        )
        
        tool_calls = response.choices[0].message.tool_calls
        
        if tool_calls:
            # ツール呼び出しから抽出された情報を取得
            function_args = json.loads(tool_calls[0].function.arguments)
            
            # 現在のデータをアップデート
            updated_data = current_data.copy()
            
            # contribution情報の更新（空でない場合のみ）
            if 'contribution' in function_args and function_args['contribution'].get('text'):
                updated_data['contribution']['text'] = function_args['contribution']['text']
                if function_args['contribution'].get('source'):
                    updated_data['contribution']['source'] = function_args['contribution']['source']
            
            # trivia情報の更新（空でない場合のみ）
            if 'trivia' in function_args and function_args['trivia']:
                updated_data['trivia'] = function_args['trivia']
                if 'triviaSource' in function_args and function_args['triviaSource']:
                    updated_data['triviaSource'] = function_args['triviaSource']
            
            return updated_data
        
        return current_data
    
    except Exception as e:
        print(f"Error extracting data: {e}")
        return current_data

def process_tavily_search_results(search_results):
    """Tavily検索結果を処理して標準化された形式に変換する"""
    # 実際のAPIレスポンスに合わせて結果を標準化
    processed_results = {"results": []}
    
    # search_resultsがNoneや空の場合は処理しない
    if not search_results:
        return processed_results
    
    # 検索結果を取得
    results = search_results.get("results", [])
    
    # 結果が文字列形式でエンコードされている場合はデコード
    if isinstance(results, str):
        try:
            import json
            results = json.loads(results)
        except:
            pass
    
    # answer情報も取得（利用可能な場合）
    answer = search_results.get("answer", "")
    
    # 結果を整形
    processed_results["results"] = results
    if answer:
        processed_results["answer"] = answer
    
    return processed_results

def main():
    # 元のJSONファイルを読み込む
    input_file = 'scholars_enhanced.json'
    output_file = 'scholars_enhanced_tavily.json'
    scholars = load_scholars_data(input_file)
    
    # 空データを持つ学者を特定
    incomplete_scholars = [
        scholar for scholar in scholars 
        if not scholar.get("contribution", {}).get("text") or not scholar.get("trivia")
    ]
    
    print(f"空データを持つ学者数: {len(incomplete_scholars)}")
    print("対象学者:", ", ".join([scholar['name']['ja'] if scholar.get('name', {}).get('ja') else scholar['id'] for scholar in incomplete_scholars]))
    
    # 処理結果の統計
    stats = {
        "total": len(incomplete_scholars),
        "updated_contribution": 0,
        "updated_trivia": 0,
        "fully_updated": 0,
        "no_changes": 0
    }
    
    # 各学者を処理
    for i, scholar in enumerate(incomplete_scholars):
        scholar_index = scholars.index(scholar)  # 元のリストでのインデックス
        scholar_name = scholar['name']['ja'] if scholar.get('name', {}).get('ja') else scholar['id']
        print(f"\n処理中 ({i+1}/{len(incomplete_scholars)}): {scholar_name}")
        
        # 更新前の状態を記録
        had_contribution = bool(scholar.get("contribution", {}).get("text"))
        had_trivia = bool(scholar.get("trivia"))
        
        # 日本語で検索
        ja_search_results = tavily_search(scholar_name, "ja")
        
        # 検索結果を処理
        ja_search_results = process_tavily_search_results(ja_search_results)
        
        # 結果から情報を抽出
        updated_scholar = extract_scholar_info_from_tavily(
            ja_search_results, scholar_name, scholar
        )
        
        # 英語版の名前がある場合は英語でも検索
        if scholar['name'].get('en') and scholar['name']['en'].strip():
            en_name = scholar['name']['en']
            print(f"英語名でも検索: {en_name}")
            
            # 英語で検索
            en_search_results = tavily_search(en_name, "en")
            
            # 検索結果を処理
            en_search_results = process_tavily_search_results(en_search_results)
            
            # 英語の結果からも情報を抽出して統合
            updated_scholar = extract_scholar_info_from_tavily(
                en_search_results, en_name, updated_scholar
            )
        
        # 更新後の状態を確認
        now_has_contribution = bool(updated_scholar.get("contribution", {}).get("text"))
        now_has_trivia = bool(updated_scholar.get("trivia"))
        
        # 統計を更新
        if now_has_contribution and not had_contribution:
            stats["updated_contribution"] += 1
        if now_has_trivia and not had_trivia:
            stats["updated_trivia"] += 1
        if now_has_contribution and now_has_trivia and (not had_contribution or not had_trivia):
            stats["fully_updated"] += 1
        if not now_has_contribution and not now_has_trivia:
            stats["no_changes"] += 1
        
        # 更新結果を表示
        print("  - 貢献情報:", "更新あり" if now_has_contribution and not had_contribution else "更新なし")
        print("  - 豆知識:", "更新あり" if now_has_trivia and not had_trivia else "更新なし")
        
        # 元のリストを更新
        scholars[scholar_index] = updated_scholar
        
        # API制限を回避するための短い遅延
        time.sleep(2)
    
    # 結果を新しいJSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scholars, f, ensure_ascii=False, indent=2)
    
    # 処理結果の統計を表示
    print("\n=== 処理結果の統計 ===")
    print(f"対象学者数: {stats['total']}")
    print(f"貢献情報が更新された学者数: {stats['updated_contribution']}")
    print(f"豆知識が更新された学者数: {stats['updated_trivia']}")
    print(f"全ての情報が更新された学者数: {stats['fully_updated']}")
    print(f"更新されなかった学者数: {stats['no_changes']}")
    print(f"\n更新完了！結果は {output_file} に保存されました")

if __name__ == "__main__":
    main()
