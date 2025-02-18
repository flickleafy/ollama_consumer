from .is_thinking_model import is_thinking_model
from .is_vision_model import is_vision_model


def get_best_preset_for_task(content_type=None, model_name=None, prompt_text=None):
    """
    Automatically determine the best LLM preset based on task type and model capabilities

    Args:
        content_type (str): Detected content type ('image', 'code', 'srt', etc.)
        model_name (str): Name of the selected model
        prompt_text (str): The actual prompt text for analysis

    Returns:
        str: Best preset name for the task, or 'default' if no specific match
    """
    # Priority order: content_type > model_type > prompt_analysis

    # 1. Content type based selection (highest priority)
    if content_type == 'image':
        return 'vision_analysis'
    elif content_type == 'code':
        return 'coding'
    elif content_type == 'srt':
        return 'text_analysis'

    # 2. Model type based selection
    if model_name:
        model_lower = model_name.lower()

        # Vision models
        if is_vision_model(model_name):
            return 'vision_analysis'

        # Reasoning/thinking models
        if is_thinking_model(model_name):
            return 'reasoning_mode'

        # MoE (Mixture of Experts) models
        moe_keywords = ['moe', 'mixtral', 'deepseek-moe', 'expert']
        if any(keyword in model_lower for keyword in moe_keywords):
            return 'moe_optimized'

        # Mathematical models
        math_keywords = ['math', 'deepseek-math', 'mathstral']
        if any(keyword in model_lower for keyword in math_keywords):
            return 'mathematical'

    # 3. Prompt analysis based selection (lowest priority)
    if prompt_text:
        prompt_lower = prompt_text.lower()

        # Mathematical/calculation tasks
        math_indicators = ['calculate', 'solve', 'equation', 'formula', 'math', 'algebra',
                           'geometry', 'statistics', 'probability', 'derivative', 'integral']
        if any(indicator in prompt_lower for indicator in math_indicators):
            return 'mathematical'

        # Coding/programming tasks
        code_indicators = ['code', 'program', 'function', 'debug', 'error', 'bug',
                           'algorithm', 'syntax', 'programming', 'script', 'refactor']
        if any(indicator in prompt_lower for indicator in code_indicators):
            return 'coding'

        # Translation tasks
        translation_indicators = ['translate', 'translation', 'language', 'español',
                                  'français', 'deutsch', 'italiano', 'português', '中文', '日本語']
        if any(indicator in prompt_lower for indicator in translation_indicators):
            return 'translation'

        # Creative writing tasks
        creative_indicators = ['write', 'story', 'poem', 'creative', 'fiction', 'novel',
                               'character', 'plot', 'narrative', 'dialogue', 'screenplay']
        if any(indicator in prompt_lower for indicator in creative_indicators):
            return 'creative_writing'

        # Summarization tasks
        summary_indicators = ['summary', 'summarize', 'summarise', 'brief', 'overview',
                              'key points', 'main ideas', 'extract', 'condense']
        if any(indicator in prompt_lower for indicator in summary_indicators):
            return 'summarization'

        # Analysis tasks
        analysis_indicators = ['analyze', 'analyse', 'analysis', 'examine', 'evaluate',
                               'assess', 'review', 'interpret', 'explain']
        if any(indicator in prompt_lower for indicator in analysis_indicators):
            return 'text_analysis'

    # Default fallback
    return 'default'
