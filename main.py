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
    format_model_response(response): Format model response with colored thinking tags visualization

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


def get_system_prompt_from_config(content_type=None):
    """
    Get system prompt from config file based on content type

    Args:
        content_type (str): Type of content - 'image', 'code', 'srt', or None for default

    Returns:
        str: Appropriate system prompt for the content type
    """
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        # If content type is specified and specialized prompt exists, use it
        if content_type and config.has_section('system_prompts'):
            if content_type == 'image' and config.has_option('system_prompts', 'image_analysis'):
                return config.get('system_prompts', 'image_analysis', fallback='').strip()
            elif content_type == 'code' and config.has_option('system_prompts', 'code_analysis'):
                return config.get('system_prompts', 'code_analysis', fallback='').strip()
            elif content_type == 'srt' and config.has_option('system_prompts', 'srt_analysis'):
                return config.get('system_prompts', 'srt_analysis', fallback='').strip()

        # Fall back to default system prompt
        return config.get('ollama', 'system_prompt', fallback='').strip()
    except configparser.Error as e:
        print(f"Warning: Error reading system prompt from config: {e}")
        return ''
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
    except configparser.Error:
        # Silently return empty dict if config has parsing errors
        return {}
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
        'qwen2.5vl', 'llava', 'bakllava', 'moondream', 'cogvlm', 'llama4'
    ]

    model_lower = model_name.lower()

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


def get_images_from_folder():
    """
    Get list of image files from the images folder

    Returns:
        list: List of image filenames, or empty list if folder doesn't exist
    """
    images_folder = os.path.join(os.path.dirname(__file__), 'content/images')

    if not os.path.exists(images_folder):
        return []

    # Common image file extensions
    image_extensions = {'.jpg', '.jpeg', '.png',
                        '.gif', '.bmp', '.webp', '.tiff', '.svg'}

    try:
        all_files = os.listdir(images_folder)
        image_files = []

        for file in all_files:
            file_lower = file.lower()
            if any(file_lower.endswith(ext) for ext in image_extensions):
                image_files.append(file)

        # Sort alphabetically for consistent ordering
        return sorted(image_files)
    except Exception as e:
        print(f"Error reading images folder: {e}")
        return []


def get_texts_from_folder():
    """
    Get list of text files from the texts folder

    Returns:
        list: List of text filenames, or empty list if folder doesn't exist
    """
    texts_folder = os.path.join(os.path.dirname(__file__), 'content/texts')

    if not os.path.exists(texts_folder):
        return []

    # Common text file extensions
    texts_extensions = {
        '.txt', '.md', '.rst', '.csv', '.json', '.xml', '.yaml', '.yml',
        '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp', '.cs',
        '.go', '.rb', '.php', '.html', '.htm', '.css', '.scss', '.less',
        '.sh', '.bat', '.ps1', '.ini', '.cfg', '.toml', '.pl', '.lua',
        '.swift', '.kt', '.dart', '.scala', '.sql', '.r', '.jl', '.m',
        '.vb', '.asm', '.s', '.vue', '.jsx', '.tsx'
    }

    try:
        all_files = os.listdir(texts_folder)
        text_files = []

        for file in all_files:
            file_lower = file.lower()
            if any(file_lower.endswith(ext) for ext in texts_extensions):
                text_files.append(file)

        # Sort alphabetically for consistent ordering
        return sorted(text_files)
    except Exception as e:
        print(f"Error reading texts folder: {e}")
        return []


def select_image_from_folder():
    """
    Display available images from the images folder and let user choose one

    Returns:
        str: Full path to selected image, or None if cancelled/no images
    """
    images = get_images_from_folder()

    if not images:
        print(color_text("📷 No images found in the 'images' folder.", 'yellow'))
        return None

    print(color_text("\n📷 Available images in 'images' folder:", 'cyan'))
    for i, image in enumerate(images, 1):
        print(f"{i}. {image}")

    print("0. Cancel (no image)")

    while True:
        try:
            choice = input(color_text(
                "\nSelect an image by number: ", 'green'))

            if choice.strip() == '0' or choice.strip().lower() == 'cancel':
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(images):
                selected_image = images[choice_num - 1]
                images_folder = os.path.join(
                    os.path.dirname(__file__), 'images')
                full_path = os.path.join(images_folder, selected_image)
                print(color_text(f"📷 Selected: {selected_image}", 'cyan'))
                return full_path
            else:
                print(f"Please enter a number between 0 and {len(images)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print(color_text("\nImage selection cancelled.", 'yellow'))
            return None


def select_text_from_folder():
    """
    Display available text files from the texts folder and let user choose one

    Returns:
        str: Full path to selected text file, or None if cancelled/no texts
    """
    texts = get_texts_from_folder()

    if not texts:
        print(color_text("📄 No text files found in the 'texts' folder.", 'yellow'))
        return None

    print(color_text("\n📄 Available text files in 'texts' folder:", 'cyan'))
    for i, text_file in enumerate(texts, 1):
        print(f"{i}. {text_file}")

    print("0. Cancel (no text file)")

    while True:
        try:
            choice = input(color_text(
                "\nSelect a text file by number: ", 'green'))

            if choice.strip() == '0' or choice.strip().lower() == 'cancel':
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(texts):
                selected_text = texts[choice_num - 1]
                texts_folder = os.path.join(
                    os.path.dirname(__file__), 'content/texts')
                full_path = os.path.join(texts_folder, selected_text)
                print(color_text(f"📄 Selected: {selected_text}", 'cyan'))
                return full_path
            else:
                print(f"Please enter a number between 0 and {len(texts)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print(color_text("\nText selection cancelled.", 'yellow'))
            return None


def show_image_help():
    """Show help information about image input options"""
    print(color_text("\n📷 Image Input Options:", 'cyan'))
    print("  1. 'img:' - Choose from images folder")
    print("  2. 'img:filename.jpg your prompt' - Use specific file from images folder")
    print("  3. 'img:/full/path/to/image.jpg your prompt' - Use full file path")
    print("  4. Type 'images' to see available images in folder")
    print(color_text("  Examples:", 'yellow'))
    print("    img: What do you see?")
    print("    img:/home/user/photo.png What's in this image?")
    print()


def show_text_help():
    """Show help information about text input options and automatic system prompt selection"""
    print(color_text("\n📄 Text Input Options:", 'cyan'))
    print("  1. 'text:' - Choose from texts folder")
    print("  2. 'text:filename.txt your prompt' - Use specific file from texts folder")
    print("  3. 'text:/full/path/to/file.txt your prompt' - Use full file path")
    print("  4. Type 'texts' to see available text files in folder")
    print(color_text("  Automatic System Prompt Selection:", 'yellow'))
    print("    🎯 Code files (.py, .js, .java, etc.) → Code Analysis prompt")
    print("    🎯 Subtitle files (.srt, .vtt, etc.) → Video Transcript Analysis prompt")
    print("    🎯 Other text files → Default prompt")
    print(color_text("  Examples:", 'yellow'))
    print("    text: Analyze this file")
    print("    text:script.py Explain what this code does")
    print("    text:video_transcript.srt Summarize this video")
    print()


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


def extract_capabilities_from_api_data(model_info):
    """
    Extract capabilities from Ollama API model information

    Args:
        model_info (dict): Model information from Ollama API

    Returns:
        list: List of capability strings
    """
    capabilities = []

    # Get capabilities directly from API
    api_capabilities = model_info.get('capabilities', [])

    # Map API capabilities to our capability names
    for api_cap in api_capabilities:
        if api_cap == 'vision':
            capabilities.append('vision')
        elif api_cap == 'thinking':
            # Map "thinking" to "reasoning" - only add if not already present
            if 'reasoning' not in capabilities:
                capabilities.append('reasoning')
        elif api_cap == 'completion':
            # All models have completion, so we don't need to show this
            pass
        elif api_cap == 'chat':
            # Most models support chat, so we don't need to show this
            pass
        elif api_cap == 'quantized':
            pass
        else:
            # Add any other capabilities as-is, but map "thinking" to "reasoning"
            if api_cap == 'thinking':
                if 'reasoning' not in capabilities:
                    capabilities.append('reasoning')
            else:
                capabilities.append(api_cap)

    # Get model details for additional analysis
    details = model_info.get('details', {})
    model_name = model_info.get('model', '').lower()
    template = model_info.get('template', '').lower()
    system = model_info.get('system', '').lower()

    # Check for reasoning capabilities in system prompts or templates
    reasoning_indicators = [
        'reasoning', 'think', 'thought', 'step by step', 'chain of thought',
        'analyze', 'reasoning process', '<think>', 'reasoning steps'
    ]
    if any(indicator in template or indicator in system for indicator in reasoning_indicators):
        if 'reasoning' not in capabilities:
            capabilities.append('reasoning')

    # Check model family for additional insights
    family = details.get('family', '').lower()
    families = details.get('families', [])

    # Check families list for more detailed information
    for fam in families:
        fam_lower = fam.lower()
        if 'llava' in fam_lower or 'vision' in fam_lower:
            if 'vision' not in capabilities:
                capabilities.append('vision')
        if 'reasoning' in fam_lower or 'thinking' in fam_lower:
            if 'reasoning' not in capabilities:
                capabilities.append('reasoning')

    # Check parameter count for MoE detection
    param_size = details.get('parameter_size', '')
    if param_size:
        # Large parameter counts might indicate MoE models
        if 'B' in param_size:
            try:
                param_num = float(param_size.replace('B', '').replace(' ', ''))
                # Very large models (>100B) are often MoE, or models with 'x' pattern
                if param_num > 100 or 'x' in model_name:
                    capabilities.append('moe')
            except:
                pass

    # Fallback to name-based detection for additional capabilities not covered by API
    name_based_capabilities = extract_capabilities_from_name(model_name)

    # Merge capabilities, avoiding duplicates
    for cap in name_based_capabilities:
        if cap not in capabilities:
            capabilities.append(cap)

    # Final cleanup: ensure "thinking" is mapped to "reasoning"
    if 'thinking' in capabilities:
        if 'reasoning' not in capabilities:
            capabilities = [cap if cap !=
                            'thinking' else 'reasoning' for cap in capabilities]
        else:
            # Remove "thinking" if "reasoning" is already present
            capabilities = [cap for cap in capabilities if cap != 'thinking']

    return capabilities


def extract_capabilities_from_name(model_name):
    """
    Fallback function to detect capabilities from model name (original logic)

    Args:
        model_name (str): Name of the model to analyze

    Returns:
        list: List of capability strings
    """
    capabilities = []
    model_lower = model_name.lower()

    # Check for reasoning capability
    reasoning_keywords = [
        'reasoning', 'think', 'thought', 'o1', 'qwq', 'deepseek-r1',
        'phi4-reasoning', 'marco-o1'
    ]
    if any(keyword in model_lower for keyword in reasoning_keywords):
        capabilities.append('reasoning')

    # Check for vision capability
    vision_keywords = [
        'vision', 'visual', 'vl', 'image', 'multimodal', 'mm',
        'qwen2.5vl', 'llava', 'bakllava', 'moondream', 'cogvlm'
    ]
    if any(keyword in model_lower for keyword in vision_keywords):
        capabilities.append('vision')

    # Check for multimodal capability (broader than just vision)
    multimodal_keywords = [
        'multimodal', 'mm', 'llama4', 'gpt-4v', 'claude-3'
    ]
    if any(keyword in model_lower for keyword in multimodal_keywords):
        if 'vision' not in capabilities:  # Don't duplicate if already has vision
            capabilities.append('multimodal')
        else:
            # Replace vision with multimodal for models that are explicitly multimodal
            capabilities.remove('vision')
            capabilities.append('multimodal')

    # Check for MoE (Mixture of Experts) models
    moe_keywords = [
        'moe', 'mixtral', 'switch', 'expert', 'x', 'deepseek-r1:671b',
        'qwen3:235b', 'qwen3:30b', 'llama4:'
    ]
    # Special patterns for MoE detection
    if any(keyword in model_lower for keyword in moe_keywords) or \
       'x' in model_lower and ('b' in model_lower or 'expert' in model_lower) or \
       ('llama4:' in model_lower and 'x' in model_lower) or \
       ('qwen3:' in model_lower and ('235b' in model_lower or '30b' in model_lower)) or \
       'deepseek-r1:671b' in model_lower:
        capabilities.append('moe')

    # Check for "plus" variants
    if 'plus' in model_lower:
        capabilities.append('plus')

    # Check for large context models
    large_context_keywords = [
        'long', 'context', 'longcontext', '128k', '256k', '1m', '2m'
    ]
    if any(keyword in model_lower for keyword in large_context_keywords):
        capabilities.append('long-context')

    # Check for coding specialized models
    coding_keywords = [
        'code', 'coder', 'codellama', 'starcoder', 'wizard-coder', 'deepseek-coder'
    ]
    if any(keyword in model_lower for keyword in coding_keywords):
        capabilities.append('coding')

    # Check for math specialized models
    math_keywords = [
        'math', 'mathematician', 'mathstral', 'wizard-math'
    ]
    if any(keyword in model_lower for keyword in math_keywords):
        capabilities.append('math')

    return capabilities


def format_model_capabilities(capabilities):
    """
    Format capabilities list into a string for display

    Args:
        capabilities (list): List of capability strings

    Returns:
        str: Formatted capabilities string or empty string if no capabilities
    """
    if not capabilities:
        return ""

    # If both "thinking" and "reasoning" are present, only keep "reasoning"
    if 'thinking' in capabilities and 'reasoning' in capabilities:
        capabilities = [cap for cap in capabilities if cap != 'thinking']
    # If only "thinking" is present, replace it with "reasoning"
    elif 'thinking' in capabilities:
        capabilities = [cap if cap !=
                        'thinking' else 'reasoning' for cap in capabilities]

    # Sort capabilities for consistent ordering
    capability_order = ['reasoning', 'vision', 'multimodal', 'moe', 'plus',
                        'long-context', 'coding', 'math']
    sorted_capabilities = sorted(capabilities, key=lambda x: capability_order.index(
        x) if x in capability_order else len(capability_order))

    formatted = "(" + ")(".join(sorted_capabilities) + ")"
    return f" {formatted}"


def select_model(previous_model=None):
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


def color_text(text, color):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'gray': '\033[90m',
        'cyan': '\033[96m',
        'red': '\033[91m',
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


def get_blacklisted_models():
    """
    Get list of blacklisted models from config.ini

    Returns:
        list: List of blacklisted model names, or empty list if none/error
    """
    try:
        config = configparser.ConfigParser()

        # Check if config file exists
        config_path = CONFIG_PATH
        if not os.path.exists(config_path):
            return []

        config.read(config_path)

        # Get blacklisted models from the [blacklist] section
        if config.has_section('blacklist') and config.has_option('blacklist', 'models'):
            blacklist_str = config.get('blacklist', 'models')

            # Parse the list - handle different formats:
            # - JSON array: ["model1", "model2"]
            # - Comma-separated: model1, model2, model3
            # - Newline-separated: model1\nmodel2\nmodel3

            blacklist_str = blacklist_str.strip()
            if not blacklist_str:
                return []

            # Try parsing as JSON array first
            try:
                blacklisted_models = json.loads(blacklist_str)
                if isinstance(blacklisted_models, list):
                    return [str(model).strip() for model in blacklisted_models if model]
            except (ValueError, json.JSONDecodeError):
                pass

            # Fall back to comma or newline separated
            if ',' in blacklist_str:
                # Comma-separated
                blacklisted_models = [model.strip().strip('"\'')
                                      for model in blacklist_str.split(',')]
            else:
                # Newline-separated or single model
                blacklisted_models = [model.strip().strip('"\'')
                                      for model in blacklist_str.split('\n')]

            # Filter out empty strings
            return [model for model in blacklisted_models if model]

        return []

    except configparser.Error as e:
        # Only show this specific error if it's not related to the system_prompts section
        if 'system_prompts' not in str(e):
            print(
                f"Warning: Error reading blacklisted models from config: {e}")
        return []
    except Exception as e:
        # Print error but don't fail the application
        print(f"Warning: Error reading blacklisted models from config: {e}")
        return []


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


def handle_special_input_tag(prompt):
    """
    Handle prompts starting with 'img:' or 'text:' tags.
    For 'img:', use select_image_from_folder and prepare_image_input.
    For 'text:', use select_text_from_folder and read the text file.
    Returns:
        tuple: (actual_prompt, image_data, text_data, content_type)
            - actual_prompt: str, the prompt to send to the model
            - image_data: str or None, base64 image data if applicable
            - text_data: str or None, text file contents if applicable
            - content_type: str or None, detected content type ('image', 'code', 'srt', etc.)
    """
    if prompt.startswith('img:'):
        parts = prompt[4:].split(' ', 1)
        if len(parts) == 0 or parts[0].strip() == '':
            selected_image_path = select_image_from_folder()
            if selected_image_path is None:
                return None, None, None, None  # User cancelled
            actual_prompt = input(color_text(
                "Enter your prompt for the image: ", 'green'))
            if not actual_prompt.strip():
                actual_prompt = "Describe this image."
            image_data = prepare_image_input(selected_image_path)
            if image_data is None:
                print(color_text(
                    f"❌ Failed to load image: {selected_image_path}", 'red'))
                return None, None, None, None
            else:
                print(color_text(
                    f"📷 Image loaded: {os.path.basename(selected_image_path)}", 'cyan'))
            return actual_prompt, image_data, None, 'image'
        else:
            image_path = parts[0]
            actual_prompt = parts[1] if len(
                parts) > 1 else "Describe this image."
            if not os.path.sep in image_path and not os.path.exists(image_path):
                images_folder = os.path.join(
                    os.path.dirname(__file__), 'images')
                full_image_path = os.path.join(images_folder, image_path)
                if os.path.exists(full_image_path):
                    image_path = full_image_path
            image_data = prepare_image_input(image_path)
            if image_data is None:
                print(color_text(
                    f"❌ Failed to load image: {image_path}", 'red'))
                if not os.path.exists(image_path):
                    images = get_images_from_folder()
                    if images:
                        print(color_text(
                            "Available images in folder:", 'yellow'))
                        for img in images:
                            print(f"  - {img}")
                return None, None, None, None
            else:
                print(color_text(
                    f"📷 Image loaded: {os.path.basename(image_path)}", 'cyan'))
            return actual_prompt, image_data, None, 'image'
    elif prompt.startswith('text:'):
        parts = prompt[5:].split(' ', 1)
        if len(parts) == 0 or parts[0].strip() == '':
            selected_text_path = select_text_from_folder()
            if selected_text_path is None:
                return None, None, None, None  # User cancelled
            actual_prompt = input(color_text(
                "Enter your prompt for the text file: ", 'green'))
            if not actual_prompt.strip():
                actual_prompt = "Analyze this text."
            try:
                with open(selected_text_path, 'r', encoding='utf-8') as f:
                    text_data = f.read()
                print(color_text(
                    f"📄 Text loaded: {os.path.basename(selected_text_path)}", 'cyan'))
                # Detect content type based on file path and content
                content_type = detect_content_type(
                    selected_text_path, text_data)
            except Exception as e:
                print(color_text(
                    f"❌ Failed to load text: {selected_text_path} ({e})", 'red'))
                return None, None, None, None
            return actual_prompt, None, text_data, content_type
        else:
            text_path = parts[0]
            actual_prompt = parts[1] if len(
                parts) > 1 else "Analyze this text."
            if not os.path.sep in text_path and not os.path.exists(text_path):
                texts_folder = os.path.join(
                    os.path.dirname(__file__), 'content/texts')
                full_text_path = os.path.join(texts_folder, text_path)
                if os.path.exists(full_text_path):
                    text_path = full_text_path
            try:
                with open(text_path, 'r', encoding='utf-8') as f:
                    text_data = f.read()
                print(color_text(
                    f"📄 Text loaded: {os.path.basename(text_path)}", 'cyan'))
                # Detect content type based on file path and content
                content_type = detect_content_type(text_path, text_data)
            except Exception as e:
                print(color_text(
                    f"❌ Failed to load text: {text_path} ({e})", 'red'))
                return None, None, None, None
            return actual_prompt, None, text_data, content_type
    else:
        return None, None, None, None


def detect_content_type(file_path=None, text_data=None):
    """
    Detect content type based on file extension and content

    Args:
        file_path (str): Path to the file
        text_data (str): Text content of the file

    Returns:
        str: Content type - 'code', 'srt', or None for generic text
    """
    if file_path:
        file_lower = file_path.lower()

        # Check for SRT/subtitle files
        if file_lower.endswith(('.srt', '.vtt', '.ass', '.ssa', '.sub')):
            return 'srt'

        # Check for source code file extensions
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp', '.cs',
            '.go', '.rb', '.php', '.html', '.htm', '.css', '.scss', '.less',
            '.sh', '.bat', '.ps1', '.pl', '.lua', '.swift', '.kt', '.dart',
            '.scala', '.sql', '.r', '.jl', '.m', '.vb', '.asm', '.s',
            '.vue', '.jsx', '.tsx', '.json', '.xml', '.yaml', '.yml'
        }

        if any(file_lower.endswith(ext) for ext in code_extensions):
            return 'code'

    # If we have text data, try to detect SRT format by content
    if text_data:
        # SRT files typically have timestamp patterns like "00:01:23,456 --> 00:01:26,789"
        srt_pattern = r'\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}'
        if re.search(srt_pattern, text_data):
            return 'srt'

        # Check for common code patterns (basic heuristics)
        code_patterns = [
            r'def\s+\w+\s*\(',  # Python functions
            r'function\s+\w+\s*\(',  # JavaScript functions
            r'class\s+\w+',  # Class definitions
            r'import\s+\w+',  # Import statements
            r'#include\s*<',  # C/C++ includes
            r'<?xml\s+version',  # XML declarations
            r'<!DOCTYPE\s+html',  # HTML doctypes
        ]

        if any(re.search(pattern, text_data, re.IGNORECASE) for pattern in code_patterns):
            return 'code'

    return None  # Generic text, use default prompt


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
            "📷 This model supports image input! Use 'img:' to choose from images folder or 'help-img' for more options.", 'cyan'))
    if is_thinking_model(selected_model):
        print(color_text(
            "🧠 This model supports thinking mode! It may show reasoning in <think> tags.", 'cyan'))

    while True:
        print(color_text(
            "Enter your prompt (or 'exit' to quit, 's' to select new model):", 'green'))
        if is_vision_model(selected_model):
            print(color_text(
                "  📷 For images: 'img:' to choose from images folder, 'help-img' for help", 'cyan'))
        print(color_text(
            "  📄 For text/code: 'text:' to choose from texts folder, 'help-text' for help", 'cyan'))

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
                    "📷 This model supports image input! Use 'img:' to choose from images folder or 'help-img' for more options.", 'cyan'))
            if is_thinking_model(selected_model):
                print(color_text(
                    "🧠 This model supports thinking mode! It may show reasoning in <think> tags.", 'cyan'))
            continue
        elif prompt.lower() in ['images', 'list-images']:
            # Show available images
            images = get_images_from_folder()
            if images:
                print(color_text("\n📷 Available images in 'images' folder:", 'cyan'))
                for i, image in enumerate(images, 1):
                    print(f"  {i}. {image}")
                print(color_text(
                    "Use 'img:filename.jpg your prompt' to use a specific image.", 'yellow'))
            else:
                print(color_text("📷 No images found in the 'images' folder.", 'yellow'))
            continue
        elif prompt.lower() in ['help-img', 'img-help', 'image-help']:
            show_image_help()
            continue
        elif prompt.lower() in ['help-text', 'text-help']:
            show_text_help()
            continue
        elif prompt.lower() in ['texts', 'list-texts']:
            # Show available text files
            texts = get_texts_from_folder()
            if texts:
                print(color_text("\n📄 Available text files in 'texts' folder:", 'cyan'))
                for i, text_file in enumerate(texts, 1):
                    print(f"  {i}. {text_file}")
                print(color_text(
                    "Use 'text:filename.txt your prompt' to use a specific text file.", 'yellow'))
            else:
                print(color_text(
                    "📄 No text files found in the 'texts' folder.", 'yellow'))
            continue
        elif prompt.lower() in ['help-text', 'text-help', 'file-help']:
            show_text_help()
            continue

        # Parse image input if present
        image_data = None
        actual_prompt = prompt
        content_type = None

        # Unified special input tag handler (img:, text:, etc.)
        if prompt.startswith('img:') or prompt.startswith('text:'):
            actual_prompt, image_data, text_data, content_type = handle_special_input_tag(
                prompt)
            if actual_prompt is None:
                continue  # User cancelled or error
            # If text_data is loaded, append it to the prompt for model input
            if text_data:
                actual_prompt = f"{actual_prompt}\n\n```\n{text_data}\n```"

        print(color_text(f"User prompt: {actual_prompt}", 'green'))
        if image_data:
            print(color_text("📷 Image included in request", 'cyan'))
        if content_type:
            content_type_names = {
                'image': 'Image Analysis',
                'code': 'Code Analysis',
                'srt': 'Video Transcript Analysis'
            }
            if content_type in content_type_names:
                print(color_text(
                    f"🎯 Using specialized prompt for: {content_type_names[content_type]}", 'cyan'))

        print("System: Sending prompt to model...")
        system_prompt = get_system_prompt_from_config(content_type)

        # Start timing the API request
        start_time = time.time()

        response = ask_ollama(
            actual_prompt,
            selected_model,
            system_prompt if system_prompt else None,
            image_data
        )

        # Stop timing and calculate elapsed time
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Format elapsed time
        if elapsed_time < 60:
            time_str = f"{elapsed_time:.1f}s"
        else:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            time_str = f"{minutes}m {seconds:.1f}s"

        print(f"\nModel response ({time_str}):")
        print(format_model_response(response))
        print("\n" + "-"*50 + "\n")
