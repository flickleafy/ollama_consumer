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

import os
import sys
import time

from infrastructure.ModelManager import ModelManager
from infrastructure.ask_ollama import ask_ollama
from infrastructure.ask_preset_override_enhanced import ask_preset_override_enhanced
from infrastructure.auto_apply_best_preset import auto_apply_best_preset
from infrastructure.color_text import color_text
from infrastructure.format_model_response import format_model_response
from infrastructure.get_best_preset_for_task import get_best_preset_for_task
from infrastructure.get_images_from_folder import get_images_from_folder
from infrastructure.get_system_prompt_from_config import get_system_prompt_from_config
from infrastructure.get_texts_from_folder import get_texts_from_folder
from infrastructure.handle_special_input_tag import handle_special_input_tag
from infrastructure.is_thinking_model import is_thinking_model
from infrastructure.is_vision_model import is_vision_model
from infrastructure.list_available_presets import list_available_presets
from infrastructure.select_model import select_model
from infrastructure.show_image_help import show_image_help
from infrastructure.show_text_help import show_text_help
from infrastructure.save_response_to_markdown import save_response_to_markdown

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')


# Create global model manager instance
model_manager = ModelManager(CONFIG_PATH)

# Global variables for preset override management
preset_override_active = False
preset_override_name = None

# Convenience functions for backward compatibility


def get_current_loaded_model():
    return model_manager.get_current_loaded_model()


def set_current_loaded_model(model_name):
    model_manager.set_current_loaded_model(model_name)


def load_ollama_model(model):
    return model_manager.load_model(model)


def unload_ollama_model(model):
    return model_manager.unload_model(model)


def set_preset_override(preset_name):
    """Set a preset override that persists across all interactions"""
    global preset_override_active, preset_override_name
    preset_override_active = True
    preset_override_name = preset_name
    print(color_text(
        f"🔒 Preset override set: '{preset_name}' (will override auto-detection)", 'yellow'))


def clear_preset_override():
    """Clear the preset override to return to automatic detection"""
    global preset_override_active, preset_override_name
    preset_override_active = False
    preset_override_name = None
    print(color_text("🔓 Preset override cleared (automatic detection restored)", 'green'))


def get_active_preset(content_type=None, model_name=None, prompt_text=None):
    """Get the active preset, considering override first, then auto-detection"""
    if preset_override_active and preset_override_name:
        return preset_override_name
    else:
        return get_best_preset_for_task(content_type, model_name, prompt_text)


def show_preset_status():
    """Show current preset status to user"""
    if preset_override_active and preset_override_name:
        print(color_text(
            f"🔒 Current preset: '{preset_override_name}' (OVERRIDDEN)", 'yellow'))
        print(color_text("   Use 'preset' command to change or clear override", 'gray'))
    else:
        print(color_text("🎯 Current preset: Auto-detection active", 'cyan'))
        print(color_text("   Use 'preset' command to set manual override", 'gray'))


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

    selected_model = select_model(model_manager=model_manager)
    print(f"Using model: {selected_model}")

    # Ask if user wants to override the default preset for this model
    default_preset = get_best_preset_for_task(model_name=selected_model)
    available_presets = list_available_presets()

    if available_presets:
        print(color_text(
            f"🎯 Default preset for this model: {default_preset}", 'yellow'))
        override_choice = input(color_text(
            "Would you like to override the preset? (y/N): ", 'green')).strip().lower()

        if override_choice in ['y', 'yes']:
            preset_result, is_override, clear_override = ask_preset_override_enhanced(
                default_preset, available_presets)

            if clear_override:
                clear_preset_override()
            elif is_override:
                set_preset_override(preset_result)
            else:
                # Apply the default preset without override
                auto_apply_best_preset(model_name=selected_model, silent=True)
        else:
            # Apply the default preset without override
            auto_apply_best_preset(model_name=selected_model, silent=True)

    # Show current preset status
    show_preset_status()

    # Show model capabilities
    if is_vision_model(selected_model):
        print(color_text(
            "📷 This model supports image input! Use 'img:' to choose from images folder or 'help-img' for more options.", 'cyan'))
    if is_thinking_model(selected_model):
        print(color_text(
            "🧠 This model supports thinking mode! It may show reasoning in <think> tags.", 'cyan'))

    while True:
        print(color_text(
            "Enter your prompt (or 'exit' to quit, 's' to select new model, 'preset' to change preset):", 'green'))
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
            selected_model = select_model(
                previous_model=previous_model, model_manager=model_manager)
            print(f"Using model: {selected_model}")

            # Ask if user wants to override the default preset for the new model
            default_preset = get_best_preset_for_task(
                model_name=selected_model)
            available_presets = list_available_presets()

            if available_presets:
                print(color_text(
                    f"🎯 Default preset for this model: {default_preset}", 'yellow'))
                override_choice = input(color_text(
                    "Would you like to override the preset? (y/N): ", 'green')).strip().lower()

                if override_choice in ['y', 'yes']:
                    preset_result, is_override, clear_override = ask_preset_override_enhanced(
                        default_preset, available_presets)

                    if clear_override:
                        clear_preset_override()
                    elif is_override:
                        set_preset_override(preset_result)
                    else:
                        # Apply the default preset
                        auto_apply_best_preset(
                            model_name=selected_model, silent=True)
                else:
                    # Apply the default preset
                    auto_apply_best_preset(
                        model_name=selected_model, silent=True)

            # Show current preset status
            show_preset_status()

            # Show capabilities for new model
            if is_vision_model(selected_model):
                print(color_text(
                    "📷 This model supports image input! Use 'img:' to choose from images folder or 'help-img' for more options.", 'cyan'))
            if is_thinking_model(selected_model):
                print(color_text(
                    "🧠 This model supports thinking mode! It may show reasoning in <think> tags.", 'cyan'))
            continue
        elif prompt.lower() in ['help', 'h', '?']:
            print(color_text("\n📋 Available Commands:", 'cyan'))
            print("  • exit/quit/q - Exit the program")
            print("  • s - Select a new model")
            print("  • preset/presets/p - Change LLM preset settings or clear override")
            print("  • images/list-images - Show available images in folder")
            print("  • texts/list-texts - Show available text files in folder")
            print("  • help-img/img-help - Show image input help")
            print("  • help-text/text-help - Show text input help")
            print("  • help/h/? - Show this help message")
            print("  • status - Show current preset and model status")
            print(color_text("\n🎯 Automatic Features:", 'yellow'))
            print("  • Auto-detects content type (code, images, subtitles)")
            print("  • Auto-applies optimal LLM presets based on task")
            print("  • Auto-selects specialized system prompts")
            print(color_text("\n🔒 Preset Override System:", 'yellow'))
            print("  • Set manual preset override to persist across all interactions")
            print("  • Override takes precedence over auto-detection")
            print("  • Clear override anytime to return to automatic detection")
            print()
            continue
        elif prompt.lower() in ['status', 'st']:
            # Show current status
            print(color_text(f"\n📊 Current Status:", 'cyan'))
            print(f"  Model: {selected_model}")
            show_preset_status()
            print()
            continue
        elif prompt.lower() in ['preset', 'presets', 'p']:
            # Show current preset and allow changing it
            available_presets = list_available_presets()
            if available_presets:
                current_preset = get_active_preset(model_name=selected_model)
                preset_result, is_override, clear_override = ask_preset_override_enhanced(
                    current_preset, available_presets)

                if clear_override:
                    clear_preset_override()
                elif is_override:
                    set_preset_override(preset_result)

                # Show updated status
                show_preset_status()
            else:
                print(color_text("❌ No presets available in config", 'red'))
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
        # Parse image input if present
        image_data = None
        text_data = None
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

        # Automatically apply the best preset for the detected task (or use override)
        active_preset = get_active_preset(
            content_type, selected_model, actual_prompt)

        if preset_override_active:
            # Use override preset
            applied_preset = active_preset
            print(color_text(
                f"🔒 Using overridden preset: '{applied_preset}'", 'yellow'))
        else:
            # Use automatic detection
            applied_preset = auto_apply_best_preset(
                content_type, selected_model, actual_prompt)
            if applied_preset != 'default':
                print(color_text(
                    f"🎯 Auto-applied preset: '{applied_preset}'", 'cyan'))

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

        # Save the response to markdown file
        try:
            save_response_to_markdown(
                user_prompt=actual_prompt,
                model_response=response,
                model_name=selected_model,
                image_data=image_data,
                content_type=content_type,
                system_prompt=system_prompt
            )
        except Exception as e:
            print(f"Warning: Could not save response to file: {e}")
