from .extract_capabilities_from_name import extract_capabilities_from_name


def extract_capabilities_from_api_data(model_info):
    """
    Extract capabilities from Ollama API model information

    Args:
        model_info (dict): Model information from Ollama API

    Returns:
        list: List of capability strings
    """
    capabilities = []

    # Get capabilities directly from API
    api_capabilities = model_info.get('capabilities', [])

    # Map API capabilities to our capability names
    for api_cap in api_capabilities:
        if api_cap == 'vision':
            capabilities.append('vision')
        elif api_cap == 'thinking':
            # Map "thinking" to "reasoning" - only add if not already present
            if 'reasoning' not in capabilities:
                capabilities.append('reasoning')
        elif api_cap == 'completion':
            # All models have completion, so we don't need to show this
            pass
        elif api_cap == 'chat':
            # Most models support chat, so we don't need to show this
            pass
        elif api_cap == 'quantized':
            pass
        else:
            # Add any other capabilities as-is, but map "thinking" to "reasoning"
            if api_cap == 'thinking':
                if 'reasoning' not in capabilities:
                    capabilities.append('reasoning')
            else:
                capabilities.append(api_cap)

    # Get model details for additional analysis
    details = model_info.get('details', {})
    model_name = model_info.get('model', '').lower()
    template = model_info.get('template', '').lower()
    system = model_info.get('system', '').lower()

    # Check for reasoning capabilities in system prompts or templates
    reasoning_indicators = [
        'reasoning', 'think', 'thought', 'step by step', 'chain of thought',
        'analyze', 'reasoning process', '<think>', 'reasoning steps'
    ]
    if any(indicator in template or indicator in system for indicator in reasoning_indicators):
        if 'reasoning' not in capabilities:
            capabilities.append('reasoning')

    # Check model family for additional insights
    family = details.get('family', '').lower()
    families = details.get('families', [])

    # Check families list for more detailed information
    for fam in families:
        fam_lower = fam.lower()
        if 'llava' in fam_lower or 'vision' in fam_lower:
            if 'vision' not in capabilities:
                capabilities.append('vision')
        if 'reasoning' in fam_lower or 'thinking' in fam_lower:
            if 'reasoning' not in capabilities:
                capabilities.append('reasoning')

    # Check parameter count for MoE detection
    param_size = details.get('parameter_size', '')
    if param_size:
        # Large parameter counts might indicate MoE models
        if 'B' in param_size:
            try:
                param_num = float(param_size.replace('B', '').replace(' ', ''))
                # Very large models (>100B) are often MoE, or models with 'x' pattern
                if param_num > 100 or 'x' in model_name:
                    capabilities.append('moe')
            except:
                pass

    # Fallback to name-based detection for additional capabilities not covered by API
    name_based_capabilities = extract_capabilities_from_name(model_name)

    # Merge capabilities, avoiding duplicates
    for cap in name_based_capabilities:
        if cap not in capabilities:
            capabilities.append(cap)

    # Final cleanup: ensure "thinking" is mapped to "reasoning"
    if 'thinking' in capabilities:
        if 'reasoning' not in capabilities:
            capabilities = [cap if cap !=
                            'thinking' else 'reasoning' for cap in capabilities]
        else:
            # Remove "thinking" if "reasoning" is already present
            capabilities = [cap for cap in capabilities if cap != 'thinking']

    return capabilities
