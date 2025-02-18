import base64
import os


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
