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


def get_model_metadata(model_name="llama3"):
    """
    Fetches metadata for a specified model from a local Ollama API instance.
    Args:
        model_name (str, optional): The name of the model to retrieve metadata for. Defaults to "llama3".
    Returns:
        dict: The model metadata if the request is successful.
        str: An error message if the request fails or a connection error occurs.
    Raises:
        None: All exceptions are caught and returned as error messages.
    """
    try:
        response = requests.post(
            f'http://localhost:11434/api/show/', json={"model": model_name})

        if response.status_code == 200:
            model = response.json()
            return model
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"
