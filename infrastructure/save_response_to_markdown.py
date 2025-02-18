"""
Save model responses to markdown files in content/answers directory

This module provides functionality to save chat interactions to markdown files
with proper formatting, including automatic title and tag generation.
"""

import os
import re
import json
import configparser
from datetime import datetime
from .get_model_info import get_model_info
from .ask_ollama import ask_ollama
from .get_advanced_params_from_config import get_advanced_params_from_config


def save_response_to_markdown(user_prompt, model_response, model_name, image_data=None, content_type=None, system_prompt=None):
    """
    Save a model response to a markdown file with proper formatting

    Args:
        user_prompt (str): The original user prompt/question
        model_response (str): The model's response
        model_name (str): Name of the model used
        image_data (str, optional): Base64 image data if image was included
        content_type (str, optional): Type of content analyzed
        system_prompt (str, optional): System prompt used

    Returns:
        str: Path to the saved markdown file, or None if failed
    """
    try:
        # Create content/answers directory if it doesn't exist
        answers_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'content', 'answers')
        os.makedirs(answers_dir, exist_ok=True)

        # Generate title using the model
        if ask_ollama:
            title = generate_title_for_query(
                user_prompt=user_prompt, model_response=model_response, model_name=model_name)
            tags = generate_tags_for_query(
                user_prompt=user_prompt, model_response=model_response, model_name=model_name)
        else:
            title = create_fallback_title(user_prompt)
            tags = create_fallback_tags(user_prompt)

        # Extract thinking process from model response
        thinking_content = extract_thinking_process(model_response)
        clean_response = remove_thinking_tags(model_response)

        # Get current timestamp
        timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")

        # Get model metadata
        model_metadata = get_model_metadata(model_name)

        # Get current parameters used
        current_params = get_advanced_params_from_config()

        # Create markdown content
        markdown_content = create_markdown_content(
            title=title,
            timestamp=timestamp,
            tags=tags,
            user_prompt=user_prompt,
            model_response=clean_response,
            thinking_content=thinking_content,
            model_name=model_name,
            model_metadata=model_metadata,
            current_params=current_params,
            image_data=image_data,
            content_type=content_type,
            system_prompt=system_prompt
        )

        # Generate safe filename from title
        safe_filename = create_safe_filename(title, timestamp)
        filename = f"{safe_filename}.md"
        filepath = os.path.join(answers_dir, filename)

        # Handle duplicate filenames
        counter = 1
        original_filepath = filepath
        while os.path.exists(filepath):
            name_without_ext = os.path.splitext(original_filepath)[0]
            filepath = f"{name_without_ext}_{counter}.md"
            counter += 1

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✅ Response saved to: {os.path.relpath(filepath)}")
        return filepath

    except Exception as e:
        print(f"❌ Failed to save response to markdown: {e}")
        return None


def generate_title_for_query(user_prompt, model_name, model_response):
    """
    Generate a concise title for the query using the model

    Args:
        user_prompt (str): The user's question/prompt
        model_name (str): Name of the model to use for title generation

    Returns:
        str: Generated title (max 10 words)
    """
    title_system_prompt = """You are a title generator. Create concise, precise titles for user queries. 
Rules:
- Maximum 10 words
- Be specific and descriptive
- Focus on the main action and main topic of the content, not the query itself
- Go through the entire content to understand the main topic
- If the action was to create a summary, the title can start as "Summary of..."
- Use clear, simple language
- Focus on: topic, domain, technology, concepts, methods
- Use precise, specific terms
- Avoid generic words like "question", "answer", "content"
- No special characters except hyphens
- Respond with ONLY the title, nothing else"""

    content_sample = f"Query: {user_prompt[:800]}... Response: {model_response[:800]}..."
    title_user_prompt = f"Create a title for this query and content: {content_sample}"

    try:
        title_response = ask_ollama(
            title_user_prompt,
            model_name,
            title_system_prompt,
            use_config_params=False
        )

        # Clean up the title
        title = remove_thinking_tags(
            title_response).strip().strip('"').strip("'")
        # Remove special chars except hyphens
        title = re.sub(r'[^\w\s-]', '', title)

        # Ensure max 10 words
        words = title.split()
        if len(words) > 10:
            title = ' '.join(words[:10])

        return title if title else create_fallback_title(user_prompt)

    except Exception as e:
        print(f"Warning: Failed to generate title: {e}")
        return create_fallback_title(user_prompt)


def generate_tags_for_query(user_prompt, model_response, model_name, ):
    """
    Generate relevant tags for the query and response using the model

    Args:
        user_prompt (str): The user's question/prompt
        model_response (str): The model's response
        model_name (str): Name of the model to use for tag generation

    Returns:
        str: Generated tags (semicolon separated, max 15 words total)
    """
    tags_system_prompt = """You are a content tagger. Generate relevant tags/keywords for content categorization.
Rules:
- Maximum 15 words total across all tags
- Use semicolon (;) to separate tags
- Focus on: topic, domain, technology, concepts, methods
- Use precise, specific terms
- Avoid generic words like "question", "answer", "content"
- Respond with ONLY the tags, nothing else"""

    # Truncate content for tag generation to avoid token limits
    content_sample = f"Query: {user_prompt[:800]}... Response: {model_response[:800]}..."
    tags_user_prompt = f"Generate tags for this content: {content_sample}"

    try:
        tags_response = ask_ollama(
            tags_user_prompt,
            model_name,
            tags_system_prompt,
            use_config_params=False
        )

        # Clean up tags
        tags = remove_thinking_tags(
            tags_response).strip().strip('"').strip("'")
        # Keep only words, spaces, semicolons, hyphens
        tags = re.sub(r'[^\w\s;-]', '', tags)

        # Ensure word limit
        all_words = re.findall(r'\w+', tags)
        if len(all_words) > 15:
            # Truncate tags to stay within word limit
            word_count = 0
            truncated_tags = []
            for tag in tags.split(';'):
                tag_words = re.findall(r'\w+', tag.strip())
                if word_count + len(tag_words) <= 15:
                    truncated_tags.append(tag.strip())
                    word_count += len(tag_words)
                else:
                    break
            tags = '; '.join(truncated_tags)

        return tags if tags else create_fallback_tags(user_prompt)

    except Exception as e:
        print(f"Warning: Failed to generate tags: {e}")
        return create_fallback_tags(user_prompt)


def create_fallback_title(user_prompt):
    """Create a fallback title from the user prompt"""
    words = user_prompt.split()[:4]
    return ' '.join(words) if words else "Untitled Query"


def create_fallback_tags(user_prompt):
    """Create fallback tags from the user prompt"""
    # Simple keyword extraction
    common_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an',
                    'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'}
    words = re.findall(r'\w+', user_prompt.lower())
    keywords = [word for word in words if len(
        word) > 3 and word not in common_words][:5]
    return '; '.join(keywords) if keywords else "general; query"


def extract_thinking_process(model_response):
    """
    Extract thinking/reasoning content from model response

    Args:
        model_response (str): The full model response

    Returns:
        str: Extracted thinking content, or None if no thinking tags found
    """
    # Pattern to match <think>...</think> or <thinking>...</thinking> tags
    thinking_pattern = r'<think[^>]*>(.*?)</think[^>]*>|<thinking[^>]*>(.*?)</thinking[^>]*>'

    matches = re.findall(thinking_pattern, model_response,
                         re.DOTALL | re.IGNORECASE)

    if matches:
        # Extract non-empty groups from matches
        thinking_parts = []
        for match in matches:
            content = match[0] or match[1]  # Get the non-empty group
            if content.strip():
                thinking_parts.append(content.strip())

        return '\n\n'.join(thinking_parts) if thinking_parts else None

    return None


def remove_thinking_tags(model_response):
    """
    Remove thinking tags from model response to get clean answer

    Args:
        model_response (str): The full model response

    Returns:
        str: Response with thinking tags removed
    """
    # Pattern to match <think>...</think> or <thinking>...</thinking> tags
    thinking_pattern = r'<think[^>]*>.*?</think[^>]*>|<thinking[^>]*>.*?</thinking[^>]*>'

    clean_response = re.sub(thinking_pattern, '',
                            model_response, flags=re.DOTALL | re.IGNORECASE)

    # Clean up extra whitespace
    # Multiple newlines to double
    clean_response = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_response)
    clean_response = clean_response.strip()

    return clean_response


def get_model_metadata(model_name):
    """
    Get model metadata including size, family, etc.

    Args:
        model_name (str): Name of the model

    Returns:
        dict: Model metadata
    """
    try:
        model_info = get_model_info(model_name)
        if isinstance(model_info, dict):
            return model_info
        else:
            return {"name": model_name, "info": "Metadata unavailable"}
    except Exception:
        return {"name": model_name, "info": "Metadata unavailable"}


def create_markdown_content(title, timestamp, tags, user_prompt, model_response, thinking_content,
                            model_name, model_metadata, current_params, image_data=None,
                            content_type=None, system_prompt=None):
    """
    Create the complete markdown content

    Returns:
        str: Formatted markdown content
    """
    markdown = f"""# {title}

**Timestamp: {timestamp}**

**Tags: {tags}**

## User question:

{user_prompt}

* * *

## Model response:

{model_response}

* * *
"""

    # Add thinking process if available
    if thinking_content:
        markdown += f"""
## Reasoning Process:

{thinking_content}

* * *
"""

    # Add session metadata
    markdown += f"""
## Session Metadata:

**Model:** {model_name}

"""

    # Add model info
    if isinstance(model_metadata, dict):
        markdown += f"**Model Info:**\n"
        for key, value in model_metadata.items():
            if key != "name":  # Skip name since it's already shown
                markdown += f"- {key.replace('_', ' ').title()}: {value}\n"
        markdown += "\n"

    # Add parameters used
    if current_params:
        markdown += f"**Parameters Used:**\n"
        for param, value in current_params.items():
            markdown += f"- {param}: {value}\n"
        markdown += "\n"

    # Add additional context
    if content_type:
        markdown += f"**Content Type:** {content_type}\n\n"

    if image_data:
        markdown += f"**Image Input:** Yes (Base64 encoded)\n\n"

    if system_prompt:
        markdown += f"**System Prompt Used:**\n```\n{system_prompt}\n```\n\n"

    return markdown


def create_safe_filename(title, timestamp):
    """
    Create a safe filename from title

    Args:
        title (str): The title to convert

    Returns:
        str: Safe filename
    """
    # Convert timestamp to short format: YYYYMMDD_HHMM
    try:
        dt = datetime.strptime(timestamp, "%d %B %Y, %I:%M %p")
        short_timestamp = dt.strftime("%Y%m%d_%H%M")
    except Exception:
        # Fallback: use only digits from timestamp
        short_timestamp = re.sub(r'\D', '', timestamp)[:12]

    # Remove/replace unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '-', title)
    # Replace spaces with underscores
    safe_name = re.sub(r'\s+', '_', safe_name)
    # Replace multiple underscores with single
    safe_name = re.sub(r'_{2,}', '_', safe_name)
    # Remove leading/trailing underscores and hyphens
    safe_name = safe_name.strip('_-')

    # Ensure reasonable length
    if len(safe_name) > 100:
        safe_name = f"{safe_name[:100]}_{short_timestamp}"

    # Add timestamp if filename is too short or empty
    if len(safe_name) < 3:
        safe_name = f"query_{short_timestamp}"

    return safe_name
