def is_thinking_model(model_name):
    """
    Check if a model supports thinking/reasoning mode based on model name

    Args:
        model_name (str): Name of the model to check

    Returns:
        bool: True if model likely supports thinking mode, False otherwise
    """
    thinking_keywords = [
        'reasoning', 'think', 'thought', 'o1', 'qwq', 'deepseek-r1',
        'phi4-reasoning', 'marco-o1'
    ]

    model_lower = model_name.lower()
    return any(keyword in model_lower for keyword in thinking_keywords)
