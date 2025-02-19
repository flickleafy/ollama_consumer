from .list_ollama_models import list_ollama_models, get_model_metadata


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


def get_model_context_length(model_name):
    """
    Extract the context length from a model's metadata.

    Args:
        model_name (str): Name of the model to get context length for

    Returns:
        int: Context length in tokens, or None if not found
    """
    try:
        # Get model metadata using existing function
        model_data = get_model_metadata(model_name)

        if not isinstance(model_data, dict):
            return None

        # Look in model_info section first - this is where the actual context length is stored
        model_info = model_data.get('model_info', {})
        if isinstance(model_info, dict):
            # Try different possible field names for context length
            context_fields = [
                'context_length',
                'llama4.context_length',
                'qwen25vl.context_length',
                'general.context_length',
                'max_context_length',
                'context_size',
                'max_seq_len',
                'max_position_embeddings'
            ]

            for field in context_fields:
                if field in model_info:
                    try:
                        return int(model_info[field])
                    except (ValueError, TypeError):
                        continue

            # Check for architecture-specific patterns
            architecture = model_info.get('general.architecture', '')
            if architecture:
                # Try architecture-specific field names
                arch_field = f"{architecture}.context_length"
                if arch_field in model_info:
                    try:
                        return int(model_info[arch_field])
                    except (ValueError, TypeError):
                        pass

        # Fallback: check other sections of the model data
        # Sometimes context info might be in details or other sections
        details = model_data.get('details', {})
        if isinstance(details, dict):
            for field in ['context_length', 'max_context', 'context_size']:
                if field in details:
                    try:
                        return int(details[field])
                    except (ValueError, TypeError):
                        continue

        return None

    except Exception as e:
        print(f"Error getting context length for {model_name}: {str(e)}")
        return None
