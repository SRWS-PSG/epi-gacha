import pandas as pd
import json
import os
from datetime import datetime

# レア度の変換マッピング
rarity_mapping = {
    1: "N",
    2: "R",
    3: "SR",
    4: "SSR"
}

# 現在のscholars.jsonを読み込む
scholars_file = 'scholars.json'
with open(scholars_file, 'r', encoding='utf-8') as f:
    scholars_data = json.load(f)

# 既存のIDを取得して重複しないようにする
existing_ids = [scholar['id'] for scholar in scholars_data]

# CSVファイルを読み込む
sheet1_file = 'リスト_Sheet1.csv'
sheet2_file = 'リスト_第二弾.csv'

# 両方のCSVファイルを処理
new_scholars = []

def process_csv(csv_file):
    scholars_list = []
    if not os.path.exists(csv_file):
        print(f"ファイル {csv_file} が見つかりません。")
        return []
    
    df = pd.read_csv(csv_file)
    
    # カラム名を修正（CSVファイルの最初の行が空白または不適切な場合）
    if df.columns[0] == '1' or df.columns[0] == '':
        # 第二弾.csvの場合（または適切なカラム名がない場合）
        df.columns = ['rarity', 'name', 'link', 'extra']
    else:
        # Sheet1.csvの場合
        df.columns = ['rarity', 'name', 'link', 'image_link']
    
    for _, row in df.iterrows():
        # 空行または必要な情報がない行はスキップ
        if pd.isna(row['name']) or str(row['name']).strip() == '':
            continue
        
        # 名前から簡単なIDを生成
        name_romaji = ""
        try:
            # ここでは簡易的にローマ字変換を行わず、名前の最初の部分を使用
            name_parts = str(row['name']).split()
            name_romaji = name_parts[0].lower() if name_parts else "unknown"
        except:
            name_romaji = "unknown"
        
        # 現在の年を取得
        current_year = datetime.now().year
        
        # IDを生成（名前のローマ字 + 年）
        scholar_id = f"{name_romaji}{current_year}"
        
        # IDが既に存在する場合は、連番を付ける
        original_id = scholar_id
        counter = 1
        while scholar_id in existing_ids:
            scholar_id = f"{original_id}_{counter}"
            counter += 1
        
        # レア度の変換
        rarity_value = row['rarity']
        try:
            rarity_value = int(rarity_value)
        except:
            rarity_value = 1  # デフォルトはN
        
        rarity = rarity_mapping.get(rarity_value, "N")
        
        # 新しい学者データを作成
        scholar = {
            "id": scholar_id,
            "name": {
                "en": "",  # 英語名はここでは空欄
                "ja": str(row['name'])
            },
            "affiliation": "",  # 所属情報はCSVにないため空欄
            "tags": [],  # タグ情報はCSVにないため空配列
            "rarity": rarity,
            "avatar": None,
            "highlights": [],
            "contribution": {
                "text": "",
                "source": row['link'] if not pd.isna(row['link']) else ""
            },
            "trivia": "",
            "triviaSource": "",
            "sources": [
                row['link'] if not pd.isna(row['link']) else ""
            ],
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        # 既存のIDリストに追加して重複を防ぐ
        existing_ids.append(scholar_id)
        
        scholars_list.append(scholar)
        
    return scholars_list

# 両方のCSVファイルを処理
new_scholars = process_csv(sheet1_file) + process_csv(sheet2_file)

# 新しい学者データを既存のデータに追加
scholars_data.extend(new_scholars)

# 更新したデータをJSONファイルに書き込む
with open('scholars_updated.json', 'w', encoding='utf-8') as f:
    json.dump(scholars_data, f, indent=2, ensure_ascii=False)

print(f"変換が完了しました。{len(new_scholars)}名の新しい学者データが追加されました。")
print("新しいファイル 'scholars_updated.json' が作成されました。")
print("新しく追加された学者のID一覧:")
for scholar in new_scholars:
    print(f"- {scholar['id']}: {scholar['name']['ja']} ({scholar['rarity']})")
