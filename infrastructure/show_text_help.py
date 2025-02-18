from .color_text import color_text


def show_text_help():
    """Show help information about text input options and automatic system prompt selection"""
    print(color_text("\n📄 Text Input Options:", 'cyan'))
    print("  1. 'text:' - Choose from texts folder")
    print("  2. 'text:filename.txt your prompt' - Use specific file from texts folder")
    print("  3. 'text:/full/path/to/file.txt your prompt' - Use full file path")
    print("  4. Type 'texts' to see available text files in folder")
    print(color_text("  Automatic System Prompt Selection:", 'yellow'))
    print("    🎯 Code files (.py, .js, .java, etc.) → Code Analysis prompt")
    print("    🎯 Subtitle files (.srt, .vtt, etc.) → Video Transcript Analysis prompt")
    print("    🎯 Other text files → Default prompt")
    print(color_text("  Examples:", 'yellow'))
    print("    text: Analyze this file")
    print("    text:script.py Explain what this code does")
    print("    text:video_transcript.srt Summarize this video")
    print()
