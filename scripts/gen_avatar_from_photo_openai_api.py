#!/usr/bin/env python
"""
特定学者のソースURLから顔写真を取得し、OpenAI API（GPT-image-1）を使ってイラスト生成するデバッグ関数

使い方:
python scripts/gen_avatar_from_photo_openai_api.py

環境変数:
- OPENAI_API_KEY: OpenAI APIキー

注意:
このスクリプトを実行するには、組織が認証済みのOpenAIアカウントが必要です。
GPT-image-1モデルを使用するには、OpenAIの組織認証が必要です。
"""

import json
import os
import time
import base64
from pathlib import Path
import io
import requests
from bs4 import BeautifulSoup
from PIL import Image
from openai import OpenAI

# OpenAI APIクライアントの初期化
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # APIキーが環境変数にない場合は、ここに直接入力してください
    api_key = "your_api_key_here"
    if api_key == "your_api_key_here":
        print("警告: OpenAI APIキーが設定されていません。")
        print("スクリプト内の'your_api_key_here'を実際のAPIキーに書き換えるか、")
        print("環境変数OPENAI_API_KEYを設定してください。")

client = OpenAI(api_key=api_key)
OUT_DIR = Path("avatars")
OUT_DIR.mkdir(exist_ok=True)

# イラスト生成用のプロンプトテンプレート
PROMPT_TEMPLATE = (
    "Based on the reference portrait of {name_en}, "
    "create a flat pastel portrait, facing forward, with a 4-colour palette, thick outline, "
    "and solid background. Keep the distinct facial features, expression, and character, "
    "but simplify into a stylized cartoon illustration. No text, no watermark."
)

def get_scholar_by_id(scholar_id):
    """scholars_enhanced.jsonから指定IDの学者データを取得"""
    try:
        with open("scholars_enhanced.json", "r", encoding="utf-8") as f:
            scholars = json.load(f)
            for scholar in scholars:
                if scholar["id"] == scholar_id:
                    return scholar
        return None
    except Exception as e:
        print(f"Error loading scholar data: {e}")
        return None

def describe_person_from_url(url, name_en):
    """URLから人物の説明を生成する関数"""
    try:
        print(f"Accessing URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # HTMLからテキストを抽出
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # タイトルとメタディスクリプションを取得
        title = soup.title.string if soup.title else ""
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")
        
        # Wikipediaの場合、最初の段落を抽出
        first_paragraphs = []
        if "wikipedia" in url.lower():
            # 英語版Wikipediaの場合
            paragraphs = soup.select("#mw-content-text p")
            # 日本語版Wikipediaの場合
            if not paragraphs:
                paragraphs = soup.select(".mw-parser-output p")
            
            # 最初の段落を取得（空でない最初の3つ）
            count = 0
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 100:  # 短すぎる段落は除外
                    first_paragraphs.append(text)
                    count += 1
                    if count >= 3:
                        break
        
        # OpenAIを使用して人物の外見を説明させる
        prompt = f"""
        The following text is from a webpage about {name_en}. Create a detailed visual description of this person's face, focusing on:
        - Facial structure and features
        - Eye shape and color
        - Hairstyle and color
        - Notable facial characteristics
        - Expression and demeanor
        - Age characteristics
        - Any distinguishing features
        
        Use visual details only, not biographical information. Keep the description objective.
        
        Text from webpage:
        Title: {title}
        Description: {meta_desc}
        Content: {' '.join(first_paragraphs)[:1500]}
        """
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a visual description assistant. Provide detailed visual descriptions of people based on text information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        description = response.choices[0].message.content
        print(f"Generated description of {name_en}")
        return description
    
    except Exception as e:
        print(f"Error generating description from URL: {e}")
        return f"A portrait of {name_en}, a distinguished academic figure with a thoughtful expression."

def get_scholar_description(scholar):
    """学者のJSONデータから画像生成用の説明を生成"""
    try:
        name_en = scholar["name"]["en"]
        
        # 貢献と豆知識を取得
        contribution = scholar.get("contribution", {}).get("text", "")
        trivia = scholar.get("trivia", "")
        
        # タグ（専門分野）を取得
        tags = scholar.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""
        
        # 所属を取得
        affiliation = scholar.get("affiliation", "")
        
        # 業績を取得
        highlights = []
        for h in scholar.get("highlights", []):
            if h.get("title"):
                highlights.append(h["title"])
        highlights_str = ", ".join(highlights[:3]) if highlights else ""
        
        # 画像生成用の説明を構築
        description = f"A portrait of {name_en}, "
        
        # 専門分野があれば追加
        if tags_str:
            description += f"a {tags_str} specialist"
            if affiliation:
                description += f" affiliated with {affiliation}"
            description += ". "
        elif affiliation:
            description += f"affiliated with {affiliation}. "
            
        # 主な業績があれば追加（視覚的特徴の参考として）
        if highlights_str:
            description += f"Known for {highlights_str}. "
            
        # 豆知識があれば追加（個性を出すため）
        if trivia:
            description += f"Interesting note: {trivia}"
            
        print(f"Generated description from JSON data for {name_en}")
        return description
        
    except Exception as e:
        print(f"Error generating description from JSON: {e}")
        return f"A portrait of {name_en}, a distinguished academic figure."

def download_reference_image(url):
    """URLから画像をダウンロードする"""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        print(f"Reference image downloaded: {img.format} {img.size}")
        return img
    except Exception as e:
        print(f"Error downloading reference image: {e}")
        return None

def extract_image_from_webpage(url):
    """WebページからWikipediaの顔写真を抽出する"""
    try:
        print(f"Looking for images on: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Wikipediaのinfoboxから画像を探す
        if "wikipedia" in url.lower():
            infobox_imgs = soup.select('.infobox img, .biography .image img, .thumb img')
            for img in infobox_imgs:
                src = img.get('src')
                if src:
                    if not src.startswith('http'):
                        src = 'https:' + src if src.startswith('//') else 'https://' + url.split('/')[2] + src
                    # 一定サイズ以上の画像のみ
                    width = img.get('width')
                    height = img.get('height')
                    if width and height and int(width) > 100 and int(height) > 100:
                        print(f"Found portrait image: {src}")
                        return src
        
        # 一般的なページからプロフィール画像のように見える画像を探す
        candidate_imgs = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
                
            # 完全なURLに変換
            if not src.startswith('http'):
                src = 'https:' + src if src.startswith('//') else 'https://' + url.split('/')[2] + src
                
            # 画像サイズを確認
            width = img.get('width')
            height = img.get('height')
            
            # 一定サイズ以上の画像をリストに追加
            if width and height and int(width) > 150 and int(height) > 150:
                candidate_imgs.append((src, int(width) * int(height)))
        
        # サイズ順にソートして最大の画像を返す
        if candidate_imgs:
            candidate_imgs.sort(key=lambda x: x[1], reverse=True)
            print(f"Selected largest image: {candidate_imgs[0][0]}")
            return candidate_imgs[0][0]
            
        print("No suitable images found on the page")
        return None
        
    except Exception as e:
        print(f"Error extracting image from webpage: {e}")
        return None

def generate_avatar_from_reference_image(name_en, reference_image_path):
    """参照画像をもとにアバター画像を生成"""
    try:
        # プロンプトの作成
        prompt = f"""
        Create a flat pastel portrait of {name_en} based on the reference image.
        
        Style guidelines:
        - Facing forward
        - 4-colour palette
        - Thick outline
        - Solid background
        - Simple, stylized cartoon illustration
        - No text or watermarks
        """
        
        print(f"Generating avatar with reference image using GPT-image-1")
        
        # GPT-image-1でイラストを生成（要組織認証）
        response = client.images.edit(
            model="gpt-image-1",
            image=open(reference_image_path, "rb"),
            prompt=prompt
        )
        
        # base64形式で画像データを取得
        image_base64 = response.data[0].b64_json
        image_data = base64.b64decode(image_base64)
        
        print("Generated avatar successfully")
        return image_data
    
    except Exception as e:
        print(f"Error generating avatar with GPT-image-1: {e}")
        return None

def generate_default_image(name_en, description=None):
    """デフォルトのイラストを生成する（説明またはデフォルト設定から）"""
    try:
        if description:
            prompt_text = f"""
            Create a flat pastel portrait of {name_en} based on this description: 
            {description}
            """
        else:
            prompt_text = f"""
            Create a flat pastel portrait of {name_en} as an academic or scholar.
            Imagine a professional looking person with thoughtful expression.
            """
            
        prompt = f"""
        {prompt_text}
        
        Style guidelines:
        - Facing forward
        - 4-colour palette
        - Thick outline
        - Solid background
        - Simple, stylized cartoon illustration
        - No text or watermarks
        """
        
        print(f"Generating default image with GPT-image-1")
        
        # ダミー画像を生成（白い背景に基本的な顔の形）
        dummy_img = Image.new('RGB', (512, 512), color=(255, 255, 255))
        dummy_path = OUT_DIR / "dummy_reference.jpg"
        dummy_img.save(dummy_path)
        
        # GPT-image-1でイラストを生成（要組織認証）
        response = client.images.edit(
            model="gpt-image-1",
            image=open(dummy_path, "rb"),
            prompt=prompt
        )
        
        # base64形式で画像データを取得
        image_base64 = response.data[0].b64_json
        image_data = base64.b64decode(image_base64)
        
        print("Generated default avatar successfully")
        return image_data
        
    except Exception as e:
        print(f"Error generating default image: {e}")
        return None

def debug_generate_from_photo(scholar_id):
    """特定学者のソースURLから顔写真を取得し、イラスト化するデバッグ関数"""
    # 1. スキーマから指定IDの学者データを取得
    scholar = get_scholar_by_id(scholar_id)
    if not scholar:
        print(f"Scholar with ID {scholar_id} not found")
        return
    
    print(f"Processing scholar: {scholar['name']['en']} ({scholar_id})")
    
    # 2. JSONデータから説明文を生成
    json_description = get_scholar_description(scholar)
    print(f"Generated description from JSON data: {json_description}")
    
    # 3. sourcesからURLを取得し顔写真を抽出
    if not scholar.get('sources') or len(scholar['sources']) == 0:
        print(f"No source URLs found for scholar {scholar_id}")
        # JSONデータのみを使用
        avatar_data = generate_default_image(scholar['name']['en'], json_description)
        if not avatar_data:
            print(f"Failed to generate image from JSON description. Aborting.")
            return
    else:
        source_url = scholar['sources'][0]
        print(f"Using source URL: {source_url}")
        
        # URLから顔写真を抽出
        img_url = extract_image_from_webpage(source_url)
        if not img_url:
            print(f"Could not extract image from webpage. Using JSON description.")
            avatar_data = generate_default_image(scholar['name']['en'], json_description)
            if not avatar_data:
                print(f"Failed to generate image from JSON description. Aborting.")
                return
        else:
            # 顔写真をダウンロードして一時ファイルに保存
            temp_img_path = OUT_DIR / f"{scholar_id}_reference.jpg"
            img = download_reference_image(img_url)
            if not img:
                print(f"Failed to download reference image. Using JSON description.")
                avatar_data = generate_default_image(scholar['name']['en'], json_description)
                if not avatar_data:
                    print(f"Failed to generate image from JSON description. Aborting.")
                    return
            else:
                img.save(temp_img_path)
                print(f"Saved reference image to {temp_img_path}")
                
                # 参照画像をもとにイラスト生成
                avatar_data = generate_avatar_from_reference_image(scholar['name']['en'], temp_img_path)
                if not avatar_data:
                    print(f"Failed to generate avatar from reference. Using JSON description.")
                    avatar_data = generate_default_image(scholar['name']['en'], json_description)
                    if not avatar_data:
                        print(f"Failed to generate image from JSON description. Aborting.")
                        return
    
    # 5. 結果を保存して表示
    avatar_path = OUT_DIR / f"{scholar_id}.png"
    with open(avatar_path, "wb") as f:
        f.write(avatar_data)
    
    print(f"Successfully generated and saved avatar to {avatar_path}")
    return avatar_path

if __name__ == "__main__":
    print("==================================================")
    print("注意: このスクリプトはOpenAI APIの組織認証が必要です")
    print("GPT-image-1モデルを使用するには、OpenAIの組織認証が必要です")
    print("エラーメッセージ: 'Your organization must be verified to use the model `gpt-image-1`'")
    print("https://platform.openai.com/settings/organization/general で組織認証を行ってください")
    print("==================================================")
    
    # APIキーがない場合は入力を求める
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("OpenAI APIキーが設定されていません。")
        api_key = input("OpenAI APIキーを入力してください: ").strip()
        os.environ["OPENAI_API_KEY"] = api_key
        client = OpenAI(api_key=api_key)

    # 実行するかどうか確認
    proceed = input("続行しますか？ (y/n): ").strip().lower()
    if proceed != 'y':
        print("スクリプトを終了します")
        exit(0)

    # デバッグテスト - ポール・ローゼンバウムの画像を生成
    scholar_id = "rosenbaum2025"
    avatar_path = debug_generate_from_photo(scholar_id)
    
    if avatar_path:
        print(f"\nDebug test completed successfully. Avatar saved to {avatar_path}")
        
        # 成功した場合、JSONを更新するか尋ねる
        update_json = input("\nscholars_enhanced.jsonにアバターパスを更新しますか？ (y/n): ").strip().lower()
        if update_json == 'y':
            with open("scholars_enhanced.json", "r", encoding="utf-8") as f:
                scholars = json.load(f)
                
            for scholar in scholars:
                if scholar["id"] == scholar_id:
                    scholar["avatar"] = str(avatar_path)
                    break
                    
            with open("scholars_enhanced.json", "w", encoding="utf-8") as f:
                json.dump(scholars, f, ensure_ascii=False, indent=2)
            
            print(f"scholars_enhanced.jsonを更新しました")
    else:
        print("\nDebug test failed. See errors above.")
