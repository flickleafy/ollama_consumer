from .filter_blacklisted_models import filter_blacklisted_models


import requests


def list_ollama_models(exclude_blacklisted=True):
    """
    List all locally available models from Ollama

    Args:
        exclude_blacklisted (bool): Whether to exclude blacklisted models from the list

    Returns:
        list: List of model dictionaries, or error string if failed
    """
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            if exclude_blacklisted:
                models = filter_blacklisted_models(models)
            return models
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"
