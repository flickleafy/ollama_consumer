# Model Management Functions - Handle loading/unloading operations


from .ask_ollama import ask_ollama
from .get_system_prompt_from_config import get_system_prompt_from_config
from .list_ollama_models import list_ollama_models


import requests


import configparser
import subprocess
import time


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

    def get_loaded_models_from_ollama(self):
        """Get list of currently loaded models from Ollama API using /api/ps endpoint"""
        try:
            response = requests.get('http://localhost:11434/api/ps', timeout=5)
            if response.status_code == 200:
                data = response.json()
                loaded_models = []
                if 'models' in data:
                    for model_info in data['models']:
                        loaded_models.append({
                            'name': model_info.get('name', ''),
                            'size': model_info.get('size', 0),
                            'size_vram': model_info.get('size_vram', 0),
                            'digest': model_info.get('digest', ''),
                            'details': model_info.get('details', {}),
                            'expires_at': model_info.get('expires_at', ''),
                            'modified_at': model_info.get('modified_at', '')
                        })
                return loaded_models
            else:
                return []
        except Exception as e:
            # If we can't connect to Ollama or any other error, return empty list
            return []

    def is_model_loaded(self, model_name):
        """Check if a specific model is currently loaded in Ollama's memory"""
        loaded_models = self.get_loaded_models_from_ollama()
        return any(model['name'] == model_name for model in loaded_models)

    def get_currently_loaded_model_name(self):
        """Get the name of the first currently loaded model (if any)"""
        loaded_models = self.get_loaded_models_from_ollama()
        if loaded_models:
            return loaded_models[0]['name']  # Return the first loaded model
        return None
