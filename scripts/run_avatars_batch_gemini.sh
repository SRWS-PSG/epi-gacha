#!/bin/bash
# Gemini APIを使用した学者アバター生成バッチ処理スクリプト

# スクリプトのパスを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJ_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJ_DIR"

# 必要なパッケージのインストール確認
pip_packages=("requests" "beautifulsoup4" "pillow" "google-genai")
missing_packages=()

for package in "${pip_packages[@]}"; do
    if ! pip show "$package" &> /dev/null; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo "必要なパッケージが不足しています。インストールします:"
    for package in "${missing_packages[@]}"; do
        echo "- $package"
    done
    
    pip install "${missing_packages[@]}"
fi

# API鍵の確認
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "警告: 環境変数GOOGLE_API_KEYが設定されていません。"
    echo "スクリプト実行時に入力を求められます。"
    echo "事前に設定する場合は以下のコマンドを実行してください："
    echo "export GOOGLE_API_KEY='your-api-key-here'"
    echo ""
fi

# スクリプト実行
echo "アバター生成バッチ処理を開始します..."
echo "注意: このスクリプトは全ての学者画像を生成しようと試みます。"
echo "処理中はAPIレート制限に注意してください。"
echo "処理状況はmissing_photos.csvに記録されます。"
echo ""

# 確認
read -p "処理を開始しますか？(y/n): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    python "$SCRIPT_DIR/gen_avatars_batch_gemini.py"
else
    echo "処理をキャンセルしました。"
fi
