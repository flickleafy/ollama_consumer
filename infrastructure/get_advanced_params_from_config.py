from .config_path import CONFIG_PATH


import configparser


def get_advanced_params_from_config():
    """
    Get all advanced model parameters from config file

    Returns:
        dict: Dictionary containing all advanced parameters with their configured values
    """
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        params = {}

        if config.has_section('ollama'):
            # Numeric parameters
            numeric_params = [
                'temperature', 'top_k', 'top_p', 'repeat_penalty', 'seed',
                'num_predict', 'num_ctx', 'num_batch', 'num_gqa', 'num_gpu',
                'main_gpu', 'num_thread', 'max_image_size'
            ]

            for param in numeric_params:
                if config.has_option('ollama', param):
                    try:
                        value = config.get('ollama', param)
                        if value.strip() == '-1':
                            # -1 means auto/default, don't include in request
                            continue
                        elif param in ['temperature', 'top_p', 'repeat_penalty']:
                            params[param] = float(value)
                        else:
                            params[param] = int(value)
                    except (ValueError, TypeError):
                        continue

            # Boolean parameters
            boolean_params = [
                'low_vram', 'f16_kv', 'logits_all', 'vocab_only',
                'use_mmap', 'use_mlock', 'stream_response', 'raw_response'
            ]

            for param in boolean_params:
                if config.has_option('ollama', param):
                    try:
                        value = config.get('ollama', param).lower()
                        if value in ['true', 'false']:
                            params[param] = value == 'true'
                    except (ValueError, TypeError):
                        continue

            # String parameters
            string_params = [
                'thinking_format', 'reasoning_depth', 'image_quality', 'image_format'
            ]

            for param in string_params:
                if config.has_option('ollama', param):
                    value = config.get('ollama', param).strip()
                    if value and value != 'auto':
                        params[param] = value

            # Special handling for enable_thinking and enable_vision
            if config.has_option('ollama', 'enable_thinking'):
                thinking = config.get(
                    'ollama', 'enable_thinking').lower().strip()
                if thinking == 'true':
                    params['enable_thinking'] = True
                elif thinking == 'false':
                    params['enable_thinking'] = False
                # 'auto' means model-dependent, don't set explicitly

            if config.has_option('ollama', 'enable_vision'):
                vision = config.get('ollama', 'enable_vision').lower().strip()
                if vision == 'true':
                    params['enable_vision'] = True
                elif vision == 'false':
                    params['enable_vision'] = False
                # 'auto' means model-dependent, don't set explicitly

        return params
    except configparser.Error:
        # Silently return empty dict if config has parsing errors
        return {}
    except Exception:
        return {}
