import os


def get_images_from_folder():
    """
    Get list of image files from the images folder

    Returns:
        list: List of image filenames, or empty list if folder doesn't exist
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    images_folder = os.path.join(base_dir, 'content', 'images')

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
