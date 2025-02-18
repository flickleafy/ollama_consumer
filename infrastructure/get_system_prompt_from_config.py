from .config_path import CONFIG_PATH


import configparser


def get_system_prompt_from_config(content_type=None):
    """
    Get system prompt from config file based on content type

    Args:
        content_type (str): Type of content - 'image', 'code', 'srt', or None for default

    Returns:
        str: Appropriate system prompt for the content type
    """
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        # If content type is specified and specialized prompt exists, use it
        if content_type and config.has_section('system_prompts'):
            if content_type == 'image' and config.has_option('system_prompts', 'image_analysis'):
                return config.get('system_prompts', 'image_analysis', fallback='').strip()
            elif content_type == 'code' and config.has_option('system_prompts', 'code_analysis'):
                return config.get('system_prompts', 'code_analysis', fallback='').strip()
            elif content_type == 'srt' and config.has_option('system_prompts', 'srt_analysis'):
                return config.get('system_prompts', 'srt_analysis', fallback='').strip()

        # Fall back to default system prompt
        return config.get('ollama', 'system_prompt', fallback='').strip()
    except configparser.Error as e:
        print(f"Warning: Error reading system prompt from config: {e}")
        return ''
    except Exception:
        return ''
