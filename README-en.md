# ComfyUI-manage_model_path

A Python script to manage ComfyUI model paths. It creates folders in an external model folder and synchronizes them with `extra_model_paths.yaml`.
Requires PyYAML and questionary.

```
pip install PyYAML
pip install questionary
```

## Usage

There are two main features:

#### 1: Create New Section

When you enter a folder name, it creates a folder inside the extra model folder. Simultaneously, it creates subfolders: `checkpoints`, `text_encoders`, `diffusion_models`, `loras`, and `vae`. It writes this configuration to `extra_model_paths.yaml` under a section named `_managed_foldername`.

If the folder already exists, it will ask whether to register it in the yaml file. If you allow it, it will write a new section.

#### 2: Sync Subfolder Configuration (Cleanup)

It reads `extra_model_paths.yaml` and updates it to match the current folder structure. If there are subfolders defined in the yaml that don't exist, it will add them as `foldername:"foldername/"`. Conversely, if subfolders are missing from the filesystem but exist in the yaml, they will be removed from the yaml. If the folder itself no longer exists, the `_managed_foldername` section will be deleted.

Only sections starting with `_managed_` are synchronized, so items added by other methods are protected. However, comments are removed during the process.

### Execution

You can use command-line arguments to specify paths and folder names.

```bash
# Display help
python manage_model_path.py --help

# Run with specified paths
python manage_model_path.py -c "G:/venv/Comfy/ComfyUI" -e "G:/venv/_extra_models"

# Run with specified language
python manage_model_path.py -l ja

# Run with all options
python manage_model_path.py -c "G:/venv/Comfy/ComfyUI" -e "G:/venv/_extra_models" -l ja "my_model_folder"
```

`manage_model_path_example.bat` is a sample that launches with specified paths.

#### Command Line Options

| Option | Short Form | Description |
|-----------|--------|------|
| `--comfy-path` | `-c` | ComfyUI root path |
| `--extra-model-path` | `-e` | Extra model root path |
| `--lang` | `-l` | Display language (en or ja) |
| `folder_name` | - | Folder name to create directly (optional) |

When launched without arguments, you will be prompted to enter the ComfyUI root path and the extra model root path.

## Screenshot

![screen](screen.jpg)
