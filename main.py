import requests
import json
import configparser
import os
import sys
import re
import subprocess
import time

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')

def ask_ollama(prompt, model="llama3"):
    """Send a prompt to Ollama and get response. Pure question/answer function."""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False  # Disable streaming to get a single JSON response
            }
        )
        if response.status_code == 200:
            return response.json().get('response', '')
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
            response = ask_ollama("ping", model)
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
            response = requests.get('http://localhost:11434/api/version', timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def restart_ollama_service(self):
        """Attempt to restart the Ollama service automatically"""
        print("Attempting to restart Ollama service...")
        
        # First, check if we can find ollama process
        try:
            # Check if ollama is running as a process
            ps_result = subprocess.run(["pgrep", "-f", "ollama"], capture_output=True, text=True)
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
                    subprocess.Popen(start_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(3)
                else:
                    subprocess.run(cmd, timeout=10, capture_output=True, text=True)
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
        parameter_size = model.get('details', {}).get('parameter_size', 'Unknown')
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
                        recovery_result = model_manager.handle_error_500(selected)
                        
                        if recovery_result['success']:
                            # Try loading again after recovery
                            print(f"Retrying load of {selected}...")
                            retry_result = model_manager.load_model(selected)
                            
                            if retry_result['success']:
                                print(f"Model {selected} loaded successfully after recovery.")
                                return selected
                            else:
                                print("Recovery failed. Please try a different model.")
                                print(f"Error: {retry_result['message']}")
                        else:
                            print("Recovery and restart attempts failed.")
                            if "User chose to quit" in recovery_result['message']:
                                return previous_model or "llama3"
                    
                    # Ask user if they want to try another model
                    retry = input("Would you like to try another model? (y/n): ").lower()
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
    parts = re.split(thinking_pattern, response, flags=re.DOTALL | re.IGNORECASE)
    
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
    while True:
        print(color_text("Enter your prompt (or 'exit' to quit, 's' to select new model):", 'green'))
        prompt = input("> ")
        if prompt.lower() in ['exit', 'quit', 'q']:
            break
        elif prompt.lower() == 's':
            previous_model = selected_model
            selected_model = select_model(previous_model)
            print(f"Using model: {selected_model}")
            continue
        print(color_text(f"User prompt: {prompt}", 'green'))
        print("System: Sending prompt to model...")
        response = ask_ollama(prompt, selected_model)
        print("\nModel response:")
        print(format_model_response(response))
        print("\n" + "-"*50 + "\n")