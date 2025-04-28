@echo off
REM 学者アバター生成バッチ処理スクリプト（Windows用）

echo Gemini APIを使用した学者アバター生成バッチ処理を開始します
echo.

REM 必要なパッケージのインストール確認（PowerShellで実行）
powershell -Command "& {$packages = @('requests', 'beautifulsoup4', 'pillow', 'google-genai'); foreach ($pkg in $packages) { if (-not (pip show $pkg 2>$null)) { Write-Host \"$pkg パッケージが見つかりません。インストールします...\"; pip install $pkg } } }"
echo.

REM API鍵の確認
if "%GOOGLE_API_KEY%"=="" (
    echo 警告: 環境変数GOOGLE_API_KEYが設定されていません。
    echo スクリプト実行時に入力を求められます。
    echo 事前に設定する場合は以下のコマンドを実行してください：
    echo set GOOGLE_API_KEY=your-api-key-here
    echo.
)

echo アバター生成バッチ処理を開始します...
echo 注意: このスクリプトは全ての学者画像を生成しようと試みます。
echo 処理中はAPIレート制限に注意してください。
echo 処理状況はmissing_photos.csvに記録されます。
echo.

REM 確認
set /p confirm=処理を開始しますか？(y/n): 
if /i "%confirm%"=="y" (
    python "%~dp0\gen_avatars_batch_gemini.py"
) else (
    echo 処理をキャンセルしました。
)

echo.
pause
