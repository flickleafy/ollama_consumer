def extract_capabilities_from_name(model_name):
    """
    Fallback function to detect capabilities from model name (original logic)

    Args:
        model_name (str): Name of the model to analyze

    Returns:
        list: List of capability strings
    """
    capabilities = []
    model_lower = model_name.lower()

    # Check for reasoning capability
    reasoning_keywords = [
        'reasoning', 'think', 'thought', 'o1', 'qwq', 'deepseek-r1',
        'phi4-reasoning', 'marco-o1'
    ]
    if any(keyword in model_lower for keyword in reasoning_keywords):
        capabilities.append('reasoning')

    # Check for vision capability
    vision_keywords = [
        'vision', 'visual', 'vl', 'image', 'multimodal', 'mm',
        'qwen2.5vl', 'llava', 'bakllava', 'moondream', 'cogvlm'
    ]
    if any(keyword in model_lower for keyword in vision_keywords):
        capabilities.append('vision')

    # Check for multimodal capability (broader than just vision)
    multimodal_keywords = [
        'multimodal', 'mm', 'llama4', 'gpt-4v', 'claude-3'
    ]
    if any(keyword in model_lower for keyword in multimodal_keywords):
        if 'vision' not in capabilities:  # Don't duplicate if already has vision
            capabilities.append('multimodal')
        else:
            # Replace vision with multimodal for models that are explicitly multimodal
            capabilities.remove('vision')
            capabilities.append('multimodal')

    # Check for MoE (Mixture of Experts) models
    moe_keywords = [
        'moe', 'mixtral', 'switch', 'expert', 'x', 'deepseek-r1:671b',
        'qwen3:235b', 'qwen3:30b', 'llama4:'
    ]
    # Special patterns for MoE detection
    if any(keyword in model_lower for keyword in moe_keywords) or \
       'x' in model_lower and ('b' in model_lower or 'expert' in model_lower) or \
       ('llama4:' in model_lower and 'x' in model_lower) or \
       ('qwen3:' in model_lower and ('235b' in model_lower or '30b' in model_lower)) or \
       'deepseek-r1:671b' in model_lower:
        capabilities.append('moe')

    # Check for "plus" variants
    if 'plus' in model_lower:
        capabilities.append('plus')

    # Check for large context models
    large_context_keywords = [
        'long', 'context', 'longcontext', '128k', '256k', '1m', '2m'
    ]
    if any(keyword in model_lower for keyword in large_context_keywords):
        capabilities.append('long-context')

    # Check for coding specialized models
    coding_keywords = [
        'code', 'coder', 'codellama', 'starcoder', 'wizard-coder', 'deepseek-coder'
    ]
    if any(keyword in model_lower for keyword in coding_keywords):
        capabilities.append('coding')

    # Check for math specialized models
    math_keywords = [
        'math', 'mathematician', 'mathstral', 'wizard-math'
    ]
    if any(keyword in model_lower for keyword in math_keywords):
        capabilities.append('math')

    return capabilities
