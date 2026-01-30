@echo off
setlocal
cd /d %~dp0

:: Pythonスクリプトのファイル名を指定してください
set SCRIPT_NAME=manage_model_path.py

:: スクリプトの実行（引数はバッチファイルへのドラッグ＆ドロップでも渡せます）
python "%SCRIPT_NAME%" %*
