from .config_path import CONFIG_PATH


import configparser
import json
import os


def get_blacklisted_models():
    """
    Get list of blacklisted models from config.ini

    Returns:
        list: List of blacklisted model names, or empty list if none/error
    """
    try:
        config = configparser.ConfigParser()

        # Check if config file exists
        config_path = CONFIG_PATH
        if not os.path.exists(config_path):
            return []

        config.read(config_path)

        # Get blacklisted models from the [blacklist] section
        if config.has_section('blacklist') and config.has_option('blacklist', 'models'):
            blacklist_str = config.get('blacklist', 'models')

            # Parse the list - handle different formats:
            # - JSON array: ["model1", "model2"]
            # - Comma-separated: model1, model2, model3
            # - Newline-separated: model1\nmodel2\nmodel3

            blacklist_str = blacklist_str.strip()
            if not blacklist_str:
                return []

            # Try parsing as JSON array first
            try:
                blacklisted_models = json.loads(blacklist_str)
                if isinstance(blacklisted_models, list):
                    return [str(model).strip() for model in blacklisted_models if model]
            except (ValueError, json.JSONDecodeError):
                pass

            # Fall back to comma or newline separated
            if ',' in blacklist_str:
                # Comma-separated
                blacklisted_models = [model.strip().strip('"\'')
                                      for model in blacklist_str.split(',')]
            else:
                # Newline-separated or single model
                blacklisted_models = [model.strip().strip('"\'')
                                      for model in blacklist_str.split('\n')]

            # Filter out empty strings
            return [model for model in blacklisted_models if model]

        return []

    except configparser.Error as e:
        # Only show this specific error if it's not related to the system_prompts section
        if 'system_prompts' not in str(e):
            print(
                f"Warning: Error reading blacklisted models from config: {e}")
        return []
    except Exception as e:
        # Print error but don't fail the application
        print(f"Warning: Error reading blacklisted models from config: {e}")
        return []
