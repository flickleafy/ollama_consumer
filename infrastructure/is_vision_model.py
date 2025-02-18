def is_vision_model(model_name):
    """
    Check if a model supports vision/image input based on model name

    Args:
        model_name (str): Name of the model to check

    Returns:
        bool: True if model likely supports vision, False otherwise
    """
    vision_keywords = [
        'vision', 'visual', 'vl', 'image', 'multimodal', 'mm',
        'qwen2.5vl', 'llava', 'bakllava', 'moondream', 'cogvlm', 'llama4'
    ]

    model_lower = model_name.lower()

    return any(keyword in model_lower for keyword in vision_keywords)
