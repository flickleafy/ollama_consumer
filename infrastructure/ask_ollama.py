from .get_advanced_params_from_config import get_advanced_params_from_config
from .is_vision_model import is_vision_model
from .is_thinking_model import is_thinking_model


import requests


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
