#!/usr/bin/env python
"""
学者画像生成スクリプト（手動実行用）

使い方:
1. scholars.jsonに新しい学者データを追加（avatarフィールドはnullまたは省略）
2. このスクリプトを実行: python scripts/gen_avatar_batch.py
3. avatarフィールドがnullの学者の画像が生成され、scholars.jsonが更新されます

環境変数:
- OPENAI_API_KEY: OpenAI APIキー

注意:
- 画像生成にはOpenAI APIの使用料金が発生します
- 既存の画像は上書きされません
"""

import json, os, time, base64
from pathlib import Path
import requests
from openai import OpenAI

# OpenAI APIクライアントの初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OUT_DIR = Path("avatars")
OUT_DIR.mkdir(exist_ok=True)

# 学者の画像を生成するためのプロンプトテンプレート
# 必要に応じてカスタマイズしてください
PROMPT_TEMPLATE = (
    "Flat pastel portrait of {name_en}, "
    "facing forward, 4-colour palette, thick outline, solid background. "
    "No text, no watermark."
)

def generate_and_save(record):
    """学者の画像を生成し、avatarsディレクトリに保存する"""
    # すでに画像が存在する場合はそのパスを返す
    img_path = OUT_DIR / f"{record['id']}.png"
    if img_path.exists():
        print(f"画像が存在するのでスキップ: {img_path}")
        return str(img_path)
        
    # 生成用プロンプトの作成
    prompt = PROMPT_TEMPLATE.format(name_en=record["name"]["en"])
    print(f"画像生成: {record['name']['en']}")
    
    try:
        # OpenAI APIを呼び出して画像を生成
        response = client.images.generate(
            model="dall-e-3",  # GPT-image-1または他の適切なモデル
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1
        )
        
        # URLから画像をダウンロード
        image_url = response.data[0].url
        print(f"画像URL: {image_url}")
        
        with requests.get(image_url, stream=True) as r:
            r.raise_for_status()
            with open(img_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"画像保存完了: {img_path}")
        time.sleep(1)  # APIレート制限対策
        
        return str(img_path)
    
    except Exception as e:
        print(f"画像生成エラー: {e}")
        return None

# メイン処理
def main():
    print("学者データの読み込み開始")
    try:
        with open("scholars.json", "r", encoding="utf-8") as f:
            scholars = json.load(f)
        
        print(f"データ読み込み完了: {len(scholars)}人の学者")
        
        changed = False
        for idx, record in enumerate(scholars):
            print(f"\n処理中: {idx+1}/{len(scholars)} - {record['name']['ja']}")
            
            if not record.get("avatar"):
                avatar_path = generate_and_save(record)
                if avatar_path:
                    record["avatar"] = avatar_path
                    changed = True
            else:
                print(f"既に画像があるためスキップ: {record['avatar']}")
        
        if changed:
            print("\nJSONファイルを更新します")
            with open("scholars.json", "w", encoding="utf-8") as f:
                json.dump(scholars, f, ensure_ascii=False, indent=2)
            print("JSON更新完了")
        else:
            print("\n変更はありませんでした")
    
    except Exception as e:
        print(f"エラー発生: {e}")
        raise

if __name__ == "__main__":
    main()
