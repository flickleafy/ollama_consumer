import re


def detect_content_type(file_path=None, text_data=None):
    """
    Detect content type based on file extension and content

    Args:
        file_path (str): Path to the file
        text_data (str): Text content of the file

    Returns:
        str: Content type - 'code', 'srt', or None for generic text
    """
    if file_path:
        file_lower = file_path.lower()

        # Check for SRT/subtitle files
        if file_lower.endswith(('.srt', '.vtt', '.ass', '.ssa', '.sub')):
            return 'srt'

        # Check for source code file extensions
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp', '.cs',
            '.go', '.rb', '.php', '.html', '.htm', '.css', '.scss', '.less',
            '.sh', '.bat', '.ps1', '.pl', '.lua', '.swift', '.kt', '.dart',
            '.scala', '.sql', '.r', '.jl', '.m', '.vb', '.asm', '.s',
            '.vue', '.jsx', '.tsx', '.json', '.xml', '.yaml', '.yml'
        }

        if any(file_lower.endswith(ext) for ext in code_extensions):
            return 'code'

    # If we have text data, try to detect SRT format by content
    if text_data:
        # SRT files typically have timestamp patterns like "00:01:23,456 --> 00:01:26,789"
        srt_pattern = r'\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}'
        if re.search(srt_pattern, text_data):
            return 'srt'

        # Check for common code patterns (basic heuristics)
        code_patterns = [
            r'def\s+\w+\s*\(',  # Python functions
            r'function\s+\w+\s*\(',  # JavaScript functions
            r'class\s+\w+',  # Class definitions
            r'import\s+\w+',  # Import statements
            r'#include\s*<',  # C/C++ includes
            r'<?xml\s+version',  # XML declarations
            r'<!DOCTYPE\s+html',  # HTML doctypes
        ]

        if any(re.search(pattern, text_data, re.IGNORECASE) for pattern in code_patterns):
            return 'code'

    return None  # Generic text, use default prompt
