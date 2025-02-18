from .get_images_from_folder import get_images_from_folder
from .color_text import color_text


import os


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
                base_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..'))
                images_folder = os.path.join(base_dir, 'content', 'images')
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
