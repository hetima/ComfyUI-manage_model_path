import os
import sys
import yaml
import shutil
import questionary
from pathlib import Path

# --- 設定 ---
# extra_model_paths.yamlの場所
YAML_PATH = Path("G:/path/to/ComfyUI/extra_model_paths.yaml")
# モデルの置き場所
BASE_EXTRA_DIR = Path("G:/path/to/extra_models")

# yamlキーのプレフィックス
TAG = "_managed_"
# バックアップ（.gitignoreで*.logが定義されているので拡張子を.logにしている）
# BACKUP_PATH = "" とすればバックアップを作成しない
BACKUP_PATH = YAML_PATH.with_name("extra_model_paths.yaml.back.log")

# 新規作成時のデフォルト構成
DEFAULT_SUB_PATHS = ["checkpoints", "text_encoders", "diffusion_models", "loras", "vae"]

def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def get_yaml_data():
    if not YAML_PATH.exists():
        return {}
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

def save_yaml_with_backup(data):
    if YAML_PATH.exists() and BACKUP_PATH:
        shutil.copy2(YAML_PATH, BACKUP_PATH)
    YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

def mode_create(raw_name=None):
    if not raw_name:
        raw_name = questionary.text("作成するフォルダ名を入力してください:").ask()
    if not raw_name: return

    section_name = f"{TAG}{raw_name}"
    target_path = BASE_EXTRA_DIR / raw_name

    if target_path.exists():
        questionary.print(f"エラー: フォルダ '{target_path}' は既に存在します。", style="bold fg:red")
        return

    # 新規作成時はデフォルトリストを使用
    inner_config = {"base_path": str(target_path).replace("\\", "/")}
    for sub in DEFAULT_SUB_PATHS:
        inner_config[sub] = f"{sub}/"

    os.makedirs(target_path)
    for sub in DEFAULT_SUB_PATHS:
        os.makedirs(target_path / sub, exist_ok=True)

    current_config = get_yaml_data()
    current_config.update({section_name: inner_config})
    save_yaml_with_backup(current_config)
    
    questionary.print(f"作成完了: {section_name}", style="bold fg:green")
    # os.startfile(target_path)

def mode_cleanup():
    config_data = get_yaml_data()
    if not config_data:
        questionary.print("YAMLが空です。")
        return

    updated = False
    # セクション名をリスト化してループ（ループ内の削除対策）
    sections = list(config_data.keys())

    for section in sections:
        if not section.startswith(TAG):
            continue

        details = config_data[section]
        base_path_str = details.get('base_path')
        if not base_path_str: continue
        
        base_path = Path(base_path_str)

        # 1. base_path自体が消えている場合はセクションごと削除
        if not base_path.exists():
            questionary.print(f" [!] base_path消失のため削除: {section}", style="fg:red")
            config_data.pop(section)
            updated = True
            continue

        # 2. 実体サブフォルダをスキャン
        actual_subfolders = {f.name for f in base_path.iterdir() if f.is_dir()}
        if "base_path" in actual_subfolders:
            actual_subfolders.remove("base_path") # 無視

        # 3. YAMLにあるが実体がないキーを削除（base_pathは除く）
        yaml_keys = list(details.keys())
        for key in yaml_keys:
            if key == "base_path": continue
            # YAMLの値（末尾スラッシュ除去）と実体フォルダ名を比較
            folder_name_in_yaml = details[key].strip('/')
            if folder_name_in_yaml not in actual_subfolders:
                questionary.print(f" [-] サブフォルダ消失につき削除: {section} -> {key}", style="fg:yellow")
                details.pop(key)
                updated = True

        # 4. 実体があるがYAMLにないフォルダを追加
        yaml_folder_names = {v.strip('/') for k, v in details.items() if k != "base_path"}
        for folder in actual_subfolders:
            if folder not in yaml_folder_names:
                new_key = folder.lower()
                details[new_key] = f"{folder}/"
                questionary.print(f" [+] 新規サブフォルダを登録: {section} -> {new_key}", style="fg:green")
                updated = True

    if updated:
        if questionary.confirm("YAMLに変更があります。保存しますか？", default=True).ask():
            save_yaml_with_backup(config_data)
            questionary.print("YAMLを同期しました。", style="bold fg:green")
    else:
        questionary.print("変更は必要ありませんでした。", style="fg:green")

def main():
    yaml.add_representer(str, str_presenter)
    if len(sys.argv) > 1:
        mode_create(sys.argv[1])
        return

    while True:
        choice = questionary.select(
            "ComfyUI Path Manager",
            choices=[
                {"name": "1: 新規セクション作成", "value": "create"},
                {"name": "2: サブフォルダ構成の同期 (Cleanup)", "value": "cleanup"},
                {"name": "終了", "value": "quit"}
            ]
        ).ask()
        if choice == "create": mode_create()
        elif choice == "cleanup": mode_cleanup()
        elif choice == "quit" or choice is None: break

if __name__ == "__main__":
    main()
