"""
Enhanced preset override management

Provides UI for managing preset overrides with clear/unset options
"""

from .color_text import color_text
from .apply_llm_preset import apply_llm_preset


def ask_preset_override_enhanced(current_preset, available_presets):
    """
    Enhanced preset override dialog with clear option

    Args:
        current_preset (str): Currently selected/applied preset
        available_presets (dict): Dictionary of available presets

    Returns:
        tuple: (preset_name, is_override_set, clear_override)
            - preset_name: str, chosen preset name
            - is_override_set: bool, whether an override was set
            - clear_override: bool, whether to clear existing override
    """
    print(color_text(f"\n🎛️ Current preset: {current_preset}", 'yellow'))
    print("Available presets:")
    preset_list = list(available_presets.keys())

    for i, (preset_name, description) in enumerate(available_presets.items(), 1):
        indicator = "✓" if preset_name == current_preset else " "
        print(f"  {indicator} {i}. {preset_name} - {description}")

    print("  0. Keep current preset (no override)")
    print(color_text("  c. Clear override (return to auto-detection)", 'cyan'))

    while True:
        try:
            choice = input(color_text(
                "\nSelect preset (0=keep, c=clear, number=override): ", 'green')).strip().lower()

            if choice == '0' or choice in ['n', 'no', '']:
                return current_preset, False, False

            if choice in ['c', 'clear']:
                return None, False, True

            choice_num = int(choice)
            if 1 <= choice_num <= len(preset_list):
                selected_preset = preset_list[choice_num - 1]
                if apply_llm_preset(selected_preset):
                    print(color_text(
                        f"✅ Applied '{selected_preset}' preset with override", 'green'))
                    return selected_preset, True, False
                else:
                    print(color_text("❌ Failed to apply preset", 'red'))
                    return current_preset, False, False
            else:
                print(
                    f"Please enter a number between 0 and {len(preset_list)}, or 'c' to clear")
        except ValueError:
            print(
                "Please enter a valid number, 'c' to clear, or press Enter to keep current")
        except KeyboardInterrupt:
            print("\nKeeping current preset")
            return current_preset, False, False
