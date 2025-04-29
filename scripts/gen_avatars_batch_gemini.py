#!/usr/bin/env python
"""
学者画像生成スクリプト（バッチ処理用）- Gemini API使用版

使い方:
1. 必要なライブラリをインストール: pip install google-genai pillow requests beautifulsoup4
2. 環境変数GOOGLE_API_KEYを設定するか、実行時に入力
3. このスクリプトを実行: python scripts/gen_avatars_batch_gemini.py

特徴:
- Gemini APIを使用してアバター画像を生成
- 参照画像が見つからない場合はmissing_photos.csvに記録
- すでに処理状態はCSVで管理（missing/manual_added/generated）

環境変数:
- GOOGLE_API_KEY: Google Gemini APIキー
"""

import json
import os
import time
from pathlib import Path

# カレントディレクトリをプロジェクトルートに設定
import sys
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# モジュールをインポート
from scripts.gen_avatar_from_photo import (
    get_scholar_by_id, debug_generate_from_photo, add_to_missing_photos_csv,
    MISSING_PHOTOS_CSV
)
import google.generativeai as genai

# Google Gemini APIキーの設定
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Google APIキーが設定されていません。")
    api_key = input("Google APIキーを入力してください: ").strip()
    if not api_key:
        print("APIキーが必要です。プログラムを終了します。")
        sys.exit(1)
    os.environ["GOOGLE_API_KEY"] = api_key

# Geminiクライアントの初期化
genai.configure(api_key=api_key)

# 出力ディレクトリの確認
OUT_DIR = Path("avatars")
OUT_DIR.mkdir(exist_ok=True)
REF_DIR = Path("reference_photos")
REF_DIR.mkdir(exist_ok=True)

def load_missing_photos_csv():
    """missing_photos.csvからステータス情報を読み込む"""
    status_dict = {}
    if MISSING_PHOTOS_CSV.exists():
        try:
            import csv
            with open(MISSING_PHOTOS_CSV, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)  # ヘッダー行をスキップ
                
                # ステータス列のインデックスを取得
                status_index = headers.index('status') if 'status' in headers else None
                
                if status_index is not None:
                    for row in reader:
                        if len(row) > status_index:
                            scholar_id = row[0]
                            status = row[status_index]
                            status_dict[scholar_id] = status
        except Exception as e:
            print(f"Warning: CSVファイルの読み込みエラー: {e}")
    
    return status_dict

def process_scholar_batch():
    """scholars_enhanced.jsonからすべての学者を処理する"""
    print("学者データの読み込み開始")
    
    try:
        # JSONファイルの読み込み
        with open("scholars_enhanced.json", "r", encoding="utf-8") as f:
            scholars = json.load(f)
        
        print(f"データ読み込み完了: {len(scholars)}人の学者")
        
        # 既存の処理状態を読み込み
        status_dict = load_missing_photos_csv()
        print(f"既存の処理状態を読み込み: {len(status_dict)}件")
        
        # 処理対象の学者をカウント
        to_process = [s for s in scholars if not s.get("avatar")]
        print(f"処理対象: {len(to_process)}人（アバターなし）")
        
        # 処理結果のカウント
        results = {
            "success": 0,
            "manual_added": 0,
            "missing": 0,
            "error": 0,
            "skipped": 0
        }
        
        # 各学者を処理
        for idx, scholar in enumerate(scholars):
            scholar_id = scholar["id"]
            name_en = scholar["name"]["en"]
            name_ja = scholar.get("ja", "")
            
            # 進捗表示
            print(f"\n処理中 [{idx+1}/{len(scholars)}]: {name_en} ({scholar_id})")
            
            # すでにアバターがある場合はスキップ
            if scholar.get("avatar"):
                avatar_path = Path(scholar["avatar"])
                if avatar_path.exists():
                    print(f"既存のアバターがあるためスキップ: {avatar_path}")
                    results["skipped"] += 1
                    continue
                else:
                    print(f"アバターパスは設定されていますが、ファイルが見つかりません: {avatar_path}")
            
            # すでに処理済み（generatedフラグあり）の場合はスキップするオプション
            if scholar_id in status_dict and status_dict[scholar_id] == "generated":
                avatar_path = OUT_DIR / f"{scholar_id}.png"
                if avatar_path.exists():
                    print(f"生成済みフラグがあり、ファイルも存在するのでスキップ: {avatar_path}")
                    scholar["avatar"] = str(avatar_path)
                    results["success"] += 1
                    continue
            
            # アバター生成を試みる
            try:
                avatar_path = debug_generate_from_photo(scholar_id)
                
                if avatar_path:
                    print(f"✅ 生成成功: {avatar_path}")
                    scholar["avatar"] = str(avatar_path)
                    results["success"] += 1
                    
                    # 状態に応じてカウント
                    if scholar_id in status_dict:
                        if status_dict[scholar_id] == "manual_added":
                            results["manual_added"] += 1
                    
                    # APIレート制限対策
                    time.sleep(2)
                else:
                    print(f"❌ 生成失敗: {scholar_id}")
                    # ステータスに基づいてカウント
                    if scholar_id in status_dict:
                        if status_dict[scholar_id] == "missing":
                            results["missing"] += 1
                        elif status_dict[scholar_id] == "manual_added":
                            results["manual_added"] += 1
                            print(f"⚠️ 手動参照画像があるのに生成に失敗しました: {scholar_id}")
                    else:
                        results["missing"] += 1
            
            except Exception as e:
                print(f"エラー発生: {e}")
                results["error"] += 1
                continue
        
        # JSONファイルの更新
        print("\nJSONファイルを更新します")
        with open("scholars_enhanced.json", "w", encoding="utf-8") as f:
            json.dump(scholars, f, ensure_ascii=False, indent=2)
        print("JSON更新完了")
        
        # 結果サマリーの表示
        print("\n===== 処理結果サマリー =====")
        print(f"総学者数: {len(scholars)}")
        print(f"成功: {results['success']} (うち手動参照画像: {results['manual_added']})")
        print(f"画像なし: {results['missing']}")
        print(f"エラー: {results['error']}")
        print(f"スキップ: {results['skipped']}")
        print(f"missing_photos.csv に記録: {MISSING_PHOTOS_CSV}")
        
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    # 開始時間を記録
    start_time = time.time()
    
    # バッチ処理の実行
    process_scholar_batch()
    
    # 終了時間と所要時間の表示
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"\n処理完了! 所要時間: {int(minutes)}分 {int(seconds)}秒")
