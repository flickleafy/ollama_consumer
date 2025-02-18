from .get_blacklisted_models import get_blacklisted_models


def filter_blacklisted_models(models, show_message=False):
    """
    Filter out blacklisted models from a list of models

    Args:
        models (list): List of model dictionaries or model names
        show_message (bool): Whether to show a message about filtered models

    Returns:
        list: Filtered list with blacklisted models removed
    """
    blacklisted_models = get_blacklisted_models()
    if not blacklisted_models:
        return models

    if not models:
        return models

    # Handle both list of dicts and list of strings
    if isinstance(models[0], dict):
        # List of model dictionaries
        original_count = len(models)
        filtered_models = [
            model for model in models
            if model.get('name', '') not in blacklisted_models
        ]
    else:
        # List of model names (strings)
        original_count = len(models)
        filtered_models = [
            model for model in models
            if model not in blacklisted_models
        ]

    filtered_count = original_count - len(filtered_models)

    if filtered_count > 0 and show_message:
        print(
            f"📋 Filtered out {filtered_count} blacklisted model(s): {', '.join(blacklisted_models)}")

    return filtered_models
