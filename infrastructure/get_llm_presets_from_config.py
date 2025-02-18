from .config_path import CONFIG_PATH


import configparser
import json


def get_llm_presets_from_config():
    """
    Get all LLM presets from config file

    Returns:
        dict: Dictionary of preset names and their parameters
    """
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        presets = {}

        if config.has_section('llm_presets'):
            for preset_name in config.options('llm_presets'):
                preset_json = config.get('llm_presets', preset_name)
                try:
                    preset_params = json.loads(preset_json)
                    presets[preset_name] = preset_params
                except json.JSONDecodeError as e:
                    print(
                        f"Warning: Invalid JSON in preset '{preset_name}': {e}")
                    continue

        return presets
    except configparser.Error:
        return {}
    except Exception:
        return {}
