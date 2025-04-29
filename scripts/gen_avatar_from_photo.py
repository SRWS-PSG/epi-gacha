#!/usr/bin/env python
"""
特定学者のソースURLから顔写真を取得し、イラスト生成するデバッグ関数

使い方:
python scripts/gen_avatar_from_photo.py

環境変数:
- GOOGLE_API_KEY: Google Gemini APIキー
"""

import json
import os
import time
import base64
import csv
from pathlib import Path
import io
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import google.generativeai as genai
from google.generativeai import types

# Google Gemini APIクライアントの初期化
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # APIキーが環境変数にない場合は、ここに直接入力してください
    api_key = "your_api_key_here"
    if api_key == "your_api_key_here":
        print("警告: Google APIキーが設定されていません。")
        print("スクリプト内の'your_api_key_here'を実際のAPIキーに書き換えるか、")
        print("環境変数GOOGLE_API_KEYを設定してください。")

# Wikipediaリクエスト用のUser-Agentヘッダー
USER_AGENT = 'Epi-Gacha/1.0 (https://github.com/SRWS-PSG/epi-gacha; youkiti@gmail.com) Python/3.x requests/2.x'

genai.configure(api_key=api_key)

# 出力ディレクトリの設定
OUT_DIR = Path("avatars")
OUT_DIR.mkdir(exist_ok=True)

# 参照画像用ディレクトリの設定
REF_DIR = Path("reference_photos")
REF_DIR.mkdir(exist_ok=True)

# 画像が見つからなかった学者の情報を記録するCSVファイル
MISSING_PHOTOS_CSV = Path("missing_photos.csv")

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
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, timeout=10, headers=headers)
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
        
        # Geminiを使用して人物の外見を説明させる
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
        
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        description = response.text
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
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, stream=True, timeout=10, headers=headers)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        
        if img.format == 'GIF' or img.mode == 'P':
            img = img.convert('RGB')
            
        print(f"Reference image downloaded: {img.format} {img.size} (mode: {img.mode})")
        return img
    except Exception as e:
        print(f"Error downloading reference image: {e}")
        return None

def extract_image_from_webpage(url):
    """WebページからWikipediaの顔写真を抽出する"""
    try:
        print(f"Looking for images on: {url}")
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Wikipediaの場合は特別な処理
        if "wikipedia" in url.lower():
            print("Wikipediaページを処理しています")
            
            # 方法1: infoboxの画像を探す（優先度高）
            infobox_imgs = soup.select('.infobox img, .biography .image img')
            for img in infobox_imgs:
                src = img.get('src')
                if src:
                    if not src.startswith('http'):
                        src = 'https:' + src if src.startswith('//') else 'https://' + url.split('/')[2] + src
                    # 一定サイズ以上の画像のみ
                    width = img.get('width')
                    height = img.get('height')
                    if width and height and int(width) > 100 and int(height) > 100:
                        print(f"Found portrait image in infobox: {src}")
                        return src
            
            # 方法2: 冒頭の画像を探す
            thumb_imgs = soup.select('.thumb img, .mw-parser-output > div > a > img')
            for img in thumb_imgs:
                src = img.get('src')
                if src:
                    if not src.startswith('http'):
                        src = 'https:' + src if src.startswith('//') else 'https://' + url.split('/')[2] + src
                    width = img.get('width')
                    height = img.get('height')
                    if width and height and int(width) > 100 and int(height) > 100:
                        print(f"Found image in article body: {src}")
                        return src
            
            # 方法3: Wikipediaの画像ファイル名からCommons URLを作成
            # 例: File:Paul_Rosenbaum.jpg -> https://commons.wikimedia.org/wiki/File:Paul_Rosenbaum.jpg
            file_links = soup.select('a[href*="File:"], a[href*="ファイル:"]')
            for link in file_links:
                href = link.get('href', '')
                if 'File:' in href or 'ファイル:' in href:
                    # ファイル名を抽出
                    filename = href.split('File:')[-1] if 'File:' in href else href.split('ファイル:')[-1]
                    if '.' in filename and any(ext in filename.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        commons_url = f"https://commons.wikimedia.org/wiki/File:{filename}"
                        try:
                            # Commonsページにアクセス
                            headers = {'User-Agent': USER_AGENT}
                            commons_response = requests.get(commons_url, timeout=10, headers=headers)
                            commons_soup = BeautifulSoup(commons_response.content, 'html.parser')
                            # 画像URLを取得
                            img = commons_soup.select_one('.fullImageLink img')
                            if img and img.get('src'):
                                img_src = img.get('src')
                                if not img_src.startswith('http'):
                                    img_src = 'https:' + img_src if img_src.startswith('//') else 'https://commons.wikimedia.org' + img_src
                                print(f"Found image via Commons: {img_src}")
                                return img_src
                        except Exception as e:
                            print(f"Commons access error: {e}")
        
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

def check_reference_photo(scholar_id):
    """参照画像フォルダ内にIDに対応する画像があるか確認"""
    # サポートされる画像形式
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    for ext in extensions:
        ref_path = REF_DIR / f"{scholar_id}{ext}"
        if ref_path.exists():
            print(f"Found manual reference photo: {ref_path}")
            return ref_path
    
    print(f"No manual reference photo found for {scholar_id}")
    return None

def add_to_missing_photos_csv(scholar_id, name_en, name_ja, source_url=None, status="missing"):
    """学者の情報をCSVに追記（画像がない場合だけでなく、処理状況も記録）
    
    status:
    - "missing": 画像が見つからず、手動での追加が必要
    - "manual_added": 手動で参照画像が追加済み
    - "generated": アバター生成成功
    """
    # CSVファイルが存在するか確認
    file_exists = MISSING_PHOTOS_CSV.exists()
    
    # ヘッダー情報の定義（新しい形式）
    headers = ['scholar_id', 'name_en', 'name_ja', 'search_url', 'status']
    
    # 既存のエントリとヘッダー情報を読み込む
    existing_data = {}
    existing_headers = None
    if file_exists:
        try:
            with open(MISSING_PHOTOS_CSV, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                # ヘッダー行を読み込む
                existing_headers = next(reader, headers)
                
                # ヘッダーが古い形式の場合（statusがない）
                if len(existing_headers) < len(headers):
                    existing_headers = headers
                
                # データ行を読み込む
                for row in reader:
                    if row and len(row) > 0:
                        # 古い形式のデータ行の場合、statusカラムを追加
                        if len(row) < len(headers):
                            row.append("missing")
                        
                        # 辞書に格納（IDをキーとして）
                        existing_data[row[0]] = row
        except Exception as e:
            print(f"Warning: Error reading existing CSV: {e}")
    
    # データを準備
    new_row = [scholar_id, name_en, name_ja, source_url or '', status]
    
    # CSVを更新（既存エントリの更新または新規追加）
    try:
        mode = 'w'  # 書き換えモード
        with open(MISSING_PHOTOS_CSV, mode, encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # ヘッダー行を書き込む
            writer.writerow(existing_headers if existing_headers else headers)
            
            # 既存データをアップデート
            if scholar_id in existing_data:
                existing_data[scholar_id] = new_row
                print(f"Updated {name_en} ({scholar_id}) in {MISSING_PHOTOS_CSV.name} with status: {status}")
            else:
                existing_data[scholar_id] = new_row
                print(f"Added {name_en} ({scholar_id}) to {MISSING_PHOTOS_CSV.name} with status: {status}")
            
            # 全データを書き込む
            for row in existing_data.values():
                writer.writerow(row)
    except Exception as e:
        print(f"Error updating {MISSING_PHOTOS_CSV.name}: {e}")

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
        
        print(f"Generating avatar with reference image using Gemini")
        
        # 画像を開く
        image = Image.open(reference_image_path)
        
        # Geminiモデルを使用して画像生成
        model = genai.GenerativeModel("gemini-pro-vision")
        try:
            response = model.generate_content(
                contents=[prompt, image]
            )
        except Exception as e:
            print(f"API呼び出しエラー: {e}")
            print(f"詳細: {str(e)}")
            raise
        
        # レスポンスから画像データを抽出
        image_data = None
        try:
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None and part.inline_data.mime_type.startswith('image/'):
                    image_data = part.inline_data.data
                    print(f"画像データを取得しました: {part.inline_data.mime_type}")
                    break
            
            if not image_data:
                raise Exception("No image data found in response")
        except Exception as e:
            print(f"画像データ抽出エラー: {e}")
            print(f"レスポンス構造: {response}")
            raise
            
        print("Generated avatar successfully")
        return image_data
    
    except Exception as e:
        print(f"Error generating avatar with Gemini: {e}")
        return None

def debug_generate_from_photo(scholar_id):
    """特定学者のソースURLから顔写真を取得し、イラスト化するデバッグ関数"""
    # 1. スキーマから指定IDの学者データを取得
    scholar = get_scholar_by_id(scholar_id)
    if not scholar:
        print(f"Scholar with ID {scholar_id} not found")
        return
    
    name_en = scholar['name']['en']
    name_ja = scholar['name'].get('ja', '')
    
    print(f"Processing scholar: {name_en} ({scholar_id})")
    
    # 2. 参照画像を取得するソースをチェック
    reference_image_path = None
    source_url = None
    
    # 2.1 まず手動で追加された参照画像をチェック
    manual_ref_path = check_reference_photo(scholar_id)
    if manual_ref_path:
        reference_image_path = manual_ref_path
        print(f"Using manual reference photo from: {manual_ref_path}")
        # 手動参照画像が見つかったことを記録
        add_to_missing_photos_csv(scholar_id, name_en, name_ja, None, "manual_added")
    
    # 2.2 手動参照画像がなければウェブから取得を試みる
    if not reference_image_path:
        if not scholar.get('sources') or len(scholar['sources']) == 0:
            print(f"No source URLs found for scholar {scholar_id}")
            # missing_photos.csvに追記
            add_to_missing_photos_csv(scholar_id, name_en, name_ja)
            print(f"Please add a reference photo for {name_en} to {REF_DIR}")
            return None
        else:
            source_url = scholar['sources'][0]
            print(f"Using source URL: {source_url}")
            
            # URLから顔写真を抽出
            img_url = extract_image_from_webpage(source_url)
            if not img_url:
                print(f"Could not extract image from webpage.")
                # missing_photos.csvに追記
                add_to_missing_photos_csv(scholar_id, name_en, name_ja, source_url)
                print(f"Please add a reference photo for {name_en} to {REF_DIR}")
                return None
            else:
                # 顔写真をダウンロードして一時ファイルに保存
                temp_img_path = OUT_DIR / f"{scholar_id}_reference.jpg"
                img = download_reference_image(img_url)
                if not img:
                    print(f"Failed to download reference image.")
                    add_to_missing_photos_csv(scholar_id, name_en, name_ja, source_url)
                    print(f"Please add a reference photo for {name_en} to {REF_DIR}")
                    return None
                else:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(temp_img_path)
                    print(f"Saved reference image to {temp_img_path}")
                    reference_image_path = temp_img_path
    
    # 参照画像が存在する場合、アバター生成を実行
    if reference_image_path:
        # 参照画像をもとにイラスト生成
        avatar_data = generate_avatar_from_reference_image(name_en, reference_image_path)
        if not avatar_data:
            print(f"Failed to generate avatar from reference.")
            return None
        
        # 結果を保存
        avatar_path = OUT_DIR / f"{scholar_id}.png"
        try:
            # base64エンコードされているか確認
            if isinstance(avatar_data, str) and avatar_data.startswith(('data:image', 'iVBOR', '/9j/')):
                # base64エンコードされた文字列からプレフィックスを削除
                if avatar_data.startswith('data:image'):
                    # 例: 'data:image/png;base64,iVBORw0...' -> 'iVBORw0...'
                    avatar_data = avatar_data.split(',', 1)[1]
                print("Base64エンコードされたデータをデコードします")
                avatar_data = base64.b64decode(avatar_data)
            
            # バイナリデータとして書き込み
            with open(avatar_path, "wb") as f:
                f.write(avatar_data)
            print(f"画像を保存しました：{avatar_path}")
        except Exception as e:
            print(f"画像の保存中にエラーが発生しました: {e}")
            print(f"データタイプ: {type(avatar_data)}")
            if isinstance(avatar_data, str) and len(avatar_data) > 100:
                print(f"データの先頭: {avatar_data[:100]}...")
            raise
        
        print(f"Successfully generated and saved avatar to {avatar_path}")
        # アバター生成成功を記録
        add_to_missing_photos_csv(scholar_id, name_en, name_ja, source_url, "generated")
        return avatar_path
    
    return None

if __name__ == "__main__":
    # APIキーがない場合は入力を求める
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("Google APIキーが設定されていません。")
        api_key = input("Google APIキーを入力してください: ").strip()
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)

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
        print("\nDebug test failed or no reference photo was available.")
        print("Check missing_photos.csv for a list of scholars without reference photos.")
