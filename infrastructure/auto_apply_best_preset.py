from .apply_llm_preset import apply_llm_preset
from .get_best_preset_for_task import get_best_preset_for_task
from .color_text import color_text


def auto_apply_best_preset(content_type=None, model_name=None, prompt_text=None, silent=False):
    """
    Automatically apply the best preset for the detected task

    Args:
        content_type (str): Detected content type
        model_name (str): Selected model name  
        prompt_text (str): User prompt
        silent (bool): If True, don't show preset application messages

    Returns:
        str: Applied preset name
    """
    best_preset = get_best_preset_for_task(
        content_type, model_name, prompt_text)

    if best_preset != 'default':
        success = apply_llm_preset(best_preset)
        if success and not silent:
            preset_descriptions = {
                'vision_analysis': 'Vision Analysis',
                'coding': 'Code Analysis',
                'text_analysis': 'Text Analysis',
                'reasoning_mode': 'Deep Reasoning',
                'moe_optimized': 'MoE Optimized',
                'mathematical': 'Mathematical',
                'translation': 'Translation',
                'creative_writing': 'Creative Writing',
                'summarization': 'Summarization'
            }
            description = preset_descriptions.get(
                best_preset, best_preset.title())
            print(color_text(
                f"🎯 Auto-applied '{description}' preset for optimal performance", 'cyan'))

    return best_preset
