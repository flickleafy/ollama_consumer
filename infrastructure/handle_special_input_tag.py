import os
from .color_text import color_text
from .get_images_from_folder import get_images_from_folder
from .detect_content_type import detect_content_type
from .prepare_image_input import prepare_image_input
from .select_image_from_folder import select_image_from_folder
from .select_text_from_folder import select_text_from_folder

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


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
                    base_dir, 'content', 'images')
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
                    base_dir, 'content', 'texts')
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
