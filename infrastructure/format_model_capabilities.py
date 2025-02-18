def format_model_capabilities(capabilities):
    """
    Format capabilities list into a string for display

    Args:
        capabilities (list): List of capability strings

    Returns:
        str: Formatted capabilities string or empty string if no capabilities
    """
    if not capabilities:
        return ""

    # If both "thinking" and "reasoning" are present, only keep "reasoning"
    if 'thinking' in capabilities and 'reasoning' in capabilities:
        capabilities = [cap for cap in capabilities if cap != 'thinking']
    # If only "thinking" is present, replace it with "reasoning"
    elif 'thinking' in capabilities:
        capabilities = [cap if cap !=
                        'thinking' else 'reasoning' for cap in capabilities]

    # Sort capabilities for consistent ordering
    capability_order = ['reasoning', 'vision', 'multimodal', 'moe', 'plus',
                        'long-context', 'coding', 'math']
    sorted_capabilities = sorted(capabilities, key=lambda x: capability_order.index(
        x) if x in capability_order else len(capability_order))

    formatted = "(" + ")(".join(sorted_capabilities) + ")"
    return f" {formatted}"
