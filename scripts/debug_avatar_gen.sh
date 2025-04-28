#!/bin/bash
# 学者アバター生成デバッグスクリプト実行用シェルスクリプト

# スクリプトのパスを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJ_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJ_DIR"

# 必要なパッケージのインストール確認
pip_packages=("requests" "beautifulsoup4" "openai" "pillow")
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

# スクリプト実行
echo "アバター生成スクリプトを実行します..."
python "$SCRIPT_DIR/gen_avatar_from_photo.py"
