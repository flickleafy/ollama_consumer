from .apply_llm_preset import apply_llm_preset
from .color_text import color_text


def ask_preset_override(current_preset, available_presets):
    """
    Ask user if they want to override the automatically selected preset

    Args:
        current_preset (str): Currently selected/applied preset
        available_presets (dict): Dictionary of available presets

    Returns:
        str: Chosen preset name, or current_preset if no override
    """
    print(color_text(f"\n🎛️ Current preset: {current_preset}", 'yellow'))
    print("Available presets:")
    preset_list = list(available_presets.keys())

    for i, (preset_name, description) in enumerate(available_presets.items(), 1):
        indicator = "✓" if preset_name == current_preset else " "
        print(f"  {indicator} {i}. {preset_name} - {description}")

    print("  0. Keep current preset")

    while True:
        try:
            choice = input(color_text(
                "\nOverride preset? (0 to keep current, number to change): ", 'green')).strip()

            if choice == '0' or choice.lower() in ['n', 'no', '']:
                return current_preset

            choice_num = int(choice)
            if 1 <= choice_num <= len(preset_list):
                selected_preset = preset_list[choice_num - 1]
                if apply_llm_preset(selected_preset):
                    print(color_text(
                        f"✅ Applied '{selected_preset}' preset", 'green'))
                    return selected_preset
                else:
                    print(color_text("❌ Failed to apply preset", 'red'))
                    return current_preset
            else:
                print(
                    f"Please enter a number between 0 and {len(preset_list)}")
        except ValueError:
            print("Please enter a valid number or press Enter to keep current")
        except KeyboardInterrupt:
            print("\nKeeping current preset")
            return current_preset
