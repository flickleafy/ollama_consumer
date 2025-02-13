"""

Ollama Consumer - Interactive chat interface for Ollama models

Copyright (C) 2025 flickleafy

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

*** 

This module provides a comprehensive interface for interacting with 
Ollama language models, including model management, conversation 
handling, and service monitoring capabilities.

Classes:
    ModelManager: Handles loading, unloading, and state tracking of Ollama models

Functions:
    ask_ollama(prompt, model): Send a prompt to Ollama and get response
    list_ollama_models(): List all locally available models from Ollama
    get_current_loaded_model(): Get the currently loaded model from config
    set_current_loaded_model(model_name): Set the currently loaded model in config
    load_ollama_model(model): Load a model by sending a test prompt
    unload_ollama_model(model): Unload a model from Ollama's memory via API
    check_ollama_storage(): Check storage location by examining models directory size
    get_model_info(model_name): Get detailed information about a specific model
    select_model(previous_model): Display numbered list of models for user selection
    color_text(text, color): Apply terminal color formatting to text
    format_model_response(response): Format model response with colored thinking tags

Features:
- Interactive model selection and switching
- Automatic service monitoring and restart capabilities
- Error recovery for HTTP 500 responses
- Configuration persistence using INI files
- Colored terminal output for better user experience
- Support for model thinking tags visualization

The implementation uses the Ollama REST API (localhost:11434) for all model operations
and maintains state through a configuration file. The main execution loop provides
a continuous chat interface with command support for model switching and graceful exit.
Ollama Consumer - Interactive chat interface for Ollama models

"""

import requests
import json
import configparser
import os
import sys
import re
import subprocess
import time
import base64

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')


def ask_ollama(prompt, model="llama3", system_prompt=None, image_data=None, use_config_params=True):
    """
    Send a prompt to Ollama and get response with full parameter support.

    Args:
        prompt (str): The text prompt to send to the model
        model (str): Name of the model to use
        system_prompt (str, optional): System prompt to set context
        image_data (str, optional): Base64 encoded image data for vision models
        use_config_params (bool): Whether to apply advanced parameters from config

    Returns:
        str: Model response or error message
    """
    try:
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False  # Disable streaming to get a single JSON response
        }

        # Add system prompt if provided
        if system_prompt:
            payload['system'] = system_prompt

        # Apply advanced parameters from config if requested
        if use_config_params:
            advanced_params = get_advanced_params_from_config()

            # Map config parameters to Ollama API parameters
            param_mapping = {
                'temperature': 'temperature',
                'top_k': 'top_k',
                'top_p': 'top_p',
                'repeat_penalty': 'repeat_penalty',
                'seed': 'seed',
                'num_predict': 'num_predict',
                'num_ctx': 'num_ctx',
                'num_batch': 'num_batch',
                'num_gqa': 'num_gqa',
                'num_gpu': 'num_gpu',
                'main_gpu': 'main_gpu',
                'low_vram': 'low_vram',
                'f16_kv': 'f16_kv',
                'logits_all': 'logits_all',
                'vocab_only': 'vocab_only',
                'use_mmap': 'use_mmap',
                'use_mlock': 'use_mlock',
                'num_thread': 'num_thread'
            }

            # Add supported parameters to payload
            for config_param, api_param in param_mapping.items():
                if config_param in advanced_params:
                    payload[api_param] = advanced_params[config_param]

            # Handle streaming preference
            if 'stream_response' in advanced_params:
                payload['stream'] = advanced_params['stream_response']

            # Handle raw response mode
            if 'raw_response' in advanced_params:
                payload['raw'] = advanced_params['raw_response']

            # Handle thinking mode for compatible models
            if 'enable_thinking' in advanced_params:
                thinking_enabled = advanced_params['enable_thinking']
                if thinking_enabled or (thinking_enabled is None and is_thinking_model(model)):
                    # For thinking models, we might want to add special instructions
                    thinking_format = advanced_params.get(
                        'thinking_format', 'xml')
                    if thinking_format == 'xml' and '<think>' not in prompt:
                        # Only add thinking tags if not already present
                        thinking_instruction = "\n\nPlease use <think> tags to show your reasoning process."
                        payload['prompt'] = prompt + thinking_instruction

        # Handle image input for vision models
        if image_data:
            # Check if model supports vision
            vision_enabled = advanced_params.get(
                'enable_vision') if use_config_params else None
            if vision_enabled or (vision_enabled is None and is_vision_model(model)):
                payload['images'] = [image_data]
            else:
                print(
                    f"Warning: Image provided but model '{model}' may not support vision")
                payload['images'] = [image_data]  # Try anyway

        response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload
        )

        if response.status_code == 200:
            response_data = response.json()

            # Handle streaming vs non-streaming responses
            if payload.get('stream', False):
                # For streaming, we'd need to handle multiple JSON objects
                # For now, just return the response field
                return response_data.get('response', '')
            else:
                return response_data.get('response', '')
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Exception: {str(e)}"


def list_ollama_models():
    """List all locally available models from Ollama"""
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            return response.json().get('models', [])
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"


def get_system_prompt_from_config():
    """Get system prompt from config file if it exists"""
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        return config.get('ollama', 'system_prompt', fallback='').strip()
    except Exception:
        return ''


def get_advanced_params_from_config():
    """
    Get all advanced model parameters from config file

    Returns:
        dict: Dictionary containing all advanced parameters with their configured values
    """
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        params = {}

        if config.has_section('ollama'):
            # Numeric parameters
            numeric_params = [
                'temperature', 'top_k', 'top_p', 'repeat_penalty', 'seed',
                'num_predict', 'num_ctx', 'num_batch', 'num_gqa', 'num_gpu',
                'main_gpu', 'num_thread', 'max_image_size'
            ]

            for param in numeric_params:
                if config.has_option('ollama', param):
                    try:
                        value = config.get('ollama', param)
                        if value.strip() == '-1':
                            # -1 means auto/default, don't include in request
                            continue
                        elif param in ['temperature', 'top_p', 'repeat_penalty']:
                            params[param] = float(value)
                        else:
                            params[param] = int(value)
                    except (ValueError, TypeError):
                        continue

            # Boolean parameters
            boolean_params = [
                'low_vram', 'f16_kv', 'logits_all', 'vocab_only',
                'use_mmap', 'use_mlock', 'stream_response', 'raw_response'
            ]

            for param in boolean_params:
                if config.has_option('ollama', param):
                    try:
                        value = config.get('ollama', param).lower()
                        if value in ['true', 'false']:
                            params[param] = value == 'true'
                    except (ValueError, TypeError):
                        continue

            # String parameters
            string_params = [
                'thinking_format', 'reasoning_depth', 'image_quality', 'image_format'
            ]

            for param in string_params:
                if config.has_option('ollama', param):
                    value = config.get('ollama', param).strip()
                    if value and value != 'auto':
                        params[param] = value

            # Special handling for enable_thinking and enable_vision
            if config.has_option('ollama', 'enable_thinking'):
                thinking = config.get(
                    'ollama', 'enable_thinking').lower().strip()
                if thinking == 'true':
                    params['enable_thinking'] = True
                elif thinking == 'false':
                    params['enable_thinking'] = False
                # 'auto' means model-dependent, don't set explicitly

            if config.has_option('ollama', 'enable_vision'):
                vision = config.get('ollama', 'enable_vision').lower().strip()
                if vision == 'true':
                    params['enable_vision'] = True
                elif vision == 'false':
                    params['enable_vision'] = False
                # 'auto' means model-dependent, don't set explicitly

        return params
    except Exception:
        return {}


def is_vision_model(model_name):
    """
    Check if a model supports vision/image input based on model name

    Args:
        model_name (str): Name of the model to check

    Returns:
        bool: True if model likely supports vision, False otherwise
    """
    vision_keywords = [
        'vision', 'visual', 'vl', 'image', 'multimodal', 'mm',
        'qwen2.5vl', 'llava', 'bakllava', 'moondream', 'cogvlm'
    ]

    model_lower = model_name.lower()

    # Special case: reasoning models like phi4-reasoning are not vision models
    if 'reasoning' in model_lower and 'vl' not in model_lower:
        return False

    return any(keyword in model_lower for keyword in vision_keywords)


def is_thinking_model(model_name):
    """
    Check if a model supports thinking/reasoning mode based on model name

    Args:
        model_name (str): Name of the model to check

    Returns:
        bool: True if model likely supports thinking mode, False otherwise
    """
    thinking_keywords = [
        'reasoning', 'think', 'thought', 'o1', 'qwq', 'deepseek-r1',
        'phi4-reasoning', 'marco-o1'
    ]

    model_lower = model_name.lower()
    return any(keyword in model_lower for keyword in thinking_keywords)


def prepare_image_input(image_path_or_data):
    """
    Prepare image input for vision models

    Args:
        image_path_or_data (str): Path to image file or base64 encoded image data

    Returns:
        str: Base64 encoded image data, or None if failed
    """
    try:
        import base64

        # If it looks like a file path
        if os.path.exists(image_path_or_data):
            with open(image_path_or_data, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                return image_data
        # If it's already base64 data
        elif image_path_or_data.startswith('data:image/') or len(image_path_or_data) > 100:
            # Remove data URL prefix if present
            if image_path_or_data.startswith('data:image/'):
                image_path_or_data = image_path_or_data.split(',', 1)[1]
            return image_path_or_data
        else:
            return None
    except Exception:
        return None


# Model Management Functions - Handle loading/unloading operations


class ModelManager:
    """Manages Ollama model loading, unloading, and state tracking"""

    def __init__(self, config_path):
        self.config_path = config_path

    def get_current_loaded_model(self):
        """Get the currently loaded model from config"""
        config = configparser.ConfigParser()
        config.read(self.config_path)
        return config.get('ollama', 'current_loaded_model', fallback='')

    def set_current_loaded_model(self, model_name):
        """Set the currently loaded model in config"""
        config = configparser.ConfigParser()
        config.read(self.config_path)
        if 'ollama' not in config:
            config['ollama'] = {}
        config['ollama']['current_loaded_model'] = model_name or ''
        with open(self.config_path, 'w') as f:
            config.write(f)

    def load_model(self, model):
        """Load a model by sending a test prompt"""
        try:
            system_prompt = get_system_prompt_from_config()
            response = ask_ollama(
                "ping", model, system_prompt if system_prompt else None)
            if "Error" not in response:
                self.set_current_loaded_model(model)
                return {"success": True, "message": f"Model {model} loaded successfully"}
            else:
                return {"success": False, "message": f"Failed to load model {model}: {response}"}
        except Exception as e:
            return {"success": False, "message": f"Exception loading model {model}: {str(e)}"}

    def unload_model(self, model):
        """Unload a model from Ollama's memory via API"""
        try:
            response = requests.post(
                'http://localhost:11434/api/unload',
                json={"model": model}
            )
            if response.status_code == 200:
                self.set_current_loaded_model('')
                return {"success": True, "message": f"Model {model} unloaded successfully"}
            elif response.status_code == 404:
                # Model not found - probably already unloaded
                self.set_current_loaded_model('')
                return {"success": True, "message": f"Model {model} was not loaded (404 - already unloaded)"}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def unload_all_models(self):
        """Attempt to unload all known models"""
        models = list_ollama_models()
        if isinstance(models, list):
            for model_info in models:
                model_name = model_info['name']
                result = self.unload_model(model_name)
                print(f"Unload {model_name}: {result['message']}")
        self.set_current_loaded_model('')

    def is_ollama_running(self):
        """Check if Ollama service is running"""
        try:
            response = requests.get(
                'http://localhost:11434/api/version', timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def restart_ollama_service(self):
        """Attempt to restart the Ollama service automatically"""
        print("Attempting to restart Ollama service...")

        # First, check if we can find ollama process
        try:
            # Check if ollama is running as a process
            ps_result = subprocess.run(
                ["pgrep", "-f", "ollama"], capture_output=True, text=True)
            if ps_result.returncode == 0:
                print("Found running Ollama processes, attempting graceful restart...")
        except Exception:
            pass

        # Common service restart commands to try
        restart_commands = [
            # systemd service restart
            ["sudo", "systemctl", "restart", "ollama"],
            ["systemctl", "--user", "restart", "ollama"],
            # pkill and restart (if installed as binary)
            ["pkill", "-f", "ollama", "&&", "ollama", "serve"],
        ]

        for cmd in restart_commands:
            try:
                print(f"Trying: {' '.join(cmd)}")
                if "&&" in cmd:
                    # Handle compound commands
                    kill_cmd = cmd[:cmd.index("&&")]
                    start_cmd = cmd[cmd.index("&&") + 1:]
                    subprocess.run(kill_cmd, timeout=10, capture_output=True)
                    time.sleep(2)
                    subprocess.Popen(
                        start_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(3)
                else:
                    subprocess.run(cmd, timeout=10,
                                   capture_output=True, text=True)
                    time.sleep(3)

                # Check if service is now running
                if self.is_ollama_running():
                    print("✓ Ollama service restarted successfully!")
                    return True

            except subprocess.TimeoutExpired:
                print(f"Timeout running: {' '.join(cmd)}")
                continue
            except subprocess.CalledProcessError as e:
                print(f"Failed: {e}")
                continue
            except Exception as e:
                print(f"Error: {e}")
                continue

        return False

    def provide_manual_restart_instructions(self):
        """Provide user with manual restart instructions if automatic restart fails"""
        print("\n" + "="*60)
        print("MANUAL RESTART REQUIRED")
        print("="*60)
        print("Automatic restart failed. Please try one of these commands:")
        print("\n1. If Ollama is installed as a system service:")
        print("   sudo systemctl restart ollama")
        print("   # OR")
        print("   systemctl --user restart ollama")

        print("\n2. If Ollama is installed as a binary:")
        print("   pkill -f ollama")
        print("   ollama serve")

        print("\n3. If using Docker:")
        print("   docker restart ollama")
        print("   # OR")
        print("   docker-compose restart ollama")

        print("\n4. Alternative approach:")
        print("   killall ollama")
        print("   nohup ollama serve > /dev/null 2>&1 &")

        print("\nAfter restarting, press Enter to continue or 'q' to quit...")
        user_input = input().strip().lower()
        return user_input != 'q'

    def handle_error_500(self, attempted_model):
        """Handle error 500 by attempting to unload conflicting model and restart service if needed"""
        current_model = self.get_current_loaded_model()
        print("Error 500 detected. Attempting recovery...")

        # Try to unload the current model from config first
        if current_model:
            print(f"Trying to unload configured model: {current_model}")
            result = self.unload_model(current_model)
            print(f"Unload result: {result['message']}")

        # If still having issues, try unloading the attempted model
        print(f"Trying to unload attempted model: {attempted_model}")
        result = self.unload_model(attempted_model)
        print(f"Unload result: {result['message']}")

        # As last resort, try to unload all models
        print("As last resort, trying to unload all models...")
        self.unload_all_models()

        # Check if Ollama is still responsive
        if not self.is_ollama_running():
            print("Ollama service appears to be down. Attempting automatic restart...")

            if self.restart_ollama_service():
                return {"success": True, "message": "Service restarted successfully"}
            else:
                print("Automatic restart failed.")
                if self.provide_manual_restart_instructions():
                    # Check again after manual restart
                    if self.is_ollama_running():
                        print("✓ Service is now running!")
                        return {"success": True, "message": "Service manually restarted"}
                    else:
                        return {"success": False, "message": "Service still not responding"}
                else:
                    return {"success": False, "message": "User chose to quit"}

        return {"success": True, "message": "Recovery attempted - cleared all models"}

    def restart_service(self):
        """Restart the Ollama service"""
        try:
            # Attempt to stop the service
            print("Stopping Ollama service...")
            subprocess.run(["ollama", "stop"], check=True)

            # Wait for a few seconds to ensure it stops completely
            time.sleep(3)

            # Attempt to start the service
            print("Starting Ollama service...")
            subprocess.run(["ollama", "start"], check=True)

            print("Ollama service restarted successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error restarting Ollama service: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


# Create global model manager instance
model_manager = ModelManager(CONFIG_PATH)

# Convenience functions for backward compatibility


def get_current_loaded_model():
    return model_manager.get_current_loaded_model()


def set_current_loaded_model(model_name):
    model_manager.set_current_loaded_model(model_name)


def load_ollama_model(model):
    return model_manager.load_model(model)


def unload_ollama_model(model):
    return model_manager.unload_model(model)


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


def select_model(previous_model=None):
    """Display a numbered list of models and ask user to choose one. Handle model switching."""
    models = list_ollama_models()
    if not isinstance(models, list):
        print(f"Error retrieving models: {models}")
        return previous_model or "llama3"  # Default model if error

    print("\nAvailable Models:")
    for i, model in enumerate(models, 1):
        parameter_size = model.get('details', {}).get(
            'parameter_size', 'Unknown')
        print(f"{i}. {model['name']} - Parameters: {parameter_size}")

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


def color_text(text, color):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'gray': '\033[90m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


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


if __name__ == "__main__":
    print("\nOllama Chat Interface:")

    # Check if Ollama service is running before starting
    if not model_manager.is_ollama_running():
        print("⚠️  Ollama service is not running!")
        print("Attempting to start Ollama service...")

        if model_manager.restart_ollama_service():
            print("✓ Ollama service started successfully!")
        else:
            print("❌ Failed to start Ollama service automatically.")
            if not model_manager.provide_manual_restart_instructions():
                print("Exiting...")
                sys.exit(1)

            # Final check after manual intervention
            if not model_manager.is_ollama_running():
                print("❌ Ollama service is still not running. Exiting...")
                sys.exit(1)
            else:
                print("✓ Ollama service is now running!")

    selected_model = select_model()
    print(f"Using model: {selected_model}")

    # Show model capabilities
    if is_vision_model(selected_model):
        print(color_text(
            "📷 This model supports image input! Use 'img:path/to/image.jpg your prompt' to include images.", 'cyan'))
    if is_thinking_model(selected_model):
        print(color_text(
            "🧠 This model supports thinking mode! It may show reasoning in <think> tags.", 'cyan'))

    while True:
        print(color_text(
            "Enter your prompt (or 'exit' to quit, 's' to select new model):", 'green'))
        if is_vision_model(selected_model):
            print(color_text(
                "  📷 For images: img:path/to/image.jpg your prompt here", 'cyan'))

        prompt = input("> ")
        if prompt.lower() in ['exit', 'quit', 'q']:
            break
        elif prompt.lower() == 's':
            previous_model = selected_model
            selected_model = select_model(previous_model)
            print(f"Using model: {selected_model}")

            # Show capabilities for new model
            if is_vision_model(selected_model):
                print(color_text(
                    "📷 This model supports image input! Use 'img:path/to/image.jpg your prompt' to include images.", 'cyan'))
            if is_thinking_model(selected_model):
                print(color_text(
                    "🧠 This model supports thinking mode! It may show reasoning in <think> tags.", 'cyan'))
            continue

        # Parse image input if present
        image_data = None
        actual_prompt = prompt

        if prompt.startswith('img:'):
            # Extract image path and prompt
            parts = prompt[4:].split(' ', 1)
            if len(parts) >= 1:
                image_path = parts[0]
                actual_prompt = parts[1] if len(
                    parts) > 1 else "Describe this image."

                # Prepare image data
                image_data = prepare_image_input(image_path)
                if image_data is None:
                    print(color_text(
                        f"❌ Failed to load image: {image_path}", 'red'))
                    continue
                else:
                    print(color_text(f"📷 Image loaded: {image_path}", 'cyan'))

        print(color_text(f"User prompt: {actual_prompt}", 'green'))
        if image_data:
            print(color_text("📷 Image included in request", 'cyan'))

        print("System: Sending prompt to model...")
        system_prompt = get_system_prompt_from_config()
        response = ask_ollama(
            actual_prompt,
            selected_model,
            system_prompt if system_prompt else None,
            image_data
        )
        print("\nModel response:")
        print(format_model_response(response))
        print("\n" + "-"*50 + "\n")
