from .get_llm_presets_from_config import get_llm_presets_from_config


def list_available_presets():
    """
    List all available LLM presets with descriptions

    Returns:
        dict: Dictionary of preset names and their descriptions
    """
    presets = get_llm_presets_from_config()

    # Preset descriptions
    descriptions = {
        'creative_writing': 'Optimized for creative and diverse outputs with higher creativity',
        'coding': 'High accuracy and precision for code generation and analysis',
        'text_analysis': 'Optimized for transcript/document analysis with minimal hallucination',
        'vision_analysis': 'Maximum accuracy for visual content analysis and interpretation',
        'reasoning_mode': 'Deep reasoning and problem-solving capabilities',
        'moe_optimized': 'Specialized settings for Mixture of Experts model architectures',
        'conversational': 'Balanced parameters for natural dialogue and chat interactions',
        'mathematical': 'Precise settings for mathematical reasoning and calculations',
        'translation': 'Optimized for accurate language translation tasks',
        'summarization': 'Efficient content summarization and key information extraction',
        'performance': 'Speed and efficiency optimized for limited resource environments',
        'debugging': 'Specialized for code debugging and error analysis tasks'
    }

    available_presets = {}
    for preset_name in presets.keys():
        available_presets[preset_name] = descriptions.get(
            preset_name, 'Custom preset')

    return available_presets
