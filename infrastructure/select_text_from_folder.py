from .get_texts_from_folder import get_texts_from_folder
from .color_text import color_text


import os


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
                base_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..'))
                texts_folder = os.path.join(base_dir, 'content', 'texts')
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
