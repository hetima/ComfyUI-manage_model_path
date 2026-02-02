import os
import sys
import yaml
import shutil
import questionary
from pathlib import Path

# --- config ---
# dispaly language. supports "en" or "ja"
LANG = "ja"
# path of extra_model_paths.yaml
YAML_PATH = Path("G:/path/to/ComfyUI/extra_model_paths.yaml")
# path of your extra models root
BASE_EXTRA_DIR = Path("G:/path/to/extra_models")

# prefix key of yaml
TAG = "_managed_"
# バックアップ（.gitignoreで*.logが定義されているので拡張子を.logにしている）
BACKUP_PATH = YAML_PATH.with_name("extra_model_paths.yaml.back.log")

# Default Subfolder Structure When Creating New Items
DEFAULT_SUB_PATHS = ["checkpoints", "text_encoders", "diffusion_models", "loras", "vae"]

# --- localization dictionary ---
LOCALIZATION_DICTIONARY = {
    "ja": {
        "menu_title": "ComfyUI Path Manager",
        "menu_create": "1: セクション作成 / 既存フォルダ登録",
        "menu_cleanup": "2: サブフォルダ構成の同期 (Cleanup)",
        "menu_quit": "終了",
        "input_folder_name": "フォルダ名を入力してください:",
        "msg_folder_exists": "通知: フォルダ '{path}' は既に存在します。",
        "msg_import_confirm": "このフォルダをモデルフォルダとして登録しますか？",
        "msg_scan_existing": "既存のフォルダ構造をスキャンしました。",
        "msg_created_new": "新規フォルダとサブフォルダを作成しました。",
        "msg_register_done": "登録完了: {section}",
        "msg_yaml_empty": "YAMLが空です。",
        "msg_removed_section": " [!] base_path消失につきセクション削除: {section}",
        "msg_removed_sub": " [-] サブフォルダ消失につき削除: {section} -> {key}",
        "msg_added_sub": " [+] 新規フォルダを登録: {section} -> {key}",
        "msg_no_change": "同期の必要はありません。",
        "msg_found_diff": "\n実体なし管理セクションを {count} 件検出:",
        "confirm_save": "YAMLに変更を保存しますか？",
        "msg_sync_complete": "YAMLを同期しました。",
        "err_yaml_load": "YAML読み込みエラー: {error}",
        "err_mkdir": "フォルダ作成失敗: {error}",
        "err_save": "YAML保存エラー: {error}"
    },
    "en": {
        "menu_title": "ComfyUI Path Manager",
        "menu_create": "1: Create Section / Register Existing Folder",
        "menu_cleanup": "2: Sync Subfolder Structures (Cleanup)",
        "menu_quit": "Quit",
        "input_folder_name": "Enter folder name:",
        "msg_folder_exists": "Notice: Folder '{path}' already exists.",
        "msg_import_confirm": "Register this folder as a model folder?",
        "msg_scan_existing": "Scanned existing structure.",
        "msg_created_new": "Created new folder and subfolders.",
        "msg_register_done": "Registered: {section}",
        "msg_yaml_empty": "YAML is empty.",
        "msg_removed_section": " [!] Removing section due to missing base_path: {section}",
        "msg_removed_sub": " [-] Removing subfolder: {section} -> {key}",
        "msg_added_sub": " [+] Registering new folder: {section} -> {key}",
        "msg_no_change": "No synchronization needed.",
        "msg_found_diff": "\nDetected {count} missing management sections:",
        "confirm_save": "Save changes to YAML?",
        "msg_sync_complete": "YAML synchronized.",
        "err_yaml_load": "YAML load error: {error}",
        "err_mkdir": "Failed to create directory: {error}",
        "err_save": "YAML save error: {error}"
    }
}

def L(key: str) -> str:
    """翻訳文字列を取得する関数"""
    return LOCALIZATION_DICTIONARY.get(LANG, LOCALIZATION_DICTIONARY["en"]).get(key, key) or key

# --- YAML設定 ---
def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def get_yaml_data():
    if not YAML_PATH.exists(): return {}
    try:
        with open(YAML_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        questionary.print(L("err_yaml_load").format(error=e), style="fg:red")
        return {}

def save_yaml_with_backup(data):
    try:
        if YAML_PATH.exists():
            shutil.copy2(YAML_PATH, BACKUP_PATH)
        YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except Exception as e:
        questionary.print(L("err_save").format(error=e), style="fg:red")

def get_filtered_subfolders(path: Path):
    if not path.exists(): return set()
    return {
        f.name for f in path.iterdir() 
        if f.is_dir() and not f.name.startswith('.') and f.name != "base_path"
    }

def mode_create(raw_name=None):
    if not raw_name:
        raw_name = questionary.text(L("input_folder_name")).ask()
    if not raw_name: return

    section_name = f"{TAG}{raw_name}"
    target_path = BASE_EXTRA_DIR / raw_name
    inner_config = {"base_path": str(target_path).replace("\\", "/")}

    if target_path.exists():
        questionary.print(L("msg_folder_exists").format(path=target_path), style="fg:yellow")
        if not questionary.confirm(L("msg_import_confirm"), default=True).ask():
            return
        actual_subfolders = get_filtered_subfolders(target_path)
        for sub in actual_subfolders:
            inner_config[sub] = f"{sub}/"
        questionary.print(L("msg_scan_existing"), style="fg:green")
    else:
        try:
            os.makedirs(target_path)
            for sub in DEFAULT_SUB_PATHS:
                os.makedirs(target_path / sub, exist_ok=True)
                inner_config[sub] = f"{sub}/"
            questionary.print(L("msg_created_new"), style="fg:green")
        except Exception as e:
            questionary.print(L("err_mkdir").format(error=e), style="fg:red")
            return

    current_config = get_yaml_data()
    current_config.update({section_name: inner_config})
    save_yaml_with_backup(current_config)
    questionary.print(L("msg_register_done").format(section=section_name), style="bold fg:green")

def mode_cleanup():
    config_data = get_yaml_data()
    if not config_data:
        questionary.print(L("msg_yaml_empty"))
        return

    updated = False
    sections = list(config_data.keys())

    for section in sections:
        if not section.startswith(TAG): continue
        details = config_data[section]
        base_path_str = details.get('base_path')
        if not base_path_str: continue
        
        base_path = Path(base_path_str)
        if not base_path.exists():
            questionary.print(L("msg_removed_section").format(section=section), style="fg:red")
            config_data.pop(section)
            updated = True
            continue

        actual_subfolders = get_filtered_subfolders(base_path)

        # YAMLにあるが実体がないキーを削除
        for key in list(details.keys()):
            if key == "base_path": continue
            folder_name_in_yaml = details[key].strip('/')
            if folder_name_in_yaml not in actual_subfolders:
                questionary.print(L("msg_removed_sub").format(section=section, key=key), style="fg:yellow")
                details.pop(key)
                updated = True

        # 実体があるがYAMLにないフォルダを追加
        yaml_folder_names = {v.strip('/') for k, v in details.items() if k != "base_path"}
        for folder in actual_subfolders:
            if folder not in yaml_folder_names:
                details[folder] = f"{folder}/"
                questionary.print(L("msg_added_sub").format(section=section, key=folder), style="fg:green")
                updated = True

    if updated:
        if questionary.confirm(L("confirm_save"), default=True).ask():
            save_yaml_with_backup(config_data)
            questionary.print(L("msg_sync_complete"), style="bold fg:green")
    else:
        questionary.print(L("msg_no_change"), style="fg:green")

def main():
    yaml.add_representer(str, str_presenter)
    if len(sys.argv) > 1:
        mode_create(sys.argv[1])
        return
    while True:
        choice = questionary.select(
            L("menu_title"),
            choices=[
                {"name": L("menu_create"), "value": "create"},
                {"name": L("menu_cleanup"), "value": "cleanup"},
                {"name": L("menu_quit"), "value": "quit"}
            ]
        ).ask()
        if choice == "create": mode_create()
        elif choice == "cleanup": mode_cleanup()
        elif choice == "quit" or choice is None: break

if __name__ == "__main__":
    main()
