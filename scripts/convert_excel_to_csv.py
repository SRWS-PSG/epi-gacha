import pandas as pd

# Excelファイルを読み込む
excel_file = 'リスト.xlsx'

# Excelファイル内のすべてのシート名を取得
xls = pd.ExcelFile(excel_file)
sheet_names = xls.sheet_names
print(f"Excelファイル '{excel_file}' には以下のシートが含まれています: {sheet_names}")

# それぞれのシートを読み込み、CSVファイルとして保存
for sheet_name in sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    csv_file = f'リスト_{sheet_name}.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')  # UTF-8 with BOMで日本語文字化けを防止
    
    print(f"シート '{sheet_name}' をCSVに変換して {csv_file} として保存しました。")
    print(f"シート '{sheet_name}' の内容のプレビュー:")
    print(df.head())
    print("\n")
