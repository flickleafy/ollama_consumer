from .extract_capabilities_from_api_data import extract_capabilities_from_api_data
from .extract_capabilities_from_name import extract_capabilities_from_name


import requests


def get_model_capabilities(model_name):
    """
    Get model capabilities from Ollama API

    Args:
        model_name (str): Name of the model to analyze

    Returns:
        list: List of capability strings based on API data
    """
    capabilities = []

    try:
        # Get detailed model information from Ollama API
        response = requests.post('http://localhost:11434/api/show',
                                 json={'name': model_name})

        if response.status_code == 200:
            model_info = response.json()

            # Extract capabilities from model information
            capabilities = extract_capabilities_from_api_data(model_info)

        else:
            # Fallback to keyword-based detection if API call fails
            capabilities = extract_capabilities_from_name(model_name)

    except Exception:
        # Fallback to keyword-based detection if there's any error
        capabilities = extract_capabilities_from_name(model_name)

    return capabilities
