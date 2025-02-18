from .color_text import color_text


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
