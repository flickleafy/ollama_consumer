from .color_text import color_text


import re


def format_model_response(response):
    """Format model response with colored thinking tags"""
    # Pattern to match <think>...</think> or <thinking>...</thinking> tags
    thinking_pattern = r'(<think>.*?</think>|<thinking>.*?</thinking>)'

    # Split the response by thinking tags
    parts = re.split(thinking_pattern, response,
                     flags=re.DOTALL | re.IGNORECASE)

    formatted_response = ""
    for part in parts:
        # Check if this part is a thinking tag
        if re.match(r'<think[^>]*>.*?</think[^>]*>', part, re.DOTALL | re.IGNORECASE):
            # Color thinking tags gray
            formatted_response += color_text(part, 'gray')
        else:
            # Keep regular response text yellow
            formatted_response += color_text(part, 'yellow')

    return formatted_response
