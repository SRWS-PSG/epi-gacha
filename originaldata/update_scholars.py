import json
import os
import requests
from bs4 import BeautifulSoup
import time
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルから環境変数をロード
load_dotenv()

# OpenAI APIキーを環境変数から取得
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_scholars_data(file_path):
    """Scholarデータをロードする"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_webpage_text(url):
    """URLからウェブページのテキストを取得する"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # レスポンスのエンコーディングを設定（文字化け対策）
        response.encoding = response.apparent_encoding
        
        # BeautifulSoupを使ってHTMLからテキストを抽出
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # スクリプトとスタイルタグを削除
        for script in soup(["script", "style"]):
            script.extract()
        
        # テキストを取得
        text = soup.get_text(separator=' ', strip=True)
        
        # 長いテキストを適切な長さに切り詰める (APIコンテキスト制限対応)
        if len(text) > 15000:
            text = text[:15000]
        
        return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_scholar_info(url, webpage_text, current_data):
    """OpenAI APIを使用してウェブページテキストから学者情報を抽出する"""
    if not webpage_text:
        return current_data
    
    # スキーマに基づいて学者データのプロパティを抽出するためのツール定義
    tools = [{
        "type": "function",
        "function": {
            "name": "extract_scholar_info",
            "description": "Extract scholar information from webpage text",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "object",
                        "properties": {
                            "en": {"type": "string", "description": "Scholar's name in English"},
                            "ja": {"type": "string", "description": "Scholar's name in Japanese"}
                        },
                        "description": "Scholar's name in both English and Japanese"
                    },
                    "affiliation": {
                        "type": "string",
                        "description": "Scholar's affiliation (university, research institution, etc.)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags related to scholar's field (e.g., 'Statistics', 'Causal Inference', etc.)"
                    },
                    "rarity": {
                        "type": "string",
                        "enum": ["N", "R", "SR", "SSR"],
                        "description": "Rarity classification of the scholar based on their historical significance"
                    },
                    "highlights": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Title of the highlight (work, publication, etc.)"},
                                "type": {"type": "string", "description": "Type of highlight (book, paper, etc.)"},
                                "year": {"type": "integer", "description": "Year of publication or creation"},
                                "doi": {"type": "string", "description": "DOI identifier if available"}
                            }
                        },
                        "description": "List of notable works or highlights of the scholar"
                    },
                    "contribution": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Description of the scholar's contribution to their field"}
                        },
                        "description": "Scholar's main contribution to their field"
                    },
                    "trivia": {
                        "type": "string",
                        "description": "Interesting trivia or fact about the scholar"
                    }
                },
                "required": []
            }
        }
    }]
    
    try:
        system_prompt = f"""
        あなたは学者に関する情報を抽出する専門家です。提供されたウェブページのテキストから学者の統計・公衆衛生・疫学に関連した詳細情報を抽出してください。
        日本語で回答を作成し、可能な限り多くの情報を抽出してください。
        存在しない情報については推測せず、空欄のままにしてください。
        """
        
        user_prompt = f"""
        以下のウェブページから学者 "{current_data['name']['ja'] or current_data['id']}" に関する情報を抽出してください。
        ソースURL: {url}
        
        ウェブページ内容:
        {webpage_text}
        """
        
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
            
            # 現在のデータをアップデート (IDとsourcesは保持)
            updated_data = current_data.copy()
            
            # 名前の更新（空でない場合のみ）
            if 'name' in function_args:
                if function_args['name'].get('en') and function_args['name']['en'].strip():
                    updated_data['name']['en'] = function_args['name']['en']
                if function_args['name'].get('ja') and function_args['name']['ja'].strip():
                    updated_data['name']['ja'] = function_args['name']['ja']
            
            # その他のフィールドの更新（空でない場合のみ）
            if 'affiliation' in function_args and function_args['affiliation']:
                updated_data['affiliation'] = function_args['affiliation']
            
            if 'tags' in function_args and function_args['tags']:
                updated_data['tags'] = function_args['tags']
            
            # rarityは更新しない（ユーザー指示により）
            # if 'rarity' in function_args and function_args['rarity']:
            #     updated_data['rarity'] = function_args['rarity']
            
            if 'highlights' in function_args and function_args['highlights']:
                updated_data['highlights'] = function_args['highlights']
            
            if 'contribution' in function_args and function_args['contribution'].get('text'):
                updated_data['contribution']['text'] = function_args['contribution']['text']
                # sourceは変更しない
            
            if 'trivia' in function_args and function_args['trivia']:
                updated_data['trivia'] = function_args['trivia']
            
            return updated_data
        
        return current_data
    
    except Exception as e:
        print(f"Error extracting data for {url}: {e}")
        return current_data

def main():
    # 元のJSONファイルを読み込む
    input_file = 'scholars_updated.json'
    output_file = 'scholars_enhanced.json'
    scholars = load_scholars_data(input_file)
    
    # 各スカラーを処理
    for i, scholar in enumerate(scholars):
        print(f"Processing scholar {i+1}/{len(scholars)}: {scholar['id']}")
        
        # URLが存在する場合、そのURLからデータを取得
        if scholar['sources'] and len(scholar['sources']) > 0:
            # 最初のURLを処理
            url = scholar['sources'][0]
            print(f"Fetching data from: {url}")
            
            # ウェブページからテキストを取得
            webpage_text = fetch_webpage_text(url)
            
            if webpage_text:
                # APIを使用してデータを抽出し、スカラーデータを更新
                scholars[i] = extract_scholar_info(url, webpage_text, scholar)
                
                # API制限を回避するための短い遅延
                time.sleep(1)
            else:
                print(f"Could not fetch content from {url}")
    
    # 結果を新しいJSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scholars, f, ensure_ascii=False, indent=2)
    
    print(f"Enhancement completed! Results saved to {output_file}")

if __name__ == "__main__":
    main()
