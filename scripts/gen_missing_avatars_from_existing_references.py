#!/usr/bin/env python
"""
既存の参照画像からアバター画像を生成するスクリプト

このスクリプトは、avatarsディレクトリ内の_referenceファイルがあるが、
対応する.pngファイルがない学者のアバター画像を生成します。
Wikipediaからの画像取得は行わず、既存の参照画像のみを使用します。

使い方:
1. 必要なライブラリをインストール: pip install google-genai pillow
2. 環境変数GOOGLE_API_KEYを設定するか、実行時に入力
3. このスクリプトを実行: python scripts/gen_missing_avatars_from_existing_references.py

環境変数:
- GOOGLE_API_KEY: Google Gemini APIキー
"""

import os
import json
import time
import base64
import csv
from pathlib import Path
import sys
import re
from PIL import Image
import google.genai as genai
from google.genai import types

# カレントディレクトリをプロジェクトルートに設定
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Google Gemini APIキーの設定
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Google APIキーが設定されていません。")
    api_key = input("Google APIキーを入力してください: ").strip()
    if not api_key:
        print("APIキーが必要です。プログラムを終了します。")
        sys.exit(1)

# Geminiクライアントの初期化
client = genai.Client(api_key=api_key)

# ディレクトリの設定
OUT_DIR = Path("avatars")
OUT_DIR.mkdir(exist_ok=True)

# 画像が見つからなかった学者の情報を記録するCSVファイル
MISSING_PHOTOS_CSV = Path("missing_photos.csv")

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

def get_all_scholars():
    """scholars_enhanced.jsonから全ての学者データを取得"""
    try:
        with open("scholars_enhanced.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading all scholars data: {e}")
        return []

def add_to_missing_photos_csv(scholar_id, name_en, name_ja, source_url=None, status="manual_added"):
    """学者の情報をCSVに追記（処理状況も記録）
    
    status:
    - "missing": 画像が見つからず、手動での追加が必要
    - "manual_added": 手動で参照画像が追加済み
    - "generated": アバター生成成功
    """
    # CSVファイルが存在するか確認
    file_exists = MISSING_PHOTOS_CSV.exists()
    
    # ヘッダー情報の定義
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
        
        # 画像を開く（モードを強制的にRGBに変換）
        try:
            image = Image.open(reference_image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            print(f"画像オープンエラー: {e}")
            return None
        
        # Geminiモデルを使用して画像生成
        model = "gemini-2.0-flash-exp-image-generation"
        try:
            response = client.models.generate_content(
                model=model,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
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

def find_missing_avatars():
    """参照画像はあるが、アバター画像がない学者を見つける"""
    missing_avatars = []
    
    # avatarsディレクトリ内のファイルを取得
    files = list(OUT_DIR.glob('*'))
    
    # _referenceファイルを見つける
    reference_files = [f for f in files if '_reference' in f.name]
    
    for ref_file in reference_files:
        # ファイル名から学者IDを抽出
        match = re.match(r'(.+)_reference\..+', ref_file.name)
        if match:
            scholar_id = match.group(1)
            
            # 対応するアバター画像（.png）が存在するか確認
            avatar_path = OUT_DIR / f"{scholar_id}.png"
            if not avatar_path.exists():
                missing_avatars.append((scholar_id, ref_file))
                print(f"Missing avatar for {scholar_id}, reference file exists: {ref_file.name}")
    
    return missing_avatars

def generate_missing_avatars():
    """参照画像はあるが、アバター画像がない学者のアバターを生成"""
    # 欠けているアバターを探す
    missing_avatars = find_missing_avatars()
    print(f"\n参照画像はあるが、アバター画像がない学者: {len(missing_avatars)}人")
    
    if not missing_avatars:
        print("全ての参照画像に対応するアバター画像が存在します。処理は不要です。")
        return
    
    # 全学者データの取得
    all_scholars = get_all_scholars()
    scholars_dict = {scholar['id']: scholar for scholar in all_scholars}
    
    # 処理結果のカウント
    results = {
        "success": 0,
        "error": 0,
        "gif_error": 0,
    }
    
    # APIレート制限対策の待機時間（秒）
    api_wait_time = 2
    
    # 各学者のアバターを生成
    for idx, (scholar_id, ref_file) in enumerate(missing_avatars):
        print(f"\n処理中 [{idx+1}/{len(missing_avatars)}]: {scholar_id}")
        
        # 学者情報の取得
        scholar = scholars_dict.get(scholar_id)
        if not scholar:
            print(f"Warning: Scholar with ID {scholar_id} not found in scholars_enhanced.json")
            name_en = scholar_id  # フォールバックとして学者IDを使用
            name_ja = ""
        else:
            name_en = scholar['name']['en']
            name_ja = scholar['name'].get('ja', '')
        
        # GIF形式の参照画像の特別処理
        if ref_file.suffix.lower() == '.gif':
            print(f"Warning: GIF形式の参照画像は処理が難しい場合があります: {ref_file.name}")
            try:
                # PILでGIFを開いてRGBに変換を試みる
                with Image.open(ref_file) as img:
                    # 最初のフレームのみ使用
                    img.seek(0)
                    rgb_img = img.convert('RGB')
                    temp_path = OUT_DIR / f"{scholar_id}_temp.jpg"
                    rgb_img.save(temp_path)
                    ref_file = temp_path
                    print(f"GIF画像をJPEGに変換しました: {temp_path}")
            except Exception as e:
                print(f"GIF画像の変換に失敗しました: {e}")
                results["gif_error"] += 1
                continue
        
        try:
            # 参照画像からアバターを生成
            avatar_data = generate_avatar_from_reference_image(name_en, ref_file)
            
            if not avatar_data:
                print(f"アバター生成に失敗しました: {scholar_id}")
                results["error"] += 1
                continue
            
            # 生成されたアバターを保存
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
                results["error"] += 1
                continue
            
            # scholars_enhanced.jsonを更新
            if scholar:
                scholar["avatar"] = str(avatar_path)
            
            # 状態を更新
            add_to_missing_photos_csv(scholar_id, name_en, name_ja, None, "generated")
            
            print(f"✅ 生成成功: {avatar_path}")
            results["success"] += 1
            
            # APIレート制限対策
            if idx < len(missing_avatars) - 1:  # 最後の項目でなければ待機
                print(f"APIレート制限対策: {api_wait_time}秒待機します...")
                time.sleep(api_wait_time)
        
        except Exception as e:
            print(f"処理中にエラーが発生しました: {e}")
            results["error"] += 1
            continue
    
    # 一時ファイルのクリーンアップ
    for temp_file in OUT_DIR.glob('*_temp.jpg'):
        try:
            temp_file.unlink()
            print(f"一時ファイルを削除しました: {temp_file}")
        except Exception as e:
            print(f"一時ファイルの削除に失敗しました: {e}")
    
    # scholars_enhanced.jsonの更新を保存
    try:
        with open("scholars_enhanced.json", "w", encoding="utf-8") as f:
            json.dump(all_scholars, f, ensure_ascii=False, indent=2)
        print("\nscholars_enhanced.jsonを更新しました")
    except Exception as e:
        print(f"\nscholars_enhanced.jsonの更新に失敗しました: {e}")
    
    # 結果サマリーの表示
    print("\n===== 処理結果サマリー =====")
    print(f"対象学者数: {len(missing_avatars)}")
    print(f"成功: {results['success']}")
    print(f"エラー: {results['error']}")
    print(f"GIF変換エラー: {results['gif_error']}")

if __name__ == "__main__":
    # 開始時間を記録
    start_time = time.time()
    
    # 処理の実行
    generate_missing_avatars()
    
    # 終了時間と所要時間の表示
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"\n処理完了! 所要時間: {int(minutes)}分 {int(seconds)}秒")
