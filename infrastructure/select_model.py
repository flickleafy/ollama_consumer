from .format_model_capabilities import format_model_capabilities
from .get_blacklisted_models import get_blacklisted_models
from .get_model_capabilities import get_model_capabilities
from .list_ollama_models import list_ollama_models


def select_model(previous_model=None, model_manager=None):
    """Display a numbered list of models and ask user to choose one. Handle model switching."""
    # Check for blacklisted models and show info
    blacklisted_models = get_blacklisted_models()
    if blacklisted_models:
        print(
            f"\n📋 Note: {len(blacklisted_models)} model(s) are blacklisted and hidden: {', '.join(blacklisted_models)}")

    models = list_ollama_models()
    if not isinstance(models, list):
        print(f"Error retrieving models: {models}")
        return previous_model or "llama3"  # Default model if error

    # Sort models alphabetically by name
    models.sort(key=lambda model: model['name'].lower())

    print("\nAvailable Models:")
    for i, model in enumerate(models, 1):
        parameter_size = model.get('details', {}).get(
            'parameter_size', 'Unknown')
        capabilities = get_model_capabilities(model['name'])
        capabilities_formatted = format_model_capabilities(capabilities)
        print(
            f"{i}. {model['name']} - Parameters: {parameter_size}{capabilities_formatted}")

    while True:
        try:
            choice = int(input("\nSelect a model by number: "))
            if 1 <= choice <= len(models):
                selected = models[choice-1]['name']

                # Handle model switching
                if previous_model and selected != previous_model:
                    print(f"Unloading previous model: {previous_model}")
                    result = model_manager.unload_model(previous_model)
                    print(f"Unload result: {result['message']}")

                # Load the selected model
                print(f"Loading model: {selected} ...")
                load_result = model_manager.load_model(selected)

                if load_result['success']:
                    print(f"Model {selected} loaded successfully.")
                    return selected
                else:
                    print(f"Failed to load model: {load_result['message']}")

                    # Handle error 500 case with recovery and potential restart
                    if "Error: 500" in load_result['message']:
                        print("Attempting automatic recovery...")
                        recovery_result = model_manager.handle_error_500(
                            selected)

                        if recovery_result['success']:
                            # Try loading again after recovery
                            print(f"Retrying load of {selected}...")
                            retry_result = model_manager.load_model(selected)

                            if retry_result['success']:
                                print(
                                    f"Model {selected} loaded successfully after recovery.")
                                return selected
                            else:
                                print(
                                    "Recovery failed. Please try a different model.")
                                print(f"Error: {retry_result['message']}")
                        else:
                            print("Recovery and restart attempts failed.")
                            if "User chose to quit" in recovery_result['message']:
                                return previous_model or "llama3"

                    # Ask user if they want to try another model
                    retry = input(
                        "Would you like to try another model? (y/n): ").lower()
                    if retry != 'y':
                        return previous_model or "llama3"
                    continue
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nSelection cancelled.")
            return previous_model or "llama3"
