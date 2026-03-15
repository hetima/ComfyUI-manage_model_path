@echo off
setlocal
cd /d %~dp0

:: Pythonスクリプトのファイル名を指定してください
set SCRIPT_NAME="manage_model_path.py"
:: ComfyUIのルートパス
set COMFY_ROOT="G:\venv\Comfy\ComfyUI"
:: エクストラモデルのルートパス
set EXTRA_MODEL_PATH="G:\venv\_extra_models"

:: スクリプトの実行
python "%SCRIPT_NAME%" --comfy-path "%COMFY_ROOT%" --extra-model-path "%EXTRA_MODEL_PATH%" --lang ja

