from .list_ollama_models import list_ollama_models


def check_ollama_storage():
    """Check storage location by examining models directory size"""
    try:
        models = list_ollama_models()
        if isinstance(models, list):
            return {
                "models_count": len(models),
                "models": models,
                "status": "Ollama is running correctly"
            }
        else:
            return {"status": "Error listing models", "error": models}
    except Exception as e:
        return {"status": "Error", "error": str(e)}
