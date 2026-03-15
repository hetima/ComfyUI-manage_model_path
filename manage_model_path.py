import os
import sys
import yaml
import shutil
import questionary
import argparse
from pathlib import Path
from typing import Optional


class ComfyUIPathManager:
    """ComfyUIのモデルパスを管理するクラス"""

    # prefix key of yaml
    TAG = "_managed_"

    # バックアップ（.gitignoreで*.logが定義されているので拡張子を.logにしている）
    # BACKUP_PATH = "" にするとバックアップを作成しない
    BACKUP_PATH = ""

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
            "err_save": "YAML保存エラー: {error}",
            "input_comfy_path": "ComfyUIのルートパスを入力してください:",
            "input_extra_model_path": "追加モデルのルートパスを入力してください:",
            "err_path_not_exists": "エラー: パス '{path}' は存在しません。もう一度入力してください。",
            "select_lang": "表示言語を選択してください:",
            "lang_ja": "日本語",
            "lang_en": "English"
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
            "err_save": "YAML save error: {error}",
            "input_comfy_path": "Enter ComfyUI root path:",
            "input_extra_model_path": "Enter extra models root path:",
            "err_path_not_exists": "Error: Path '{path}' does not exist. Please try again.",
            "select_lang": "Select display language:",
            "lang_ja": "日本語",
            "lang_en": "English"
        }
    }

    def __init__(self, comfy_path: Optional[str] = None, extra_model_path: Optional[str] = None, lang: str = "en"):
        """
        初期化メソッド

        Args:
            comfy_path: ComfyUIのルートパス（省略時は対話入力）
            extra_model_path: 追加モデルのルートパス（省略時は対話入力）
            lang: 表示言語（"en"または"ja"、デフォルトは"en"）
        """
        self.lang = lang
        self.comfy_path = self._validate_path(comfy_path, "input_comfy_path")
        self.extra_model_path = self._validate_path(extra_model_path, "input_extra_model_path")
        self.yaml_path = Path(self.comfy_path, "extra_model_paths.yaml")

    def _validate_path(self, path: Optional[str], prompt_key: str) -> str:
        """
        パスを検証し、存在しない場合は対話入力を求める

        Args:
            path: 検証するパス
            prompt_key: プロンプトメッセージのキー

        Returns:
            検証されたパス
        """
        if path and Path(path).exists():
            return path

        while True:
            input_path = questionary.text(self.L(prompt_key)).ask()
            if input_path == None:
                exit(0)
            if not input_path:
                continue
            if Path(input_path).exists():
                return input_path
            questionary.print(self.L("err_path_not_exists").format(path=input_path), style="fg:red")

    def L(self, key: str) -> str:
        """翻訳文字列を取得する関数"""
        return self.LOCALIZATION_DICTIONARY.get(self.lang, self.LOCALIZATION_DICTIONARY["en"]).get(key, key) or key

    @staticmethod
    def str_presenter(dumper, data):
        """YAMLの文字列表現をカスタマイズ"""
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    def get_yaml_data(self):
        """YAMLファイルからデータを読み込む"""
        if not self.yaml_path.exists():
            return {}
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            questionary.print(self.L("err_yaml_load").format(error=e), style="fg:red")
            return {}

    def save_yaml_with_backup(self, data):
        """YAMLファイルを保存する（バックアップ付き）"""
        try:
            if self.yaml_path.exists() and self.BACKUP_PATH:
                shutil.copy2(self.yaml_path, self.BACKUP_PATH)
            self.yaml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except Exception as e:
            questionary.print(self.L("err_save").format(error=e), style="fg:red")

    def get_filtered_subfolders(self, path: Path):
        """フィルタリングされたサブフォルダを取得する"""
        if not path.exists():
            return set()
        return {
            f.name for f in path.iterdir()
            if f.is_dir() and not f.name.startswith('.') and f.name != "base_path"
        }

    def mode_create(self, raw_name=None):
        """セクション作成モード"""
        if not raw_name:
            raw_name = questionary.text(self.L("input_folder_name")).ask()
        if not raw_name:
            return

        section_name = f"{self.TAG}{raw_name}"
        target_path = Path(self.extra_model_path) / raw_name
        inner_config = {"base_path": str(target_path).replace("\\", "/")}

        if target_path.exists():
            questionary.print(self.L("msg_folder_exists").format(path=target_path), style="fg:yellow")
            if not questionary.confirm(self.L("msg_import_confirm"), default=True).ask():
                return
            actual_subfolders = self.get_filtered_subfolders(target_path)
            for sub in actual_subfolders:
                inner_config[sub] = f"{sub}/"
            questionary.print(self.L("msg_scan_existing"), style="fg:green")
        else:
            try:
                os.makedirs(target_path)
                for sub in self.DEFAULT_SUB_PATHS:
                    os.makedirs(target_path / sub, exist_ok=True)
                    inner_config[sub] = f"{sub}/"
                questionary.print(self.L("msg_created_new"), style="fg:green")
            except Exception as e:
                questionary.print(self.L("err_mkdir").format(error=e), style="fg:red")
                return

        current_config = self.get_yaml_data()
        current_config.update({section_name: inner_config})
        self.save_yaml_with_backup(current_config)
        questionary.print(self.L("msg_register_done").format(section=section_name), style="bold fg:green")

    def mode_cleanup(self):
        """サブフォルダ構成の同期モード"""
        config_data = self.get_yaml_data()
        if not config_data:
            questionary.print(self.L("msg_yaml_empty"))
            return

        updated = False
        sections = list(config_data.keys())

        for section in sections:
            if not section.startswith(self.TAG):
                continue
            details = config_data[section]
            base_path_str = details.get('base_path')
            if not base_path_str:
                continue

            base_path = Path(base_path_str)
            if not base_path.exists():
                questionary.print(self.L("msg_removed_section").format(section=section), style="fg:orange")
                config_data.pop(section)
                updated = True
                continue

            actual_subfolders = self.get_filtered_subfolders(base_path)

            # YAMLにあるが実体がないキーを削除
            for key in list(details.keys()):
                if key == "base_path":
                    continue
                folder_name_in_yaml = details[key].strip('/')
                if folder_name_in_yaml not in actual_subfolders:
                    questionary.print(self.L("msg_removed_sub").format(section=section, key=key), style="fg:yellow")
                    details.pop(key)
                    updated = True

            # 実体があるがYAMLにないフォルダを追加
            yaml_folder_names = {v.strip('/') for k, v in details.items() if k != "base_path"}
            for folder in actual_subfolders:
                if folder not in yaml_folder_names:
                    details[folder] = f"{folder}/"
                    questionary.print(self.L("msg_added_sub").format(section=section, key=folder), style="fg:green")
                    updated = True

        if updated:
            if questionary.confirm(self.L("confirm_save"), default=True).ask():
                self.save_yaml_with_backup(config_data)
                questionary.print(self.L("msg_sync_complete"), style="bold fg:green")
        else:
            questionary.print(self.L("msg_no_change"), style="fg:green")

    def run(self):
        """メインループを実行する"""
        yaml.add_representer(str, self.str_presenter)

        while True:
            choice = questionary.select(
                self.L("menu_title"),
                choices=[
                    {"name": self.L("menu_create"), "value": "create"},
                    {"name": self.L("menu_cleanup"), "value": "cleanup"},
                    {"name": self.L("menu_quit"), "value": "quit"}
                ]
            ).ask()
            if choice == "create":
                self.mode_create()
            elif choice == "cleanup":
                self.mode_cleanup()
            elif choice == "quit" or choice is None:
                break


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="ComfyUI Path Manager")
    parser.add_argument("-c", "--comfy-path", help="ComfyUI root path")
    parser.add_argument("-e", "--extra-model-path", help="Extra models root path")
    parser.add_argument("-l", "--lang", choices=["en", "ja"], default="en", help="Display language (en or ja)")
    parser.add_argument("folder_name", nargs="?", help="Folder name for direct creation (optional)")

    args = parser.parse_args()

    # マネージャーの初期化と実行
    manager = ComfyUIPathManager(comfy_path=args.comfy_path, extra_model_path=args.extra_model_path, lang=args.lang)
    
    # フォルダ名が指定されている場合は直接作成モードを実行
    if args.folder_name:
        manager.mode_create(args.folder_name)
    else:
        manager.run()


if __name__ == "__main__":
    main()
