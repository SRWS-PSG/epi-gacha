import json

def load_scholars_data(file_path):
    """Scholarデータをロードする"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # JSONファイルを読み込む
    input_file = 'scholars_enhanced.json'
    scholars = load_scholars_data(input_file)
    
    # 空データを持つ学者を特定
    incomplete_scholars = [
        scholar for scholar in scholars 
        if not scholar.get("contribution", {}).get("text") or not scholar.get("trivia")
    ]
    
    print(f"空データを持つ学者数: {len(incomplete_scholars)}")
    
    # 対象学者の詳細を表示
    print("\n空データを持つ学者リスト:")
    for i, scholar in enumerate(incomplete_scholars):
        scholar_name = scholar['name']['ja'] if scholar.get('name', {}).get('ja') else scholar['id']
        has_contribution = bool(scholar.get("contribution", {}).get("text"))
        has_trivia = bool(scholar.get("trivia"))
        
        status = []
        if not has_contribution:
            status.append("貢献情報なし")
        if not has_trivia:
            status.append("豆知識なし")
        
        print(f"{i+1}. {scholar_name} - {', '.join(status)}")

if __name__ == "__main__":
    main()
