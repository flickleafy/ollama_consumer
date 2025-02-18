def color_text(text, color):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'gray': '\033[90m',
        'cyan': '\033[96m',
        'red': '\033[91m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"
