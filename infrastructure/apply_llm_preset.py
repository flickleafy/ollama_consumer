from .get_llm_presets_from_config import get_llm_presets_from_config
from .config_path import CONFIG_PATH


import configparser


def apply_llm_preset(preset_name):
    """
    Apply an LLM preset by temporarily modifying the config

    Args:
        preset_name (str): Name of the preset to apply

    Returns:
        bool: True if preset was applied successfully, False otherwise
    """
    try:
        presets = get_llm_presets_from_config()

        if preset_name not in presets:
            print(f"❌ Preset '{preset_name}' not found")
            return False

        preset_params = presets[preset_name]

        # Read current config
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        # Ensure [ollama] section exists
        if not config.has_section('ollama'):
            config.add_section('ollama')

        # Apply preset parameters to [ollama] section
        for param, value in preset_params.items():
            config.set('ollama', param, str(value))

        # Write back to config
        with open(CONFIG_PATH, 'w') as f:
            config.write(f)

        print(f"✅ Applied preset '{preset_name}' successfully")
        return True

    except Exception as e:
        print(f"❌ Error applying preset '{preset_name}': {e}")
        return False
