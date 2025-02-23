from .format_model_capabilities import format_model_capabilities
from .get_blacklisted_models import get_blacklisted_models
from .get_model_capabilities import get_model_capabilities
from .list_ollama_models import list_ollama_models
from .color_text import color_text
import psutil
import subprocess


def get_system_total_ram():
    """
    Get total system RAM including GPU memory and system memory in bytes

    Returns:
        int: Total RAM in bytes
    """
    total_ram = 0

    # Get system RAM
    try:
        system_ram = psutil.virtual_memory().total
        total_ram += system_ram
    except Exception:
        # Fallback: assume 8GB system RAM
        total_ram += 8 * 1024 * 1024 * 1024

    # Get GPU memory (NVIDIA)
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_memories = result.stdout.strip().split('\n')
            for gpu_mem in gpu_memories:
                if gpu_mem.strip():
                    # Convert MB to bytes
                    gpu_ram = int(gpu_mem.strip()) * 1024 * 1024
                    total_ram += gpu_ram
    except Exception:
        # Fallback: assume no GPU or can't detect
        pass

    # Try ROCm for AMD GPUs
    try:
        result = subprocess.run(['rocm-smi', '--showmeminfo', 'vram'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Parse ROCm output (basic implementation)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'Total VRAM' in line or 'Memory Total' in line:
                    # Extract memory size (this is a simplified parser)
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i + 1 < len(parts):
                            if 'GB' in parts[i + 1]:
                                gpu_ram = int(part) * 1024 * 1024 * 1024
                                total_ram += gpu_ram
                            elif 'MB' in parts[i + 1]:
                                gpu_ram = int(part) * 1024 * 1024
                                total_ram += gpu_ram
    except Exception:
        pass

    return total_ram


def get_model_physical_size(model_info):
    """
    Get the physical size of the model on disk in bytes

    Args:
        model_info (dict): Model information from Ollama API

    Returns:
        int: Model size in bytes
    """
    try:
        # The 'size' field from Ollama API contains the physical size in bytes
        return model_info.get('size', 0)
    except Exception:
        return 0


def determine_model_color(model_size_bytes, total_ram_bytes):
    """
    Determine the color for model display based on size vs RAM

    Args:
        model_size_bytes (int): Model size in bytes
        total_ram_bytes (int): Total system RAM in bytes

    Returns:
        str: Color name for display ('red', 'yellow', or None for white)
    """
    if model_size_bytes == 0 or total_ram_bytes == 0:
        return None  # Default color (white)

    # Model size plus 10% overhead
    model_with_10_percent = model_size_bytes * 1.1

    # Model size plus 15% overhead
    model_with_15_percent = model_size_bytes * 1.15

    # Model size plus 20% overhead
    model_with_20_percent = model_size_bytes * 1.2

    if model_with_10_percent > total_ram_bytes:
        # Model + 10% is bigger than total RAM - RED
        return 'red'
    elif model_with_15_percent <= total_ram_bytes and model_with_20_percent > total_ram_bytes:
        # Model + 15% fits but model + 20% doesn't - ORANGE/YELLOW
        return 'yellow'
    else:
        # Model + 20% fits with plenty of space - WHITE (default)
        return None


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

    # Get currently loaded models from Ollama
    loaded_models = []
    if model_manager:
        loaded_models_data = model_manager.get_loaded_models_from_ollama()
        loaded_models = [model['name'] for model in loaded_models_data]
        
        if loaded_models:
            print(f"\n🔋 Currently loaded in memory: {', '.join(loaded_models)}")

    # Get total system RAM once
    total_ram = get_system_total_ram()
    total_ram_gb = total_ram / (1024 * 1024 * 1024)
    print(f"💾 Total system RAM detected: {total_ram_gb:.1f} GB")

    # Show color legend
    print("\n🎨 Color Legend:")
    print(f"  {color_text('Red', 'red')} - Model too large for available RAM (may cause issues)")
    print(
        f"  {color_text('Yellow', 'yellow')} - Model fits but with limited headroom")
    print(f"  {color_text('Green', 'green')} - Model currently loaded in memory")
    print("  White - Model fits comfortably with plenty of RAM")

    print("\nAvailable Models:")
    for i, model in enumerate(models, 1):
        parameter_size = model.get('details', {}).get(
            'parameter_size', 'Unknown')
        capabilities = get_model_capabilities(model['name'])
        capabilities_formatted = format_model_capabilities(capabilities)

        # Check if this model is currently loaded
        is_loaded = model['name'] in loaded_models

        # Get model physical size and determine color
        model_size_bytes = get_model_physical_size(model)
        model_color = determine_model_color(model_size_bytes, total_ram)

        # Format the model line
        model_line = f"{i}. {model['name']} - Parameters: {parameter_size}{capabilities_formatted}"
        if is_loaded:
            model_line += " 🔋 (loaded)"

        # Apply color based on RAM requirements and model status
        if is_loaded:
            print(color_text(model_line, 'green'))
        elif model_color:
            print(color_text(model_line, model_color))
        else:
            print(model_line)

    while True:
        try:
            choice = int(input("\nSelect a model by number: "))
            if 1 <= choice <= len(models):
                selected = models[choice-1]['name']

                # Check if the selected model is already loaded
                if model_manager and model_manager.is_model_loaded(selected):
                    print(f"✅ Model {selected} is already loaded in memory.")
                    # Update the config to reflect current selection but don't reload
                    model_manager.set_current_loaded_model(selected)
                    return selected

                # Handle model switching for different models
                if previous_model and selected != previous_model:
                    print(f"Unloading previous model: {previous_model}")
                    result = model_manager.unload_model(previous_model)
                    print(f"Unload result: {result['message']}")

                # Load the selected model if it's not already loaded
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
