from .list_ollama_models import list_ollama_models


def get_model_info(model_name="llama3"):
    """Get detailed information about a specific model"""
    try:
        models = list_ollama_models()
        if isinstance(models, list):
            for model in models:
                if model_name in model['name']:
                    return {
                        "name": model['name'],
                        "size_gb": round(model['size'] / (1024**3), 2),
                        "parameter_size": model['details']['parameter_size'],
                        "family": model['details']['family'],
                        "format": model['details']['format'],
                        "quantization": model['details']['quantization_level'],
                        "modified": model['modified_at']
                    }
            return f"Model '{model_name}' not found"
        else:
            return f"Error: {models}"
    except Exception as e:
        return f"Error: {str(e)}"
